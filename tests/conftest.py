"""Test config: force mock mode (never call the Anthropic API) and isolate the cache.

Every test runs free and deterministic. The Claude API key is explicitly disabled here.
"""
import pytest

from swarm import providers, orchestrator


@pytest.fixture(autouse=True)
def force_mock(monkeypatch, tmp_path):
    # never use a real key during tests, even if .env set one on import
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(providers, "have_key", lambda: False)
    # isolate the disk cache per test
    monkeypatch.setattr(orchestrator, "CACHE_DIR", tmp_path / "swarm_cache")
    yield
