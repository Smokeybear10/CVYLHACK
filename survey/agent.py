"""The per-site agent: call the client, force identity, validate, retry, fall back.

This is where the reliability stack is enforced. An agent's raw output is never
trusted directly: it is revalidated, and if it cannot pass (schema, grounding, or
consistency) after a retry, we fall back to the deterministic grounded report so a
single bad agent never produces a bad or hallucinated site.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import deterministic
from .schema import SiteBundle, SiteReport
from .validators import ValidationResult, validate

_SKILLS_PATH = Path(__file__).resolve().parent / "skills.md"


@lru_cache(maxsize=1)
def load_skills() -> str:
    return _SKILLS_PATH.read_text()


@dataclass
class SurveyOutcome:
    report: SiteReport
    validation: ValidationResult
    used_fallback: bool
    attempts: int
    error: str | None = None


def _graft(bundle: SiteBundle, data: dict, generated_by: str) -> SiteReport:
    """Build a fully grounded report from the bundle, then graft only the model's
    prose/judgment onto it. Every number in the report therefore comes from the
    bundle (deterministic sections); the model contributes narrative, never figures.
    Identity is always the bundle's. May raise if the model output is not schema-valid."""
    base = deterministic.build_report(bundle, generated_by=generated_by)
    model = SiteReport.model_validate({**data, "site": bundle.site.model_dump()})
    if model.verdict.one_line_reason:
        base.verdict.one_line_reason = model.verdict.one_line_reason
    if model.executive_summary:
        base.executive_summary = model.executive_summary
    if model.risks_and_constraints:
        base.risks_and_constraints = model.risks_and_constraints
    if model.next_steps:
        base.next_steps = model.next_steps
    if model.evidence and model.evidence.cv_findings:
        base.evidence.cv_findings = model.evidence.cv_findings
    return base


def survey_site(bundle: SiteBundle, client, skills: str | None = None,
                max_retries: int = 1) -> SurveyOutcome:
    """Produce a validated report for one site. Grafts the model's prose onto a
    grounded base, then validates. Falls back to the deterministic grounded report
    on any error or persistent validation failure (e.g. an invented number in prose)."""
    skills = skills if skills is not None else load_skills()
    last_issues: list[str] = []
    last_error: str | None = None

    for attempt in range(1, max_retries + 2):  # initial try + retries
        try:
            data = client.generate(bundle, skills)
            report = _graft(bundle, data, client.name)
            result = validate(report, bundle)
            if result.ok:
                return SurveyOutcome(report=result.report, validation=result,
                                     used_fallback=False, attempts=attempt)
            last_issues = result.all_issues
        except Exception as exc:  # network, parse, schema, anything
            last_error = f"{type(exc).__name__}: {exc}"

    # Fallback: deterministic, grounded by construction.
    fb = deterministic.build_report(bundle, generated_by="fallback")
    fb_result = validate(fb, bundle)
    err = last_error or ("validation failed: " + "; ".join(last_issues) if last_issues else None)
    return SurveyOutcome(report=fb, validation=fb_result, used_fallback=True,
                         attempts=max_retries + 1, error=err)
