"""The orchestrator: runs all sites, preserves order, caches deterministically,
and survives failing agents."""
from survey.orchestrator import run_survey


class RaisingClient:
    name = "raise"

    def generate(self, b, s):
        raise RuntimeError("boom")


def test_runs_all_and_preserves_order(bundles, stub):
    outs = run_survey(bundles, stub, use_cache=False)
    assert len(outs) == len(bundles)
    assert [o.report.site.id for o in outs] == [b.site.id for b in bundles]
    assert all(o.validation.ok for o in outs)


def test_cache_is_deterministic_and_written(bundles, stub, tmp_path):
    a = run_survey(bundles, stub, use_cache=True, cache_dir=tmp_path)
    assert list(tmp_path.glob("*.json")), "cache files should be written"
    b = run_survey(bundles, stub, use_cache=True, cache_dir=tmp_path)
    assert [o.report.model_dump() for o in a] == [o.report.model_dump() for o in b]


def test_swarm_survives_failing_agents(bundles):
    outs = run_survey(bundles, RaisingClient(), use_cache=False)
    assert len(outs) == len(bundles)              # one bad agent never sinks the swarm
    assert all(o.used_fallback for o in outs)
    assert all(o.validation.ok for o in outs)      # fallbacks are still valid + grounded


def test_small_wave_size_still_complete(bundles, stub):
    outs = run_survey(bundles, stub, wave_size=2, use_cache=False)
    assert len(outs) == len(bundles)
