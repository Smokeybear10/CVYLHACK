"""Sonder Stage 2 survey swarm (fresh build, my methods).

Standalone backend: consumes the Stage 1 screening-output contract, sends one agent
per site, validates and grounds the output, and produces a structured report (and a
PDF). See DEVELOPMENT_PLAN.md and ../research/00-SYNTHESIS.md.

    from survey.bundler import bundles_from_contract
    from survey.client import StubClient        # or AnthropicClient (needs ANTHROPIC_API_KEY)
    from survey.orchestrator import run_survey
    from survey.pdf import build_pdf

    bundles = bundles_from_contract(contract)
    outcomes = run_survey(bundles, StubClient())
    build_pdf([o.report for o in outcomes], "out/report.pdf")
"""
from .env import load_dotenv

load_dotenv()  # pick up ANTHROPIC_API_KEY / SURVEY_MODEL from a .env before anything reads them

from .agent import SurveyOutcome, survey_site
from .bundler import bundles_from_contract, bundle_from_feature
from .client import AnthropicClient, StubClient, have_key
from .orchestrator import reports_only, run_survey
from .pdf import build_pdf
from .schema import SiteBundle, SiteReport
from .validators import validate

__all__ = [
    "bundles_from_contract", "bundle_from_feature", "StubClient", "AnthropicClient",
    "have_key", "run_survey", "reports_only", "survey_site", "SurveyOutcome",
    "validate", "build_pdf", "SiteBundle", "SiteReport",
]
