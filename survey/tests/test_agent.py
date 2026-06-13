"""The per-site agent: success, fallback on error, fallback on hallucination,
forced identity."""
from survey import deterministic
from survey.agent import survey_site
from survey.client import StubClient


class RaisingClient:
    name = "raise"

    def generate(self, b, s):
        raise RuntimeError("boom")


class HallucinatingClient:
    name = "hallu"

    def generate(self, b, s):
        d = deterministic.build_report(b).model_dump()
        d["connection"]["rom_cost_usd"] = 999999.0  # not in the allow-list
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


def test_hallucination_is_caught_and_dropped(one_bundle):
    out = survey_site(one_bundle, HallucinatingClient())
    assert out.used_fallback  # the bad output was rejected
    assert out.report.connection.rom_cost_usd != 999999.0  # invented number never ships
    assert out.validation.ok  # the fallback is grounded


def test_identity_is_forced_from_bundle(one_bundle):
    out = survey_site(one_bundle, WrongIdClient())
    assert out.report.site.id == one_bundle.site.id  # model cannot change identity
    assert not out.used_fallback
