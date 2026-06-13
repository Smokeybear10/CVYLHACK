"""Schema sanity: serialization and no shared mutable defaults."""
from swarm.schema import Verdict, UserPriorities


def test_verdict_to_dict_includes_error_default():
    v = Verdict(site_id="a", verdict="go", confidence=0.9, one_line_reason="r", rationale="r",
                positives=[], concerns=[], verify_on_site=[], evidence_image_url="", sub_scores={})
    d = v.to_dict()
    assert d["site_id"] == "a"
    assert d["error"] is None
    assert d["crew"] is None
    assert d["source"] == "swarm.breadth"


def test_priorities_weights_not_shared():
    a, b = UserPriorities(), UserPriorities()
    a.weights["power"] = 9.0
    assert b.weights["power"] == 1.0   # default_factory, not a shared dict
