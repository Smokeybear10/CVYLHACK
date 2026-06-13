# swarm/ — Sonder Stage 2 survey swarm

Our lane. Turns finalist curb segments into measured Go / Conditional / No-go verdicts with AI
surveyor agents. Full design + contracts in [../docs/SWARM.md](../docs/SWARM.md).

## Run it (mock mode, no key, no CV)

```bash
python -m swarm.run_demo
```

Prints a breadth verdict per finalist, then a deep-dive on the winner. Works today against
`mock_data.py` (stand-ins for Saim's screen and Max's measurements).

## Run it for real

```bash
export ANTHROPIC_API_KEY=...        # team key, kickoff
export ANTHROPIC_MODEL=claude-sonnet-4-5   # optional
python -m swarm.run_demo
```

## Files

| File | Role |
|---|---|
| `schema.py` | data contracts: `SiteInput` (Saim), `Measurements` (Max), `UserPriorities` (UI), `Verdict` (out) |
| `prompts.py` | surveyor system prompt + per-site builder; specialist crew + judge prompts |
| `providers.py` | Anthropic call + deterministic mock fallback |
| `orchestrator.py` | wave runner (breadth) + winner crew + disk cache |
| `mock_data.py` | stub finalists + measurements |
| `run_demo.py` | end-to-end entry point |

## Wiring into the rest of Sonder

- Replace `mock_data.finalists()` with Saim's Stage 1 output (map to `SiteInput`).
- Replace `mock_data.measurements()` with Max's per-site measurements (map to `Measurements`).
- Stream `run_breadth(...)` verdicts to Thomas's survey endpoint; they arrive as agents finish.
- Verdicts are cached in `.swarm_cache/` keyed by site + station + weights, so rehearsals are free
  and reproducible. Delete the folder to force fresh runs.

Mock mode is for development and the demo fallback only. The verdicts we actually show must come
from the real agents on real measurements (PLAN.md §5.4).
