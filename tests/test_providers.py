"""Provider unit tests: mock gates, output normalization, JSON parsing."""
import pytest

from swarm import providers, mock_data
from swarm.schema import Verdict


def test_mock_mode_active():
    assert providers.have_key() is False


def test_parse_json_plain():
    assert providers._parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_fenced():
    assert providers._parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_with_prose_around():
    assert providers._parse_json('Here you go: {"a": 1} done')["a"] == 1


def test_parse_json_no_object_raises():
    with pytest.raises(ValueError):
        providers._parse_json("no json here")


def test_normalize_fills_defaults():
    out = providers._normalize({})
    assert out["verdict"] == "conditional"
    assert out["confidence"] == 0.5
    assert out["positives"] == [] and out["sub_scores"] == {}


def test_normalize_clamps_confidence_and_coerces():
    out = providers._normalize({"confidence": 5, "verdict": "bogus", "positives": "tight"})
    assert out["confidence"] == 1.0          # clamped to [0,1]
    assert out["verdict"] == "conditional"   # invalid label -> conditional
    assert out["positives"] == ["tight"]     # scalar -> list


def test_normalize_bad_confidence_type():
    assert providers._normalize({"confidence": "abc"})["confidence"] == 0.5


def _site_meas(site_id):
    site = next(s for s in mock_data.finalists() if s.site_id == site_id)
    meas = mock_data.measurements()[site_id]
    return site, meas


@pytest.mark.parametrize("site_id,expected", [
    ("seg_001", "go"),           # clean
    ("seg_002", "conditional"),  # bus stop on frontage
    ("seg_003", "no_go"),        # frontage 11ft < 18ft
    ("seg_005", "no_go"),        # power 41m > 30m
    ("seg_006", "no_go"),        # pavement PCI 18 < 25
])
def test_mock_gates(site_id, expected):
    site, meas = _site_meas(site_id)
    v = providers.surveyor_verdict(site, meas, mock_data.priorities())
    assert isinstance(v, Verdict)
    assert v.verdict == expected
    assert v.source == "swarm.breadth.mock"
    assert 0.0 <= v.confidence <= 1.0
    assert v.evidence_image_url  # carried through from measurements
