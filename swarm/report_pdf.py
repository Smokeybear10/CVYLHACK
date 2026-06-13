"""Bridge the live swarm verdict + the frontend's Cyvl measurements into a PDF.

The swarm emits a verdict (go/conditional/no_go + crew); the polished generator lives in the
other lane (survey/pdf.py, reportlab) and consumes survey.schema.SiteReport. This adapter maps
the real per-site measurements the frontend already holds (frontage, power, PCI, obstructions,
etc.) plus the live agent verdict into a faithful SiteReport, then renders it. No stub numbers:
every technical row comes from the site's actual scan measurements.
"""
from __future__ import annotations

import os
import tempfile
from typing import Any

from survey.pdf import build_pdf
from survey.schema import (
    SiteReport, SiteInfo, Verdict, ScoreRow, PhysicalFit, Connection,
    Demand, SiteConditions, Accessibility, Evidence,
)

_TIER = {"go": "Tier 1", "conditional": "Tier 2", "no_go": "No-go"}
_FT_PER_M = 3.281


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _rate_frontage(fr, req):
    if fr is None or req is None:
        return "CAUTION"
    return "GO" if fr >= req else "NO-GO"


def _rate_power(m):
    if m is None:
        return "CAUTION"
    return "GO" if m <= 30 else ("CAUTION" if m <= 60 else "NO-GO")


def _rate_pci(p):
    if p is None:
        return "CAUTION"
    return "GO" if p >= 56 else ("CAUTION" if p >= 25 else "NO-GO")


def _cost_band(usd):
    if usd is None:
        return None
    return "low" if usd < 8000 else ("moderate" if usd < 15000 else "high")


