"""Gating and weighted scoring.

Two stages. Hard gates remove obvious No-gos (no power in range, frontage too
small for the chosen station size, failed pavement). Survivors get a weighted
score from 0 to 100, where the filter weights are the only knobs. Every score
keeps its component breakdown so the report can explain it.

Nothing here touches the network or geometry; it operates on the enriched
candidate frame from features.py, so it is fully unit-testable.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

from . import config


@dataclass
class Filters:
    """User-facing screening inputs.

    station_size: one of SIZE_FRONTAGE_FT keys; sets the required frontage.
    weights: component -> weight; merged over defaults, then normalized.
    required_frontage_ft: overrides the size-derived requirement when given.
    """
    station_size: str = config.DEFAULT_SIZE
    weights: dict = field(default_factory=dict)
    required_frontage_ft: float | None = None
    demand_mix: float = config.DEFAULT_DEMAND_MIX  # fraction residential vs traveler

    def resolved_weights(self) -> dict:
        merged = dict(config.DEFAULT_WEIGHTS)
        for k, v in (self.weights or {}).items():
            if k in merged:  # ignore unknown keys rather than crash later
                merged[k] = v
        total = sum(max(0.0, v) for v in merged.values())
        if total <= 0:
            return dict(config.DEFAULT_WEIGHTS)  # already sums to 1
        return {k: max(0.0, v) / total for k, v in merged.items()}

    def required_frontage(self) -> float:
        if self.required_frontage_ft is not None:
            return float(self.required_frontage_ft)
        return config.SIZE_FRONTAGE_FT.get(self.station_size, config.SIZE_FRONTAGE_FT[config.DEFAULT_SIZE])


def _clamp01(x: float) -> float:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return 0.0
    return max(0.0, min(1.0, float(x)))


# --- component sub-scores (each 0..1) ---------------------------------------

def power_score(dist_m: float) -> float:
    if dist_m is None or math.isinf(dist_m) or math.isnan(dist_m):
        return 0.0
    if dist_m <= config.POWER_FULL_M:
        return 1.0
    if dist_m >= config.POWER_ZERO_M:
        return 0.0
    span = config.POWER_ZERO_M - config.POWER_FULL_M
    return _clamp01((config.POWER_ZERO_M - dist_m) / span)


def fit_score(length_ft: float, required_ft: float) -> float:
    if not length_ft or length_ft <= 0:
        return 0.0
    return _clamp01(length_ft / required_ft)  # 1.0 once the segment meets the requirement


def _fclass(functional_class):
    try:
        return int(functional_class)
    except (TypeError, ValueError):
        return None


def residential_score(functional_class) -> float:
    """Overnight-residential suitability: local and collector streets score high."""
    fc = _fclass(functional_class)
    if fc is None:
        return config.DEFAULT_RESIDENTIAL
    return config.RESIDENTIAL_BY_FCLASS.get(fc, config.DEFAULT_RESIDENTIAL)


def traffic_score(functional_class) -> float:
    """Traveler / through-traffic suitability with curb access: arterials and
    collectors score high, freeways and pure-local streets low."""
    fc = _fclass(functional_class)
    if fc is None:
        return config.DEFAULT_TRAFFIC
    return config.TRAFFIC_BY_FCLASS.get(fc, config.DEFAULT_TRAFFIC)


def demand_score(functional_class, mix: float = config.DEFAULT_DEMAND_MIX) -> float:
    """Blend residential and traveler demand. mix is the fraction on residential
    (0 = all traveler, 1 = all residential, 0.5 = balanced, the default)."""
    mix = _clamp01(mix)
    return mix * residential_score(functional_class) + (1.0 - mix) * traffic_score(functional_class)


def pavement_score(pci: float) -> float:
    return _clamp01((pci or 0.0) / 100.0)


def obstruction_score(count: int) -> float:
    # 1.0 = clear, decreasing with each obstruction in the frontage.
    return _clamp01(1.0 - (count or 0) / config.OBSTRUCTION_FULL_PENALTY_AT)


# --- gating and total --------------------------------------------------------

def gate(row, required_ft: float) -> list:
    """Return a list of gate-failure reasons; empty list means the segment passes."""
    reasons = []
    dist = row.get("dist_to_power_m")
    if dist is None or math.isinf(dist) or dist > config.POWER_GATE_M:
        reasons.append("no power within range")
    length = row.get("length_ft") or 0.0
    if length < required_ft:
        reasons.append("frontage too small for station size")
    if str(row.get("label")) == config.FAILED_LABEL:
        reasons.append("pavement failed")
    if bool(row.get("disqualify_marking")):
        reasons.append("fire lane or no-parking marking present")
    return reasons


def verdict_for(score: float, gated: bool) -> str:
    if gated:
        return "No-go"
    if score >= config.GO_THRESHOLD:
        return "Go"
    if score >= config.CONDITIONAL_THRESHOLD:
        return "Conditional"
    return "No-go"


def score_row(row, filters: Filters, weights: dict, required_ft: float) -> dict:
    components = {
        "power": power_score(row.get("dist_to_power_m")),
        "demand": demand_score(row.get("functional_class"), filters.demand_mix),
        "fit": fit_score(row.get("length_ft"), required_ft),
        "pavement": pavement_score(row.get("pci")),
        "obstruction": obstruction_score(row.get("obstruction_count")),
    }
    raw = sum(weights.get(k, 0.0) * components[k] for k in components)
    score = round(100.0 * _clamp01(raw), 1)
    reasons = gate(row, required_ft)
    gated = len(reasons) > 0
    if gated:
        score = 0.0
    return {
        "score": score,
        "components": {k: round(v, 3) for k, v in components.items()},
        "gated": gated,
        "gate_reasons": reasons,
        "verdict": verdict_for(score, gated),
    }


def score_candidates(gdf, filters: Filters | None = None):
    """Score an enriched candidate frame in place-ish; returns a new GeoDataFrame.

    Adds columns: score, verdict, gated, gate_reasons, components (dict).
    """
    filters = filters or Filters()
    weights = filters.resolved_weights()
    required_ft = filters.required_frontage()

    out = gdf.copy()
    if len(out) == 0:
        for col in ("score", "verdict", "gated", "gate_reasons", "components"):
            out[col] = pd.Series(dtype="object")
        return out

    results = [score_row(r, filters, weights, required_ft) for r in out.to_dict("records")]
    out["score"] = [r["score"] for r in results]
    out["verdict"] = [r["verdict"] for r in results]
    out["gated"] = [r["gated"] for r in results]
    out["gate_reasons"] = [r["gate_reasons"] for r in results]
    out["components"] = [r["components"] for r in results]
    return out.sort_values("score", ascending=False).reset_index(drop=True)
