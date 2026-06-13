"""Judging constants, derived from the research (research/00-SYNTHESIS.md).

Machine-readable counterparts to skills.md. Used by the deterministic generator
and the validators so gates, tiers, and ratings are computed consistently in code
rather than left to the model.
"""
from __future__ import annotations

# Composite score (0-100) -> tier. Gated sites are always No-go regardless.
# Bands follow the screening verdict (Go >= 70, Conditional >= 45) refined into tiers.
TIER_1_MIN = 80.0
TIER_2_MIN = 62.0
TIER_3_MIN = 45.0

# Component sub-score (0-1) -> RAG rating for the scorecard.
RATING_GO_MIN = 0.66
RATING_CAUTION_MIN = 0.40

TRENCH_FT_PER_M = 3.281
DEFAULT_REQUIRED_FRONTAGE_FT = 20.0  # one curbside L2 parallel stall, ~6 m

# The fixed set of things a curb scan cannot establish; every report carries these
# so unknowns are deferred, never guessed (the anti-hallucination convention).
VERIFY_ON_SITE = [
    "True grid / transformer capacity and available service amperage",
    "Single vs three-phase power and voltage at the connection point",
    "Utility make-ready scope, interconnection queue, and transformer lead time",
    "Permit and curb-use approval from the city",
    "ADA running and cross slope of the path of travel",
    "On-street parking regulations and any time limits",
    "Tree roots, drainage, and snow-storage conflicts",
]

# Standard exclusions on the rough-order-of-magnitude make-ready estimate.
COST_EXCLUSIONS = [
    "Utility-side make-ready (transformer, service drop) if an upgrade is needed",
    "Soft costs: permitting, design, project management",
    "Charger hardware and networking",
    "Restoration beyond the trench (landscaping, sidewalk panels)",
]


def tier_from(composite_score: float, gated: bool) -> str:
    if gated:
        return "No-go"
    if composite_score >= TIER_1_MIN:
        return "Tier 1"
    if composite_score >= TIER_2_MIN:
        return "Tier 2"
    if composite_score >= TIER_3_MIN:
        return "Tier 3"
    return "No-go"


def rating_from(sub_score: float | None) -> str:
    if sub_score is None:
        return "CAUTION"
    if sub_score >= RATING_GO_MIN:
        return "GO"
    if sub_score >= RATING_CAUTION_MIN:
        return "CAUTION"
    return "NO-GO"
