"""End-to-end HTTP tests via FastAPI TestClient (mock mode, no API calls)."""
import dataclasses

from fastapi.testclient import TestClient

from swarm import mock_data
from swarm.service import app

client = TestClient(app)


def _finalist_dict(site_id):
    d = dataclasses.asdict(mock_data.finalists()[0])
    d["site_id"] = site_id
    return d


def _meas_dict(site_id):
    return dataclasses.asdict(mock_data.measurements()["seg_001"]) | {"site_id": site_id}


def test_health():
    r = client.get("/health").json()
    assert r["ok"] is True and r["mode"] == "mock"


def test_mock_refused_without_flag():
    # no finalists/measurements and no allow_mock -> 400 (mock can't reach a demo by accident)
    r = client.post("/survey", json={"deep_dive": True})
    assert r.status_code == 400


def test_survey_full_run():
    r = client.post("/survey", json={"deep_dive": True, "allow_mock": True}).json()
    assert len(r["verdicts"]) == 6
    assert r["winners"] == ["seg_001"]
    assert r["crew"][0]["crew"]                 # crew block present on the winner
    assert r["verdicts"][0]["lon"] is not None  # coords carried for the map


def test_survey_no_deep_dive():
    r = client.post("/survey", json={"deep_dive": False, "allow_mock": True}).json()
    assert "winners" not in r and "crew" not in r


def test_stream_emits_events():
    r = client.post("/survey/stream", json={"deep_dive": True, "allow_mock": True})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    body = r.text
    assert body.count("event: verdict") == 6
    assert "event: winner" in body
    assert "event: done" in body


def test_incomplete_finalist_returns_422():
    # both provided (passes the mock guard), but the finalist is missing required fields
    r = client.post("/survey", json={"finalists": [{"site_id": "x"}],
                                      "measurements": {"x": _meas_dict("x")}})
    assert r.status_code == 422


def test_missing_measurement_returns_422():
    fin = _finalist_dict("zzz")
    meas = {"seg_001": _meas_dict("seg_001")}   # non-empty, but lacks 'zzz'
    r = client.post("/survey", json={"finalists": [fin], "measurements": meas})
    assert r.status_code == 422


def test_custom_complete_inputs_ok():
    fin = _finalist_dict("seg_001")
    meas = {"seg_001": _meas_dict("seg_001")}
    r = client.post("/survey", json={"finalists": [fin], "measurements": meas, "deep_dive": False})
    assert r.status_code == 200
    assert len(r.json()["verdicts"]) == 1
