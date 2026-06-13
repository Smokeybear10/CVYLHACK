"""Orchestrator tests: breadth waves, caching, winner selection, error resilience, cost cap."""
import pytest

from swarm import orchestrator, providers, mock_data, config
from swarm.schema import Verdict


def _inputs():
    return mock_data.finalists(), mock_data.measurements(), mock_data.priorities()


def test_breadth_one_verdict_per_site():
    sites, meas, prefs = _inputs()
    verdicts = list(orchestrator.run_breadth(sites, meas, prefs))
    assert len(verdicts) == len(sites)
    assert {v.site_id for v in verdicts} == {s.site_id for s in sites}


def test_breadth_expected_labels():
    sites, meas, prefs = _inputs()
    by = {v.site_id: v.verdict for v in orchestrator.run_breadth(sites, meas, prefs)}
    assert by["seg_001"] == "go"
    assert by["seg_003"] == "no_go"
    assert by["seg_002"] == "conditional"


def test_cache_avoids_second_call(monkeypatch):
    sites, meas, prefs = _inputs()
    sites = sites[:2]
    calls = {"n": 0}
    real = providers.surveyor_verdict

    def counting(site, m, p):
        calls["n"] += 1
        return real(site, m, p)

    monkeypatch.setattr(providers, "surveyor_verdict", counting)
    list(orchestrator.run_breadth(sites, meas, prefs))   # populates cache
    first = calls["n"]
    list(orchestrator.run_breadth(sites, meas, prefs))   # should hit cache
    assert first == 2 and calls["n"] == 2                # no new calls


def test_missing_measurement_yields_error_verdict():
    sites, meas, prefs = _inputs()
    meas.pop("seg_001")
    verdicts = {v.site_id: v for v in orchestrator.run_breadth(sites, meas, prefs)}
    assert verdicts["seg_001"].source == "swarm.breadth.error"
    assert verdicts["seg_001"].error and verdicts["seg_001"].confidence == 0.0


def test_agent_exception_isolated(monkeypatch):
    sites, meas, prefs = _inputs()

    def fake(site, m, p):
        if site.site_id == "seg_002":
            raise RuntimeError("simulated agent failure")
        return Verdict(site_id=site.site_id, verdict="go", confidence=0.9, one_line_reason="ok",
                       rationale="ok", positives=[], concerns=[], verify_on_site=[],
                       evidence_image_url="", sub_scores={})

    monkeypatch.setattr(providers, "surveyor_verdict", fake)
    verdicts = {v.site_id: v for v in orchestrator.run_breadth(sites, meas, prefs)}
    assert verdicts["seg_002"].source == "swarm.breadth.error"   # flagged, not crashed
    assert verdicts["seg_001"].verdict == "go"                   # others fine
    assert len(verdicts) == len(sites)


def test_max_breadth_cap(monkeypatch):
    monkeypatch.setattr(config, "MAX_BREADTH_SITES", 2)
    sites, meas, prefs = _inputs()
    verdicts = list(orchestrator.run_breadth(sites, meas, prefs))
    assert len(verdicts) == 2


def test_pick_winners_prefers_go():
    sites, meas, prefs = _inputs()
    verdicts = list(orchestrator.run_breadth(sites, meas, prefs))
    winners = orchestrator.pick_winners(verdicts, sites, n=1)
    assert winners == ["seg_001"]


def test_run_crew_mock_has_crew_block():
    sites, meas, prefs = _inputs()
    site = next(s for s in sites if s.site_id == "seg_001")
    cv = orchestrator.run_crew(site, meas["seg_001"], prefs)
    assert isinstance(cv, Verdict)
    assert cv.crew and set(cv.crew) == {"fit", "connection", "context"}
    assert cv.source.startswith("swarm.crew.judge")


def test_stale_cache_file_is_ignored(tmp_path, monkeypatch):
    sites, meas, prefs = _inputs()
    monkeypatch.setattr(orchestrator, "CACHE_DIR", tmp_path)
    tmp_path.mkdir(exist_ok=True)
    key = orchestrator._cache_key(sites[0], prefs)
    (tmp_path / f"{key}.json").write_text('{"unexpected": "old schema"}')
    # should not raise; treats the bad file as a miss and re-surveys
    assert orchestrator._cache_get(key) is None
