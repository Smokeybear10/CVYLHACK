"""Run the swarm: one agent per site, in bounded concurrent waves, with caching.

The orchestrator never trusts raw output; each site goes through survey_site (which
validates and falls back). Results come back in input order. Caching keys on the
bundle + client + prompt version so reruns are identical and free.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from .agent import SurveyOutcome, load_skills, survey_site
from .cache import CacheStore, cache_key
from .schema import SiteBundle, SiteReport
from .validators import validate


def _from_cache(bundle: SiteBundle, cached: dict) -> SurveyOutcome:
    result = validate(cached, bundle)  # re-validate cached payload for safety
    report = result.report if result.report is not None else SiteReport.model_validate(cached)
    return SurveyOutcome(report=report, validation=result,
                         used_fallback=(report.generated_by == "fallback"),
                         attempts=0, error=None)


def run_survey(bundles: list[SiteBundle], client, skills: str | None = None,
               wave_size: int = 6, use_cache: bool = True,
               cache_dir=None) -> list[SurveyOutcome]:
    skills = skills if skills is not None else load_skills()
    cache = CacheStore(cache_dir) if use_cache else None

    def work(bundle: SiteBundle) -> SurveyOutcome:
        if cache is not None:
            key = cache_key(bundle, client.name)
            hit = cache.get(key)
            if hit is not None:
                return _from_cache(bundle, hit)
        outcome = survey_site(bundle, client, skills)
        if cache is not None:
            cache.set(cache_key(bundle, client.name), outcome.report.model_dump())
        return outcome

    outcomes: list[SurveyOutcome | None] = [None] * len(bundles)
    for start in range(0, len(bundles), max(1, wave_size)):
        wave = list(range(start, min(start + wave_size, len(bundles))))
        with ThreadPoolExecutor(max_workers=max(1, wave_size)) as pool:
            for idx, outcome in zip(wave, pool.map(lambda i: work(bundles[i]), wave)):
                outcomes[idx] = outcome
    return [o for o in outcomes if o is not None]


def reports_only(outcomes: list[SurveyOutcome]) -> list[SiteReport]:
    return [o.report for o in outcomes]
