"""Schema models validate and round-trip."""
import pytest
from pydantic import ValidationError

from survey.deterministic import build_report
from survey.schema import SiteReport


def test_report_builds_and_round_trips(one_bundle):
    rep = build_report(one_bundle)
    dumped = rep.model_dump()
    again = SiteReport.model_validate(dumped)
    assert again.model_dump() == dumped


def test_required_sections_present(one_bundle):
    rep = build_report(one_bundle)
    assert rep.verdict.tier in {"Tier 1", "Tier 2", "Tier 3", "No-go"}
    assert rep.scorecard and rep.physical_fit and rep.connection
    assert rep.to_be_verified  # unknowns always deferred


def test_invalid_tier_rejected(one_bundle):
    d = build_report(one_bundle).model_dump()
    d["verdict"]["tier"] = "Excellent"  # not a valid Tier literal
    with pytest.raises(ValidationError):
        SiteReport.model_validate(d)


def test_invalid_rating_rejected(one_bundle):
    d = build_report(one_bundle).model_dump()
    if d["scorecard"]:
        d["scorecard"][0]["rating"] = "MAYBE"
        with pytest.raises(ValidationError):
            SiteReport.model_validate(d)
