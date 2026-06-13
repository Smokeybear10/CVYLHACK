"""Integration tests against the cached real data.

Skipped automatically if the cache is not present (so unit tests still run in CI
without network). Populate the cache by running the module once, or download the
layers from the public bucket / Google Drive into screening/_cache/.
"""
import json

import pytest

from screening import config, screen
from screening.scoring import Filters

_HAVE_CACHE = (config.CACHE_DIR / "pavements_v2.geojson").exists()
pytestmark = pytest.mark.skipif(not _HAVE_CACHE, reason="data cache not present")


def test_demo_region_returns_well_formed_result():
    r = screen(region=config.DEMO_BBOX)
    assert set(r) == {"candidates", "top", "summary"}
    s = r["summary"]
    assert s["n_candidates"] > 0
    # verdict counts partition the candidates
    assert s["n_go"] + s["n_conditional"] + s["n_nogo"] == s["n_candidates"]
    assert s["n_go"] > 0 and s["n_nogo"] > 0  # healthy spread in the overlap strip


def test_result_is_json_serializable():
    r = screen(region=config.DEMO_BBOX)
    json.dumps(r)  # must not raise (no NaN/inf/numpy leaking through)


def test_top_is_sorted_and_capped():
    r = screen(region=config.DEMO_BBOX, top_n=10)
    scores = [t["score"] for t in r["top"]]
    assert scores == sorted(scores, reverse=True)
    assert len(r["top"]) <= 10
    for t in r["top"]:
        assert t["lon"] is not None and t["lat"] is not None


def test_candidates_sorted_best_first():
    r = screen(region=config.DEMO_BBOX)
    scores = [f["properties"]["score"] for f in r["candidates"]["features"]]
    assert scores == sorted(scores, reverse=True)


def test_filters_change_the_ranking():
    base = screen(region=config.DEMO_BBOX, filters=Filters(weights={"demand": 1.0}))
    powered = screen(region=config.DEMO_BBOX, filters=Filters(weights={"power": 1.0}))
    # different priorities should not produce an identical top list
    assert [t["cand_id"] for t in base["top"]] != [t["cand_id"] for t in powered["top"]]


def test_demand_mix_shifts_ranking_residential_vs_traveler():
    residential = screen(region=config.DEMO_BBOX,
                         filters=Filters(weights={"demand": 1.0}, demand_mix=1.0))
    traveler = screen(region=config.DEMO_BBOX,
                      filters=Filters(weights={"demand": 1.0}, demand_mix=0.0))
    # leaning fully residential vs fully traveler should reorder the finalists
    assert [t["cand_id"] for t in residential["top"]] != [t["cand_id"] for t in traveler["top"]]


def test_empty_region_clean():
    r = screen(region=[10.0, 10.0, 11.0, 11.0])  # middle of nowhere
    assert r["summary"]["n_candidates"] == 0
    assert r["candidates"]["features"] == []
    assert r["top"] == []
    json.dumps(r)


def test_determinism():
    a = screen(region=config.DEMO_BBOX)
    b = screen(region=config.DEMO_BBOX)
    assert a["summary"] == b["summary"]
    assert [t["cand_id"] for t in a["top"]] == [t["cand_id"] for t in b["top"]]


def test_dict_filters_accepted():
    r = screen(region=config.DEMO_BBOX, filters={"station_size": "large", "weights": {"power": 0.5}})
    assert r["summary"]["filters"]["station_size"] == "large"
    assert r["summary"]["filters"]["required_frontage_ft"] == config.SIZE_FRONTAGE_FT["large"]
