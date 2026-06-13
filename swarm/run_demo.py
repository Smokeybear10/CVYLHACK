"""Run the survey swarm end to end on mock data.

    python -m swarm.run_demo

With no ANTHROPIC_API_KEY this uses the deterministic mock (good for wiring + the demo safety
net). Set ANTHROPIC_API_KEY (and optionally ANTHROPIC_MODEL) to run the real agents.
"""
from __future__ import annotations

import argparse

from . import mock_data, providers, config
from .orchestrator import run_breadth, run_crew, pick_winners

ICON = {"go": "[GO ]", "conditional": "[CND]", "no_go": "[NO ]"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="cap finalists (frugal real-mode testing; 0 = all)")
    args = ap.parse_args()

    sites = mock_data.finalists()
    if args.limit:
        sites = sites[: args.limit]
    meas = mock_data.measurements()
    prefs = mock_data.priorities()

    if providers.have_key():
        mode = f"REAL — breadth={config.BREADTH_MODEL} crew={config.CREW_MODEL}"
    else:
        mode = "MOCK (no key)"
    print(f"Sonder survey swarm — {mode} — {len(sites)} finalists\n")

    print("== breadth pass ==")
    verdicts = []
    try:
        for v in run_breadth(sites, meas, prefs, wave_size=6):
            verdicts.append(v)
            print(f" {ICON[v.verdict]} {v.site_id}  conf={v.confidence:.2f}  {v.one_line_reason}")
    except Exception as e:
        msg = str(e)
        if "x-api-key" in msg or "authentication" in msg.lower():
            print("\n  ANTHROPIC AUTH FAILED — check ANTHROPIC_API_KEY in .env (401 invalid x-api-key).")
            print("  Unset it to run the free mock pipeline instead.")
            return
        raise

    winners = pick_winners(verdicts, sites, n=1)
    print(f"\n== winner deep-dive: {winners[0]} ==")
    site = next(s for s in sites if s.site_id == winners[0])
    cv = run_crew(site, meas[site.site_id], prefs)
    print(f" {ICON[cv.verdict]} {cv.site_id}  conf={cv.confidence:.2f}")
    print(f"   reason: {cv.one_line_reason}")
    print(f"   rationale: {cv.rationale}")
    if cv.crew:
        for role, f in cv.crew.items():
            print(f"   - {role}: {f.get('finding') or f.get('saw')}")
    print(f"   verify on site: {', '.join(cv.verify_on_site)}")


if __name__ == "__main__":
    main()
