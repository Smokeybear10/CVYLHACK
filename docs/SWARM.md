# Sonder Survey Swarm — our lane

Stage 2 of Sonder. We own the AI surveyor agents that turn a shortlist of candidate curb
segments into measured Go / Conditional / No-go verdicts. This is the truck-roll replacement
and the reason Sonder uses agents at all.

See [PLAN.md](../PLAN.md) §5.3 for where this sits. This doc is the contract + design for our part.

## What we own vs what we consume

```
Saim (Stage 1 screen)  --finalists-->  [ SWARM (us) ]  --verdicts-->  Thomas (frontend)
Max  (CV + measurement) --measurements-->     ^
User priorities (UI) -------------------------/
```

- We do NOT screen, score, measure, or render. We judge.
- We consume finalists (Saim) + measurements/evidence (Max) + user priorities (UI).
- We emit a stream of structured verdicts (Thomas renders them on the map + report).
- We build against **mocks** for Saim's and Max's outputs so all four of us work in parallel.

## Design: breadth swarm + winner deep-dive

1. **Breadth pass.** One surveyor agent per finalist (~12-15 live, scales to ~25). Run in waves
   of ~6 so the map fills progressively and we stay under rate limits. Each agent gets the same
   system prompt and its own data-filled user prompt + that site's street photo. Output: one
   structured verdict per site.
2. **Winner deep-dive.** The top 1-3 by score get a specialist crew: a **Fit** agent, a
   **Connection** agent, a **Context/vision** agent, and a **Judge** that fuses them into a
   richer verdict + report narrative. Cost-bounded because it is only 1-3 sites.

Why agents and not a script: the breadth agent's job is to look at the **photo** and catch what
the numbers cannot — bus stop, loading zone, driveway curb cut, construction, a hydrant in the
frontage — and downgrade a numerically-passing site. That override is the demo's money moment.

## Hard rules baked into every prompt

- Judge the provided facts. **Never invent a number.** Measurements come from Max.
- Always cite the specific values behind the verdict.
- Use the photo to catch photo-only disqualifiers the numbers miss.
- Output strict JSON only, matching the schema. No prose outside JSON.
- Anything uncertain or out of scan scope (grid capacity, permits, lot interiors, behind a
  fence) goes in `verify_on_site`, never faked.
- Low temperature. Demo verdicts are cached so rehearsals are reproducible.

## Verdict schema (our output to Thomas)

```json
{
  "site_id": "seg_00123",
  "verdict": "conditional",            // go | conditional | no_go
  "confidence": 0.78,                  // 0-1
  "one_line_reason": "Fits an L2 stall and power is close, but a bus stop occupies the frontage.",
  "rationale": "Measured usable frontage 6.4 m clears the 5.5 m an L2 curbside stall needs; nearest power pole 11 m. The street photo shows an MBTA bus stop sign and shelter on the same frontage, which would conflict with a charging stall.",
  "positives": ["6.4 m usable frontage", "power pole 11 m", "PCI 78 (Satisfactory)"],
  "concerns": ["bus stop on frontage (photo)", "AADT proxy only"],
  "verify_on_site": ["grid capacity at pole", "curbside permit / bus-stop conflict", "final survey"],
  "evidence_image_url": "https://.../seg_00123_masked.jpg",
  "sub_scores": {"fit": 0.8, "power": 0.9, "traffic": 0.6, "pavement": 0.75},
  "source": "swarm.breadth"           // or swarm.crew.judge
}
```

Crew verdicts add a `crew` block with each specialist's finding:
```json
"crew": {
  "fit":        {"finding": "...", "values": {...}},
  "connection": {"finding": "...", "values": {...}},
  "context":    {"finding": "...", "saw": ["bus stop", "fire hydrant"]}
}
```

## Input contracts (what we expect)

### SiteInput — from Saim's Stage 1 (one per finalist)
`site_id`, `address`, `lon`, `lat`, `score` (0-1), `score_breakdown` (dict),
`pavement_label`, `pavement_score`, `road_class`, `aadt`, `power_distance_m`,
`ada_ramp_dist_m`, `sidewalk_condition`, `obstruction_count`, `marking_flags`
(`fire_lane`/`no_parking`/`bus_stop`/...), `road_width_proxy_ft`.

### Measurements — from Max's CV/SDK (one per finalist)
`usable_frontage_ft`, `distance_to_power_m` (measured), `obstruction_positions` (list),
`ada_clearance_ft`, `evidence_image_url` (SAM3 masks drawn), `street_photo_url` (raw, for the
agent's vision), `measure_confidence`.

### UserPriorities — from the UI (one per run)
`station_size` (default curbside L2 → `required_frontage_ft`), `weights`
(`power`/`traffic`/`fit`, the live sliders).

Until Saim and Max land these, `swarm/mock_data.py` produces realistic stand-ins so we run end
to end today.

## Files

- `swarm/schema.py` — the dataclasses + JSON schema above.
- `swarm/prompts.py` — system prompts + per-site and per-specialist prompt builders.
- `swarm/providers.py` — the LLM call (Anthropic) with a deterministic mock fallback for no-key dev.
- `swarm/orchestrator.py` — wave runner (breadth) + winner crew, streams verdicts.
- `swarm/mock_data.py` — stub finalists + measurements (stand in for Saim + Max).
- `swarm/run_demo.py` — CLI: run the mock swarm, print verdicts.

## Cost / latency budget

Breadth: tokens only on the shortlist, ~10-30c per agent. 15 sites is a few dollars; the $200
lasts. Crew adds ~3-4 calls for 1-3 winners. Waves of 6. ~25 finalists take 1-2 min; for the
live show run 12-15 and say it scales. Cache during the build so we are not re-paying.

## Integration checklist (do these the moment Saim/Max have output)

- [ ] Swap `mock_data.finalists()` for Saim's Stage 1 result objects (map fields to SiteInput).
- [ ] Swap `mock_data.measurements()` for Max's per-site measurement dicts.
- [ ] Confirm `evidence_image_url` and `street_photo_url` resolve (the agent needs the photo).
- [ ] Point the verdict stream at Thomas's survey endpoint / SSE channel.
- [ ] Set `ANTHROPIC_API_KEY` (kickoff) so providers use the real model instead of the mock.
