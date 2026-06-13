"""Shared fixtures for the survey test suite. Uses the real screening-output
fixture so tests run against real Somerville data."""
import pytest

from survey import evals
from survey.bundler import bundles_from_contract
from survey.client import StubClient


@pytest.fixture
def contract():
    return evals.load_contract()


@pytest.fixture
def bundles(contract):
    return bundles_from_contract(contract)


@pytest.fixture
def one_bundle(bundles):
    return bundles[0]


@pytest.fixture
def gated_bundle(bundles):
    g = [b for b in bundles if b.derived.gated]
    assert g, "fixture should include at least one gated site"
    return g[0]


@pytest.fixture
def stub():
    return StubClient()
