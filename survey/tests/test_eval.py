"""The eval harness proves the swarm is reliable with hard metrics."""
from survey.client import StubClient
from survey.evals import run_eval


def test_eval_metrics_are_green():
    m = run_eval(StubClient(), runs=2)
    assert m["n_sites"] > 0
    assert m["schema_valid_rate"] == 1.0
    assert m["grounding_violations"] == 0
    assert m["hallucination_rate"] == 0.0
    assert m["consistency_violations"] == 0
    assert m["fallback_count"] == 0
    assert m["determinism"] is True
    assert m["tier_agreement"] == 1.0
