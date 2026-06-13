"""The per-site agent: success, fallback on error, hallucination handling, identity.

With grafting, the model only contributes prose: numbers always come from the
bundle. So a structured hallucination is discarded; only an invented number in
prose can force a fallback."""
from survey import deterministic
from survey.agent import survey_site
from survey.client import StubClient


class RaisingClient:
    name = "raise"

    def generate(self, b, s):
        raise RuntimeError("boom")


class StructHallucinatingClient:
    name = "structhallu"

    def generate(self, b, s):
        d = deterministic.build_report(b).model_dump()
        d["connection"]["rom_cost_usd"] = 999999.0  # invented, in a numeric field
        return d


class ProseHallucinatingClient:
    name = "prosehallu"

    def generate(self, b, s):
        d = deterministic.build_report(b).model_dump()
        d["executive_summary"].append("Transformer has 480 kVA of spare capacity.")  # invented prose number
        return d


class WrongIdClient:
    name = "wrongid"

    def generate(self, b, s):
        d = deterministic.build_report(b).model_dump()
        d["site"]["id"] = "HACKED"
        return d


def test_stub_passes_without_fallback(one_bundle):
    out = survey_site(one_bundle, StubClient())
    assert out.validation.ok and not out.used_fallback
    assert out.report.generated_by == "stub"


def test_raising_client_falls_back(one_bundle):
    out = survey_site(one_bundle, RaisingClient())
    assert out.used_fallback and out.validation.ok
    assert out.report.generated_by == "fallback"
    assert out.error and "boom" in out.error


def test_structured_hallucination_is_discarded(one_bundle):
    # a numeric field is filled from the bundle, so the invented value never ships
    out = survey_site(one_bundle, StructHallucinatingClient())
    assert not out.used_fallback
    assert out.report.connection.rom_cost_usd != 999999.0
    assert out.validation.ok


def test_prose_hallucination_falls_back(one_bundle):
    out = survey_site(one_bundle, ProseHallucinatingClient())
    assert out.used_fallback  # invented number in prose is caught
    assert all("480" not in s for s in out.report.executive_summary)  # never shipped


def test_identity_is_forced_from_bundle(one_bundle):
    out = survey_site(one_bundle, WrongIdClient())
    assert out.report.site.id == one_bundle.site.id
    assert not out.used_fallback
