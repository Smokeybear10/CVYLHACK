"""The reliability stack: grounding guard and consistency checks."""
from survey.deterministic import build_report
from survey.validators import consistency_checks, grounding_guard, validate


def test_clean_report_is_grounded_and_valid(one_bundle):
    rep = build_report(one_bundle)
    assert grounding_guard(rep, one_bundle) == []
    assert consistency_checks(rep, one_bundle) == []
    assert validate(rep, one_bundle).ok


def test_grounding_guard_catches_hallucinated_number(one_bundle):
    d = build_report(one_bundle).model_dump()
    d["connection"]["rom_cost_usd"] = 999999.0  # nowhere in the bundle
    res = validate(d, one_bundle)
    assert not res.ok
    assert any("999999" in v for v in res.grounding_violations)


def test_grounding_guard_catches_hallucinated_number_in_prose(one_bundle):
    d = build_report(one_bundle).model_dump()
    d["executive_summary"].append("Transformer has 480 kVA of spare capacity.")  # invented
    res = validate(d, one_bundle)
    assert not res.ok
    assert any("480" in v for v in res.grounding_violations)


def test_identity_fields_not_flagged(one_bundle):
    # site id digits and region bbox coords must not count as ungrounded
    rep = build_report(one_bundle)
    assert grounding_guard(rep, one_bundle) == []


def test_consistency_catches_gated_not_nogo(gated_bundle):
    d = build_report(gated_bundle).model_dump()
    d["verdict"]["tier"] = "Tier 1"
    res = validate(d, gated_bundle)
    assert not res.ok
    assert any("No-go" in v or "tier" in v for v in res.consistency_violations)


def test_consistency_catches_score_mismatch(one_bundle):
    d = build_report(one_bundle).model_dump()
    d["verdict"]["composite_score"] = one_bundle.derived.composite_score + 25
    res = validate(d, one_bundle)
    assert not res.ok


def test_consistency_catches_missing_verify_list(one_bundle):
    d = build_report(one_bundle).model_dump()
    d["to_be_verified"] = []
    res = validate(d, one_bundle)
    assert not res.ok
    assert any("to_be_verified" in v for v in res.consistency_violations)
