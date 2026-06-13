"""Deterministic report generator.

Builds a fully grounded SiteReport from a SiteBundle using only bundle numbers.
Two jobs: the offline stub judgment (for development, tests, and when there is no
API key) and the failure fallback when a live agent errors. Because it only ever
restates bundle values, its output passes the grounding guard by construction.
"""
from __future__ import annotations

from . import criteria
from .schema import (
    Accessibility, Connection, Demand, Evidence, PhysicalFit, ScoreRow,
    SiteBundle, SiteConditions, SiteReport, Verdict,
)

CRITERION_LABELS = {
    "power": "Power proximity / make-ready",
    "demand": "Demand (residential + traveler)",
    "fit": "Physical fit",
    "pavement": "Pavement condition",
    "obstruction": "Obstruction clearance",
}
CRITERION_SOURCE = {  # provenance tag per the report convention
    "power": "have", "demand": "partial", "fit": "partial",
    "pavement": "have", "obstruction": "partial",
}


def _f(x, fmt="{:.0f}"):
    return fmt.format(x) if x is not None else "n/a"


def _scorecard(b: SiteBundle) -> list[ScoreRow]:
    m, d = b.measured, b.derived
    values = {
        "power": f"{_f(m.distance_to_power_m)} m to nearest power; cost band {d.cost_band or 'n/a'}",
        "demand": f"residential {_f(d.residential_suit, '{:.2f}')}, traveler {_f(d.traveler_suit, '{:.2f}')}",
        "fit": f"{_f(m.usable_frontage_ft)} ft frontage, fits {_f(d.ports_that_fit)} port(s)",
        "pavement": f"PCI {_f(m.pavement_pci)}",
        "obstruction": f"{m.obstruction_count} in frontage buffer",
    }
    rows = []
    for key, score in d.component_scores.items():
        rows.append(ScoreRow(
            criterion=CRITERION_LABELS.get(key, key),
            value=values.get(key, _f(score, "{:.2f}")),
            rating=criteria.rating_from(score),
            source=CRITERION_SOURCE.get(key, "partial"),
        ))
    return rows


def _one_line(b: SiteBundle) -> str:
    d, m = b.derived, b.measured
    if d.gated:
        reason = d.gate_reasons[0] if d.gate_reasons else "fails screening thresholds"
        return f"No-go: {reason}."
    return (f"{d.tier_hint}: power {_f(m.distance_to_power_m)} m away, "
            f"fits {_f(d.ports_that_fit)} curbside port(s), pavement PCI {_f(m.pavement_pci)}.")


def _exec_summary(b: SiteBundle) -> list[str]:
    d, m = b.derived, b.measured
    bullets = [
        f"Screening tier: {d.tier_hint} (composite score {_f(d.composite_score, '{:.1f}')}).",
        f"Nearest power asset is {_f(m.distance_to_power_m)} m away; estimated make-ready "
        f"cost band {d.cost_band or 'n/a'}.",
        f"Curb frontage {_f(m.usable_frontage_ft)} ft fits about {_f(d.ports_that_fit)} "
        f"curbside L2 port(s) at {_f(d.required_frontage_ft)} ft each.",
    ]
    if d.gated:
        bullets.append("Gated as No-go in screening: " + "; ".join(d.gate_reasons) + ".")
    else:
        bullets.append("Passed all screening gates; recommend a site visit to confirm the "
                       "deferred items below before design.")
    return bullets


def _risks(b: SiteBundle) -> list[str]:
    d = b.derived
    risks = list(d.gate_reasons)
    for key, score in d.component_scores.items():
        if criteria.rating_from(score) == "NO-GO":
            risks.append(f"Weak {CRITERION_LABELS.get(key, key).lower()} (sub-score "
                         f"{_f(score, '{:.2f}')}).")
    if not risks:
        risks.append("No screening-level risks flagged; physical and grid items remain to verify.")
    return risks


def _next_steps(b: SiteBundle) -> list[str]:
    if b.derived.gated:
        return ["Deprioritize this segment for the reasons above.",
                "Re-evaluate only if the limiting factor (usually power distance) changes."]
    return [
        "Schedule a curbside site visit to confirm the deferred items.",
        "Request a utility load letter to confirm capacity and phase at the connection point.",
        "Confirm parking regulation and curb-use permit with the city.",
    ]


def build_report(bundle: SiteBundle, generated_by: str = "stub") -> SiteReport:
    b, m, d = bundle, bundle.measured, bundle.derived
    pole = m.pole_type or "nearest power asset (pole or luminaire; type to confirm)"
    return SiteReport(
        site=b.site,
        verdict=Verdict(tier=d.tier_hint, composite_score=d.composite_score,
                        one_line_reason=_one_line(b)),
        executive_summary=_exec_summary(b),
        scorecard=_scorecard(b),
        physical_fit=PhysicalFit(
            usable_frontage_ft=m.usable_frontage_ft, ports_that_fit=d.ports_that_fit,
            road_width_ft=m.road_width_ft,
            notes=[f"Frontage is the Stage 1 segment-length proxy at {_f(d.required_frontage_ft)} "
                   f"ft per port; true usable frontage is measured from the 3D scan in Stage 2."],
        ),
        connection=Connection(
            distance_to_power_m=m.distance_to_power_m, pole_type=pole,
            trench_len_ft=d.trench_len_ft, surface=m.surface,
            rom_cost_usd=d.rom_cost_usd, cost_band=d.cost_band,
            exclusions=list(criteria.COST_EXCLUSIONS),
        ),
        demand=Demand(
            residential_suit=d.residential_suit, traveler_suit=d.traveler_suit,
            functional_class=d.functional_class, nearby_chargers=b.public.nearby_chargers,
            notes=[f"Road class: {b.public.road_class or 'n/a'}. Demand blends overnight "
                   f"residential and through-traveler suitability."],
        ),
        site_conditions=SiteConditions(
            pavement_pci=m.pavement_pci, surface=m.surface,
            obstruction_count=m.obstruction_count,
            clearance_notes=[f"{m.obstruction_count} mapped obstruction(s) within the frontage "
                             f"buffer; precise curb clearances are confirmed by CV and on site."],
        ),
        accessibility=Accessibility(
            near_curb_ramp=None,
            notes=["ADA path width, ramp proximity, and slope are confirmed on site (Stage 2 CV "
                   "assists, final check is a survey)."],
        ),
        risks_and_constraints=_risks(b),
        to_be_verified=list(b.known_unknowns),
        next_steps=_next_steps(b),
        evidence=Evidence(photo_ref=b.evidence.photo_ref, cv_findings=list(b.evidence.cv_findings)),
        generated_by=generated_by,
    )
