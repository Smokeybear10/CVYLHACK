"""Unit tests for gating and scoring. No network, no geometry."""
import math

import pytest

from screening import config
from screening import scoring as S
from screening.scoring import Filters


# --- component sub-scores ----------------------------------------------------

def test_power_score_bounds_and_monotonic():
    assert S.power_score(0) == 1.0
    assert S.power_score(config.POWER_FULL_M) == 1.0
    assert S.power_score(config.POWER_ZERO_M) == 0.0
    assert S.power_score(1e9) == 0.0
    assert S.power_score(float("inf")) == 0.0
    assert S.power_score(float("nan")) == 0.0
    mid = S.power_score((config.POWER_FULL_M + config.POWER_ZERO_M) / 2)
    assert 0.0 < mid < 1.0
    # closer is never worse
    assert S.power_score(20) >= S.power_score(40) >= S.power_score(80)


def test_fit_score():
    assert S.fit_score(0, 20) == 0.0
    assert S.fit_score(None, 20) == 0.0
    assert S.fit_score(10, 20) == pytest.approx(0.5)
    assert S.fit_score(20, 20) == 1.0
    assert S.fit_score(40, 20) == 1.0  # clamped


def test_demand_signals_residential_vs_traffic():
    # residential: local/collector high, arterial/freeway low
    assert S.residential_score(7) > S.residential_score(4) > S.residential_score(1)
    assert S.residential_score(None) == config.DEFAULT_RESIDENTIAL
    assert S.residential_score(99) == config.DEFAULT_RESIDENTIAL
    # traveler/through-traffic with curb access: arterial high, freeway and local low
    assert S.traffic_score(3) > S.traffic_score(5) > S.traffic_score(1)
    assert S.traffic_score(None) == config.DEFAULT_TRAFFIC
    assert S.traffic_score("x") == config.DEFAULT_TRAFFIC


def test_demand_mix_blends_both_use_cases():
    local, arterial = 7, 3
    # all-residential mix favors the local street; all-traveler mix favors the arterial
    assert S.demand_score(local, mix=1.0) > S.demand_score(arterial, mix=1.0)
    assert S.demand_score(arterial, mix=0.0) > S.demand_score(local, mix=0.0)
    # balanced considers both, so a collector (good for either) beats a freeway
    assert S.demand_score(5, mix=0.5) > S.demand_score(1, mix=0.5)
    # mix is clamped; out-of-range does not crash or escape [0,1]
    assert 0.0 <= S.demand_score(4, mix=5.0) <= 1.0


def test_pavement_obstruction_bounds():
    assert S.pavement_score(0) == 0.0
    assert S.pavement_score(100) == 1.0
    assert S.pavement_score(None) == 0.0
    assert S.obstruction_score(0) == 1.0
    assert S.obstruction_score(config.OBSTRUCTION_FULL_PENALTY_AT) == 0.0
    assert S.obstruction_score(100) == 0.0  # clamped, never negative


# --- gates -------------------------------------------------------------------

def _good_row():
    return {
        "dist_to_power_m": 12.0, "length_ft": 30.0, "label": "Good",
        "disqualify_marking": False, "pci": 85.0,
        "obstruction_count": 0, "functional_class": 4.0,
    }


def test_gate_passes_good_row():
    assert S.gate(_good_row(), required_ft=18.0) == []


def test_gate_catches_each_failure():
    r = _good_row(); r["dist_to_power_m"] = 500.0
    assert "no power within range" in S.gate(r, 18.0)
    r = _good_row(); r["dist_to_power_m"] = float("inf")
    assert "no power within range" in S.gate(r, 18.0)
    r = _good_row(); r["length_ft"] = 10.0
    assert "frontage too small for station size" in S.gate(r, 18.0)
    r = _good_row(); r["label"] = "Failed"
    assert "pavement failed" in S.gate(r, 18.0)
    r = _good_row(); r["disqualify_marking"] = True
    assert any("fire" in x for x in S.gate(r, 18.0))


# --- total score -------------------------------------------------------------

def test_score_row_gated_is_zero_nogo():
    r = _good_row(); r["dist_to_power_m"] = 999.0
    out = S.score_row(r, Filters(), Filters().resolved_weights(), 18.0)
    assert out["gated"] is True
    assert out["score"] == 0.0
    assert out["verdict"] == "No-go"
    assert out["gate_reasons"]


def test_score_row_in_bounds_and_components():
    out = S.score_row(_good_row(), Filters(), Filters().resolved_weights(), 18.0)
    assert 0.0 <= out["score"] <= 100.0
    assert set(out["components"]) == set(config.DEFAULT_WEIGHTS)
    assert all(0.0 <= v <= 1.0 for v in out["components"].values())
    assert out["verdict"] in {"Go", "Conditional", "No-go"}


def test_verdict_thresholds():
    assert S.verdict_for(90, False) == "Go"
    assert S.verdict_for(config.GO_THRESHOLD, False) == "Go"
    assert S.verdict_for(50, False) == "Conditional"
    assert S.verdict_for(10, False) == "No-go"
    assert S.verdict_for(95, True) == "No-go"  # gated overrides score


# --- filters -----------------------------------------------------------------

def test_weights_normalize_to_one():
    w = Filters(weights={"power": 10}).resolved_weights()
    assert math.isclose(sum(w.values()), 1.0, rel_tol=1e-9)
    assert w["power"] > config.DEFAULT_WEIGHTS["power"]  # boosting power raised its share


def test_all_zero_weights_fall_back_to_defaults():
    w = Filters(weights={k: 0 for k in config.DEFAULT_WEIGHTS}).resolved_weights()
    assert math.isclose(sum(w.values()), 1.0, rel_tol=1e-9)


def test_required_frontage_from_size_and_override():
    assert Filters(station_size="small").required_frontage() == config.SIZE_FRONTAGE_FT["small"]
    assert Filters(station_size="large").required_frontage() == config.SIZE_FRONTAGE_FT["large"]
    assert Filters(required_frontage_ft=99).required_frontage() == 99.0
    # unknown size falls back to default, does not crash
    assert Filters(station_size="bogus").required_frontage() == config.SIZE_FRONTAGE_FT[config.DEFAULT_SIZE]


def test_power_weight_changes_ranking_direction():
    near = _good_row(); near["dist_to_power_m"] = 8.0; near["functional_class"] = 7
    far = _good_row(); far["dist_to_power_m"] = 110.0; far["functional_class"] = 3
    power_heavy = Filters(weights={"power": 1.0})
    s_near = S.score_row(near, power_heavy, power_heavy.resolved_weights(), 18.0)["score"]
    s_far = S.score_row(far, power_heavy, power_heavy.resolved_weights(), 18.0)["score"]
    assert s_near > s_far  # with power dominant, the near-power site wins
