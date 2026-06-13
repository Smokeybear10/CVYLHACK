"""Run the survey swarm end to end and generate the PDF.

    python -m survey.run_demo                 # stub (no key), all fixture sites, writes PDF
    python -m survey.run_demo --pdf out.pdf   # choose output path
    python -m survey.run_demo --limit 3       # cap sites

With ANTHROPIC_API_KEY set it uses the real agent; otherwise the deterministic stub
(also the demo fallback). Either way the output is validated and grounded.
"""
from __future__ import annotations

import argparse

from . import evals
from .bundler import bundles_from_contract
from .client import AnthropicClient, StubClient, have_key
from .orchestrator import reports_only, run_survey
from .pdf import build_pdf

ICON = {"Tier 1": "[T1]", "Tier 2": "[T2]", "Tier 3": "[T3]", "No-go": "[NO]"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="cap sites (0 = all)")
    ap.add_argument("--pdf", default="out/survey_report.pdf", help="PDF output path")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--model", default=None, help="override model (e.g. claude-haiku-4-5-20251001)")
    args = ap.parse_args()

    contract = evals.load_contract()
    bundles = bundles_from_contract(contract)
    if args.limit:
        bundles = bundles[: args.limit]

    if have_key():
        client = AnthropicClient(model=args.model) if args.model else AnthropicClient()
        mode = f"REAL (Anthropic, {client.model})"
    else:
        client = StubClient()
        mode = "STUB (no key)"
    print(f"Sonder survey swarm — {mode} — {len(bundles)} sites\n")

    outcomes = run_survey(bundles, client, use_cache=not args.no_cache)
    for o in outcomes:
        v = o.report.verdict
        tag = " (fallback)" if o.used_fallback else ""
        flags = "" if o.validation.ok else f"  !{len(o.validation.all_issues)} issues"
        print(f" {ICON.get(v.tier, '[? ]')} {o.report.site.id:9s} "
              f"score={v.composite_score:5.1f} {o.report.site.street or '':16s} "
              f"{v.one_line_reason}{tag}{flags}")

    path = build_pdf(reports_only(outcomes), args.pdf)
    print(f"\nPDF written: {path}")

    metrics = evals.run_eval(client, runs=2, contract=contract)
    print("\neval metrics:")
    for k, val in metrics.items():
        print(f"  {k}: {val}")


if __name__ == "__main__":
    main()
