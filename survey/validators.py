"""Validation stack: schema, grounding guard, consistency.

An agent output is trusted only after it passes all three. The grounding guard is
the anti-hallucination core: every number in the report must trace to a value in
the bundle's allow-list, so an invented figure cannot ship.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from . import criteria
from .schema import SiteBundle, SiteReport

# numbers like 12, 12.5, 1,200, $11,500, 42 (commas/$/spaces handled by cleaning)
_NUM = re.compile(r"-?\$?\d[\d,]*\.?\d*")
# fields whose numbers are identity / references, not factual claims, so they are
# not grounding-checked: the whole site block (id, coords, region) and the photo ref.
_IDENTITY_EXACT = {"evidence.photo_ref", "generated_by"}


def _is_identity(path: str) -> bool:
    return path == "site" or path.startswith("site.") or path in _IDENTITY_EXACT


def _to_float(tok: str):
    t = tok.replace("$", "").replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def _numbers_in_text(text: str) -> list[float]:
    out = []
    for tok in _NUM.findall(text or ""):
        v = _to_float(tok)
        if v is not None:
            out.append(v)
    return out


def _walk_numbers(obj, path=""):
    """Yield (path, number) for every numeric value and number-in-string, skipping
    identity fields (the site block, photo ref)."""
    if _is_identity(path):
        return
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield path, float(obj)
    elif isinstance(obj, str):
        for v in _numbers_in_text(obj):
            yield path, v
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_numbers(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _walk_numbers(v, f"{path}[{i}]")


def _is_grounded(value: float, allowed: list[float]) -> bool:
    for a in allowed:
        if abs(value - a) <= max(0.5, 0.02 * abs(a)):
            return True
    return False


def grounding_guard(report: SiteReport, bundle: SiteBundle) -> list[str]:
    """Return a list of ungrounded-number violations (empty = fully grounded)."""
    allowed = list(bundle.allowed_numbers)
    violations = []
    for path, num in _walk_numbers(report.model_dump()):
        if not _is_grounded(num, allowed):
            violations.append(f"ungrounded number {num} at {path} (not in bundle allow-list)")
    return violations


def consistency_checks(report: SiteReport, bundle: SiteBundle) -> list[str]:
    issues = []
    d = bundle.derived
    if report.site.id != bundle.site.id:
        issues.append(f"site id mismatch: report {report.site.id} vs bundle {bundle.site.id}")
    canonical_tier = criteria.tier_from(d.composite_score, d.gated)
    if report.verdict.tier != canonical_tier:
        issues.append(f"tier {report.verdict.tier!r} != canonical {canonical_tier!r}")
    if d.gated and report.verdict.tier != "No-go":
        issues.append("gated site must be tier No-go")
    if abs(report.verdict.composite_score - d.composite_score) > 0.2:
        issues.append(f"composite_score {report.verdict.composite_score} != bundle "
                      f"{d.composite_score}")
    if not report.scorecard:
        issues.append("scorecard is empty")
    if not report.to_be_verified:
        issues.append("to_be_verified is empty (unknowns must be deferred, not omitted)")
    return issues


@dataclass
class ValidationResult:
    ok: bool
    schema_ok: bool
    report: SiteReport | None
    schema_error: str | None = None
    grounding_violations: list[str] = field(default_factory=list)
    consistency_violations: list[str] = field(default_factory=list)

    @property
    def all_issues(self) -> list[str]:
        out = []
        if self.schema_error:
            out.append(f"schema: {self.schema_error}")
        out += [f"grounding: {v}" for v in self.grounding_violations]
        out += [f"consistency: {v}" for v in self.consistency_violations]
        return out


def validate(report_data, bundle: SiteBundle) -> ValidationResult:
    """Validate a report (dict or SiteReport) against the bundle. ok is True only
    when schema, grounding, and consistency all pass."""
    try:
        report = report_data if isinstance(report_data, SiteReport) else SiteReport.model_validate(report_data)
    except ValidationError as e:
        return ValidationResult(ok=False, schema_ok=False, report=None, schema_error=str(e))

    grounding = grounding_guard(report, bundle)
    consistency = consistency_checks(report, bundle)
    ok = not grounding and not consistency
    return ValidationResult(ok=ok, schema_ok=True, report=report,
                            grounding_violations=grounding, consistency_violations=consistency)