def _site_report(payload: dict[str, Any]) -> SiteReport:
    site = payload.get("site") or {}
    v = payload.get("verdict") or {}
    m = site.get("m") or {}
    req = _num(payload.get("required_frontage_ft"))

    frontage = _num(m.get("frontage_ft"))
    width = _num(m.get("width_ft"))
    power = _num(m.get("dist_power"))
    pci = _num(m.get("pci"))
    n_obst = int(_num(m.get("n_obst"), 0) or 0)
    stalls = int(_num(m.get("stalls"), 0) or 0)
    surface = m.get("surface")
    score = _num(site.get("score"), 0) or 0
    cost = _num(site.get("cost"))
    ada_mapped = bool(m.get("ada_mapped"))
    ada_pass = bool(m.get("ada_pass"))

    verdict_key = v.get("verdict")  # go / conditional / no_go, or None for screen-only
    live = bool(verdict_key)
    one_line = v.get("one_line_reason") or _screen_reason(score, frontage, power, pci)
    tier = _TIER.get(verdict_key, "Tier 1" if score >= 75 else "Tier 2" if score >= 60 else "No-go")

    positives = list(v.get("positives") or [])
    concerns = list(v.get("concerns") or [])
    verify = list(v.get("verify_on_site") or [])
    rationale = v.get("rationale") or ""
    crew = v.get("crew") or {}

    summary = []
    if rationale:
        summary.append(rationale)
    elif one_line:
        summary.append(one_line)
    if not live:
        summary.append("Deterministic screen only; the live agent survey has not been run for this segment.")
    summary += positives

    scorecard = [
        ScoreRow(criterion="Usable frontage",
                 value=f"{frontage:.0f} ft (needs {req:.0f} ft)" if frontage is not None and req else f"{frontage} ft",
                 rating=_rate_frontage(frontage, req), source="have"),
        ScoreRow(criterion="Distance to power",
                 value=f"{power:.0f} m" if power is not None else "n/a",
                 rating=_rate_power(power), source="have"),
        ScoreRow(criterion="Pavement",
                 value=f"{m.get('pci_label','')} (PCI {pci:.0f})" if pci is not None else "n/a",
                 rating=_rate_pci(pci), source="have"),
        ScoreRow(criterion="Obstructions in frontage",
                 value=str(n_obst), rating="GO" if n_obst <= 2 else "CAUTION", source="have"),
        ScoreRow(criterion="ADA ramp",
                 value=(f"ramp {m.get('dist_ada')} m" if ada_mapped else "not mapped"),
                 rating=("GO" if ada_mapped and ada_pass else "CAUTION"),
                 source=("have" if ada_mapped else "verify")),
        ScoreRow(criterion="Grid capacity / zoning / permit",
                 value="not in export", rating="CAUTION", source="verify"),
    ]

    trench_ft = round((power * 1.2 + 4) * _FT_PER_M) if power is not None else None

    physical_fit = PhysicalFit(
        usable_frontage_ft=frontage, ports_that_fit=stalls or None, road_width_ft=width,
        notes=[c for c in concerns if "frontage" in c.lower() or "fit" in c.lower()] or
              ([f"{stalls} stall(s) fit at 5.5 m spacing"] if stalls else []),
    )
    connection = Connection(
        distance_to_power_m=power, trench_len_ft=trench_ft, surface=surface,
        rom_cost_usd=cost, cost_band=_cost_band(cost),
        exclusions=["true grid capacity is private (verify with utility)"],
    )
    demand = Demand(
        notes=[f"{m.get('activity')} curbside markings within 45 m (activity proxy)"]
        if m.get("activity") is not None else [],
    )
    site_conditions = SiteConditions(
        pavement_pci=pci, surface=surface, obstruction_count=n_obst,
        clearance_notes=([f"{n_obst} obstruction(s) within 8 m"] if n_obst else ["no obstructions within 8 m"]),
    )
    accessibility = Accessibility(
        near_curb_ramp=(ada_pass if ada_mapped else None),
        notes=([] if ada_mapped else ["nearest ADA ramp not in this export; verify on site"]),
    )

    next_steps = {
        "go": ["Schedule the on-site survey", "Request grid capacity at the pole", "Confirm curbside parking permit"],
        "conditional": ["On-site survey to resolve the flagged conflict", "Request grid capacity",
                        "Check permit and curbside use"],
        "no_go": ["Re-screen adjacent segments", "Hold pending the disqualifier noted above"],
    }.get(verdict_key, ["Run the live agent survey on this segment", "Schedule an on-site survey if it passes"])

    cv = list((crew.get("context") or {}).get("saw") or [])
    if not cv and crew:
        cv = [str((crew.get(k) or {}).get("finding", ""))[:160]
              for k in ("fit", "connection", "context") if crew.get(k)]
    cv = [c for c in cv if c]

    gen = ("Sonder live swarm · Claude crew deep-dive" if crew else
           "Sonder live swarm · Claude survey" if live else
           "Sonder deterministic screen")

    return SiteReport(
        site=SiteInfo(id=site.get("id", "site"), lat=_num(site.get("lat"), 0) or 0,
                      lon=_num(site.get("lng"), 0) or 0, street=site.get("addr"), region=site.get("nb")),
        verdict=Verdict(tier=tier, composite_score=round(score, 1), one_line_reason=one_line),
        executive_summary=summary,
        scorecard=scorecard,
        physical_fit=physical_fit, connection=connection, demand=demand,
        site_conditions=site_conditions, accessibility=accessibility,
        risks_and_constraints=concerns + ["Zoning, grid capacity, host willingness, and permit are out of scan scope."],
        to_be_verified=verify or ["Final on-site survey", "Grid capacity at the pole", "Curbside / parking permit"],
        next_steps=next_steps,
        evidence=Evidence(photo_ref=site.get("img"), cv_findings=cv),
        generated_by=gen,
    )


def _screen_reason(score, frontage, power, pci):
    bits = []
    if frontage is not None:
        bits.append(f"{frontage:.0f} ft frontage")
    if power is not None:
        bits.append(f"{power:.0f} m to power")
    if pci is not None:
        bits.append(f"PCI {pci:.0f}")
    return f"Screen score {score:.0f} · " + ", ".join(bits) if bits else f"Screen score {score:.0f}"


def build_live_pdf(payload: dict[str, Any]) -> tuple[bytes, str]:
    """Return (pdf_bytes, filename) for one surveyed/screened site."""
    report = _site_report(payload)
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        build_pdf([report], path)
        with open(path, "rb") as f:
            data = f.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return data, f"sonder_{report.site.id}.pdf"
