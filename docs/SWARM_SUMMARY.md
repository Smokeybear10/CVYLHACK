# Swarm — what we built (summary)

A record of the Stage 2 survey swarm work (our lane). Design is in [SWARM.md](SWARM.md), the
line-by-line how-it-works is in [SWARM_INTERNALS.md](SWARM_INTERNALS.md). This is the short "what
exists and why" so the team can catch up fast.

## What it is

The AI surveyor layer of Sonder. It takes the finalist curb segments (from Saim's Stage 1), their
measurements (from Max's CV + SDK), and the user's priorities, and returns a Go / Conditional /
No-go verdict per site with reasons. It is the truck-roll replacement and the reason Sonder uses
agents at all.

## Shape of the build

- **Breadth swarm**: one surveyor agent per finalist, run in waves, streamed as they finish so the
  map fills live. Each agent gets a shared system prompt + that site's data + its street photo.
- **Winner deep-dive**: the top 1-3 get a specialist crew (fit / connection / context) fused by a
  judge into a richer verdict.
- **The agent's real value**: it looks at the photo and catches what the numbers miss (bus stop,
  loading zone, driveway, construction, hydrant in the frontage) and downgrades accordingly.

## What is in the repo (`swarm/`)

| File | Role |
|---|---|
| `schema.py` | contracts: `SiteInput` (Saim), `Measurements` (Max), `UserPriorities` (UI), `Verdict` (out) |
| `prompts.py` | surveyor system prompt + per-site builder; specialist crew + judge |
| `providers.py` | Anthropic call + deterministic mock fallback |
| `orchestrator.py` | wave runner, winner crew, disk cache (mock/real kept separate) |
| `config.py` | `.env` loading, model tiers, cost knobs |
| `service.py` | FastAPI: `/health`, `/survey`, `/survey/stream` (SSE) |
| `mock_data.py` | stub finalists + measurements (stand in for Saim + Max) |
| `run_demo.py` | CLI end-to-end entry point |

Docs: `docs/SWARM.md`, `docs/SWARM_INTERNALS.md`, `swarm/README.md`.

## How it runs

- CLI: `python -m swarm.run_demo` (mock, free) / `--limit N` (frugal real).
- Service: `uvicorn swarm.service:app --port 8000`. The frontend calls `POST /survey/stream` and
  drops a pin per `verdict` event, opens the report on the `winner` event.
- Runs today with **no key and no CV** via `mock_data` fallback, so all four lanes build in parallel.

## Decisions made

- Breadth + winner deep-dive (not full crew per site): best demo, cost-bounded.
- Frugal models: breadth on Haiku, crew on Sonnet. Cache so reruns are free. The $200 lasts.
- Strict JSON, low temperature, cached verdicts → reproducible across rehearsals.
- The agent judges provided facts and never invents numbers. Out-of-scan items become
  "verify on site" flags. Mock verdicts are never shown in the real demo (rubric: fake data = 0).

## Status

- Built and verified end to end in mock mode (health, full survey, SSE stream all correct).
- Pending (swaps, not blockers): a valid `ANTHROPIC_API_KEY`; an adapter from Saim's Stage 1
  output to `SiteInput`; an adapter from Max's measurements to `Measurements`; pointing the SSE
  stream at Thomas's frontend.
- All on the `swarm` branch.
