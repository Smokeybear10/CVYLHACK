"""Tests for the perception stage (Stage 1.5).

Pure-math tests always run (no network). The SDK integration test runs only when
PERCEPTION_SDK_TEST=1 (it downloads the scene); the SAM test also needs FAL_KEY.
"""
import os

import pytest

from perception import measure, config, perceive


# --- pure geometry / scoring (no SDK, always run) ---

def test_segment_endpoints():
    geom = {"type": "LineString", "coordinates": [[-71.103, 42.390], [-71.102, 42.391], [-71.101, 42.392]]}
    a, b = measure.segment_endpoints(geom)
    assert a == (-71.103, 42.390)
    assert b == (-71.101, 42.392)


def test_segment_endpoints_bad_geometry():
    assert measure.segment_endpoints({"type": "Point", "coordinates": [0, 0]}) is None
    assert measure.segment_endpoints({}) is None


def test_dist_point_to_segment():
    a, b = (0.0, 0.0), (10.0, 0.0)
    assert measure.dist_point_to_segment_m((5.0, 3.0), a, b) == pytest.approx(3.0)
    assert measure.dist_point_to_segment_m((5.0, 0.0), a, b) == pytest.approx(0.0)
    assert measure.dist_point_to_segment_m((-4.0, 0.0), a, b) == pytest.approx(4.0)  # clamps to A


def test_usable_frontage_subtracts_on_segment_blockers():
    obstr = [
        {"label": "driveway curb cut", "on_segment": True},   # eats 12
        {"label": "fire hydrant", "on_segment": True},        # eats 5
        {"label": "bus stop", "on_segment": False},           # off segment, ignored
    ]
    assert measure.usable_frontage_ft(40.0, obstr) == pytest.approx(40 - 12 - 5)


def test_usable_frontage_never_negative():
    obstr = [{"label": "bus stop", "on_segment": True}]  # 40 ft footprint
    assert measure.usable_frontage_ft(20.0, obstr) == 0.0


def test_fits_station():
    assert measure.fits_station(23.0, "small") is True      # need 20
    assert measure.fits_station(23.0, "medium") is False    # need 42
    assert measure.fits_station(90.0, "large") is True      # need 84


def test_refined_verdict_matrix():
    assert measure.refined_verdict(fits=False, dist_to_power_m=10, has_blocker=False, sam_used=True) == "No-go"
    assert measure.refined_verdict(fits=True, dist_to_power_m=999, has_blocker=False, sam_used=True) == "No-go"
    assert measure.refined_verdict(fits=True, dist_to_power_m=20, has_blocker=True, sam_used=True) == "Conditional"
    assert measure.refined_verdict(fits=True, dist_to_power_m=20, has_blocker=False, sam_used=False) == "Conditional"
    assert measure.refined_verdict(fits=True, dist_to_power_m=20, has_blocker=False, sam_used=True) == "Go"


def test_on_segment_tagging():
    # a short curb segment in Somerville and an obstruction at its midpoint vs far away
    endpoints = ((-71.1030, 42.3904), (-71.1026, 42.3906))
    mid_lon = (-71.1030 + -71.1026) / 2
    mid_lat = (42.3904 + 42.3906) / 2
    obstr = [
        {"label": "driveway curb cut", "lon": mid_lon, "lat": mid_lat},
        {"label": "bus stop", "lon": -71.1010, "lat": 42.3915},  # ~hundreds of m away
    ]
    tagged = measure.on_segment_obstructions(obstr, endpoints)
    assert tagged[0]["on_segment"] is True
    assert tagged[1]["on_segment"] is False


def test_required_frontage_config():
    assert config.required_frontage_ft("small") == 20.0
    assert config.required_frontage_ft("unknown") == 20.0  # falls back to default


# --- SDK integration (opt-in) ---

sdk = pytest.mark.skipif(
    os.getenv("PERCEPTION_SDK_TEST") != "1",
    reason="set PERCEPTION_SDK_TEST=1 to run the real-scene test (downloads data)",
)


@sdk
def test_real_pipeline_on_segment():
    # a real curb segment inside the pavement/pole overlap strip
    feature = {
        "type": "Feature",
        "geometry": {"type": "LineString",
                     "coordinates": [[-71.10310, 42.39040], [-71.10280, 42.39060]]},
        "properties": {"cand_id": "test-seg-1", "verdict": "Go", "score": 70,
                       "length_ft": 30.0, "dist_to_power_m": 18.0},
    }
    site = perceive(feature, station_size="small", use_cache=False, render=True)
    assert site["measured"] is True
    assert site["segment_frontage_ft"] > 0
    assert site["frontage_source"] in ("scan", "geometry", "screening")
    assert site["refined_verdict"] in ("Go", "Conditional", "No-go")
    assert site["dist_to_power_m"] is not None
    # JSON serializable (frontend boundary)
    import json
    json.dumps(site)


@sdk
@pytest.mark.skipif(not config.sam_available(), reason="needs FAL_KEY + cyvl[sam]")
def test_sam_runs_when_keyed():
    from perception import scene, segment
    frame = scene.nearest_frame(-71.1030, 42.3905)
    obstr, used, _ = segment.locate_obstructions(frame)
    assert used is True
    assert isinstance(obstr, list)
