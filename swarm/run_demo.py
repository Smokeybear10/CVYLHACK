"""Run the survey swarm end to end on mock data.

    python -m swarm.run_demo

With no ANTHROPIC_API_KEY this uses the deterministic mock (good for wiring + the demo safety
net). Set ANTHROPIC_API_KEY (and optionally ANTHROPIC_MODEL) to run the real agents.
"""
from __future__ import annotations

from . import mock_data, providers
from .orchestrator import run_breadth, run_crew, pick_winners

ICON = {"go": "[GO ]", "conditional": "[CND]", "no_go": "[NO ]"}


def main() -> None:
    sites = mock_data.finalists()
    meas = mock_data.measurements()
    prefs = mock_data.priorities()

    mode = "REAL (Anthropic)" if providers.have_key() else "MOCK (no key)"
    print(f"Sonder survey swarm — {mode} — {len(sites)} finalists\n")

    print("== breadth pass ==")
    verdicts = []
    for v in run_breadth(sites, meas, prefs, wave_size=6):
        verdicts.append(v)
        print(f" {ICON[v.verdict]} {v.site_id}  conf={v.confidence:.2f}  {v.one_line_reason}")

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
