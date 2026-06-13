"""Evaluation harness: prove the swarm is reliable with hard metrics.

Runs the survey over a golden set and measures schema validity, hallucination
(grounding violations), consistency, determinism, and tier agreement. This is the
difference between "the agents seem fine" and "the agents are measured reliable".
"""
from __future__ import annotations

import json
from pathlib import Path

from . import criteria
from .bundler import bundles_from_contract
from .orchestrator import run_survey

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_sites.json"


def load_contract(path=_FIXTURE) -> dict:
    return json.loads(Path(path).read_text())


def golden_expectations(bundles) -> dict[str, str]:
    """Expected tier per site = the canonical tier from screening score + gate.
    A site that screened as gated must come back No-go; a high scorer must not."""
    return {b.site.id: criteria.tier_from(b.derived.composite_score, b.derived.gated)
            for b in bundles}


def run_eval(client, runs: int = 2, contract: dict | None = None) -> dict:
    contract = contract or load_contract()
    bundles = bundles_from_contract(contract)
    expected = golden_expectations(bundles)
    n = len(bundles)

    runs_out = [run_survey(bundles, client, use_cache=False) for _ in range(max(1, runs))]
    first = runs_out[0]

    schema_ok = sum(1 for o in first if o.validation.schema_ok)
    grounding_violations = sum(len(o.validation.grounding_violations) for o in first)
    consistency_violations = sum(len(o.validation.consistency_violations) for o in first)
    fallbacks = sum(1 for o in first if o.used_fallback)
    tier_ok = sum(1 for o in first if o.report.verdict.tier == expected.get(o.report.site.id))

    # determinism: every run must produce identical report payloads
    deterministic = True
    base = [o.report.model_dump() for o in first]
    for other in runs_out[1:]:
        if [o.report.model_dump() for o in other] != base:
            deterministic = False
            break

    return {
        "n_sites": n,
        "client": client.name,
        "schema_valid_rate": round(schema_ok / n, 3) if n else 1.0,
        "grounding_violations": grounding_violations,
        "hallucination_rate": round(grounding_violations / n, 3) if n else 0.0,
        "consistency_violations": consistency_violations,
        "fallback_count": fallbacks,
        "tier_agreement": round(tier_ok / n, 3) if n else 1.0,
        "determinism": deterministic,
        "runs": len(runs_out),
    }
