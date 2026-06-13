"""Swarm orchestration.

run_breadth: one surveyor agent per finalist, in waves, streamed as they finish.
run_crew:    the winner deep-dive (fit / connection / context specialists -> judge).

Verdicts are yielded as they complete so the frontend can fill the map live. A disk cache keyed
by (site_id, station_size, weights) makes rehearsals reproducible and free.
"""
from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator

from .schema import SiteInput, Measurements, UserPriorities, Verdict
from . import providers, prompts

CACHE_DIR = Path(os.environ.get("SWARM_CACHE", ".swarm_cache"))


def _cache_key(site: SiteInput, prefs: UserPriorities) -> str:
    blob = json.dumps([site.site_id, prefs.station_size, prefs.weights], sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def _cache_get(key: str) -> Verdict | None:
    p = CACHE_DIR / f"{key}.json"
    if p.exists():
        d = json.loads(p.read_text())
        return Verdict(**d)
    return None


def _cache_put(key: str, v: Verdict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / f"{key}.json").write_text(json.dumps(v.to_dict(), indent=2))


def run_breadth(
    sites: list[SiteInput],
    measurements: dict[str, Measurements],
    prefs: UserPriorities,
    wave_size: int = 6,
    use_cache: bool = True,
) -> Iterator[Verdict]:
    """Survey every finalist, ~wave_size agents at a time, yielding verdicts as they land."""
    pending = list(sites)
    while pending:
        wave, pending = pending[:wave_size], pending[wave_size:]
        with ThreadPoolExecutor(max_workers=wave_size) as ex:
            futs = {}
            for site in wave:
                key = _cache_key(site, prefs)
                if use_cache and (cached := _cache_get(key)):
                    yield cached
                    continue
                futs[ex.submit(providers.surveyor_verdict, site, measurements[site.site_id], prefs)] = (site, key)
            for fut in as_completed(futs):
                site, key = futs[fut]
                v = fut.result()
                if use_cache:
                    _cache_put(key, v)
                yield v


def pick_winners(verdicts: list[Verdict], sites: list[SiteInput], n: int = 3) -> list[str]:
    """Top n site_ids for the deep-dive: prefer 'go', then Stage 1 score, then confidence."""
    score = {s.site_id: s.score for s in sites}
    rank = {"go": 0, "conditional": 1, "no_go": 2}
    ordered = sorted(verdicts, key=lambda v: (rank[v.verdict], -score.get(v.site_id, 0), -v.confidence))
    return [v.site_id for v in ordered[:n]]


def run_crew(site: SiteInput, meas: Measurements, prefs: UserPriorities) -> Verdict:
    """Deep-dive one winner with specialist agents, then a judge fuses them."""
    if providers.have_key():
        findings = {}
        for role, sys in prompts.CREW_SPECIALISTS.items():
            msgs = prompts.build_surveyor_messages(site, meas, prefs)
            findings[role] = providers._parse_json(providers._call_model(sys, msgs, max_tokens=512))
        judge_user = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompts._facts_block(site, meas, prefs)},
                {"type": "text", "text": "Specialist findings:\n" + json.dumps(findings, indent=2)},
                {"type": "image_ref", "url": meas.street_photo_url},
                {"type": "text", "text": "Return the final verdict JSON with a crew object."},
            ],
        }]
        data = providers._parse_json(providers._call_model(prompts.JUDGE_SYSTEM, judge_user, max_tokens=1200))
        crew = data.get("crew", findings)
        base = {k: data[k] for k in (
            "verdict", "confidence", "one_line_reason", "rationale",
            "positives", "concerns", "verify_on_site", "sub_scores")}
    else:
        # mock crew: derive from the breadth mock and synthesize specialist findings
        bv = providers.surveyor_verdict(site, meas, prefs)
        crew = {
            "fit": {"finding": f"{meas.usable_frontage_ft:.1f} ft usable; "
                    f"{'fits' if meas.usable_frontage_ft >= prefs.required_frontage_ft else 'too tight for'} "
                    f"{prefs.station_size}", "values": {"frontage_ft": meas.usable_frontage_ft}},
            "connection": {"finding": f"power {meas.distance_to_power_m:.0f} m; "
                           f"{site.pavement_label} surface to cut", "values": {"power_m": meas.distance_to_power_m}},
            "context": {"finding": "photo scan", "saw": [o.get("type") for o in meas.obstruction_positions]
                        + [k for k in ("bus_stop", "loading_zone") if site.marking_flags.get(k)]},
        }
        base = {k: getattr(bv, k) for k in (
            "verdict", "confidence", "one_line_reason", "rationale",
            "positives", "concerns", "verify_on_site", "sub_scores")}
    return Verdict(site_id=site.site_id, evidence_image_url=meas.evidence_image_url,
                   source="swarm.crew.judge" + ("" if providers.have_key() else ".mock"),
                   crew=crew, **base)
