# Swarm Internals — how the survey swarm actually works

Granular reference for `swarm/` (Sonder Stage 2). Pairs with [SWARM.md](SWARM.md) (the design +
contracts). This doc is the line-by-line "what runs when" so anyone on the team can pick it up.

Read order: SWARM.md for the why and the contracts, this for the how.

---

## 1. Where it sits

```
Saim Stage 1 screen ──finalists──┐
Max CV + SDK measure ──measure──► [ swarm/ ]  ──Verdict stream──► Thomas frontend
UI sliders ──priorities──────────┘
```

The swarm is pure judgment. It does not screen, measure, render, or query Cyvl. It takes
pre-fetched facts + a street photo and returns a structured verdict per site. That isolation is
what lets all four lanes build in parallel.

---

## 2. End-to-end execution flow

`python -m swarm.run_demo [--limit N]` runs this:

```
run_demo.main()
  │  load finalists (mock_data.finalists)        -> list[SiteInput]
  │  load measurements (mock_data.measurements)  -> dict[site_id -> Measurements]
  │  load priorities (mock_data.priorities)      -> UserPriorities
  │
  ├─ run_breadth(sites, meas, prefs, wave_size)            # orchestrator.py
  │     for each wave of <=wave_size finalists:
  │        for each site in wave:
  │           key = _cache_key(site, prefs)                # site + station + weights + mode
  │           if cached: yield cached Verdict              # free, reproducible
  │           else: submit surveyor_verdict(site, meas, prefs) to a thread pool
  │        as each future completes:
  │           cache it, yield Verdict
  │     (verdicts stream out as agents finish -> map fills live)
  │
  ├─ pick_winners(verdicts, sites, n=CREW_WINNERS)         # rank: go > conditional > no_go,
  │                                                        # then Stage 1 score, then confidence
  │
  └─ run_crew(winner_site, meas, prefs)                    # the deep-dive
        for role in (fit, connection, context):
           specialist call -> {finding, values|saw}
        judge call(facts + specialist findings + photo) -> full Verdict + crew{}
```

A single breadth agent's path:

```
surveyor_verdict(site, meas, prefs)                        # providers.py
  if ANTHROPIC_API_KEY present:
     msgs = build_surveyor_messages(site, meas, prefs)     # prompts.py
     text = _call_model(SURVEYOR_SYSTEM, msgs, BREADTH_MODEL)
     data = _parse_json(text)
     source = "swarm.breadth"
  else:
     data = _mock_verdict(site, meas, prefs)               # deterministic gates
     source = "swarm.breadth.mock"
  return Verdict(site_id, evidence_image_url, source, **data)
```

---

## 3. Module reference

### `schema.py` — the contracts
Dataclasses, no logic. Single source of truth for field names.

| Type | Produced by | Key fields |
|---|---|---|
| `SiteInput` | Saim (Stage 1) | `site_id, address, lon, lat, score, score_breakdown, pavement_label, pavement_score, road_class, aadt, power_distance_m, ada_ramp_dist_m, sidewalk_condition, obstruction_count, marking_flags, road_width_proxy_ft` |
| `Measurements` | Max (CV+SDK) | `site_id, usable_frontage_ft, distance_to_power_m, obstruction_positions, ada_clearance_ft, evidence_image_url, street_photo_url, measure_confidence` |
| `UserPriorities` | UI | `station_size, required_frontage_ft, weights{power,traffic,fit}` |
| `Verdict` | us (out) | `site_id, verdict, confidence, one_line_reason, rationale, positives[], concerns[], verify_on_site[], evidence_image_url, sub_scores, source, crew?` |

`VERDICT_JSON_SCHEMA` is the JSON contract embedded in the prompts and used to validate model
output. `Verdict.to_dict()` serializes for the frontend.

### `config.py` — env + models + cost knobs
- `load_env()` runs on import: reads repo-root `.env`, sets vars with `setdefault` (never
  overwrites an already-exported var). No dependency.
- Models (override in `.env`): `BREADTH_MODEL` (default `claude-haiku-4-5`, high volume),
  `CREW_MODEL` (default `claude-sonnet-4-5`, only 1-3 sites).
- Cost knobs: `WAVE_SIZE` (6), `MAX_BREADTH_SITES` (0 = no cap), `CREW_WINNERS` (1).

### `prompts.py` — the product
- `SURVEYOR_SYSTEM`: role, scope (curbside L2), verdict definitions, the hard rules (judge facts,
  never invent numbers, cite values, use the photo to catch what numbers miss, flag out-of-scope),
  and the JSON schema. The photo-override instruction is what justifies using agents.
- `_facts_block(site, meas, prefs)`: renders the compact, unambiguous fact sheet (below).
- `build_surveyor_messages(...)`: returns the user turn = `[text fact-sheet, image_ref(photo),
  "Return the verdict JSON now."]`.
- `CREW_SPECIALISTS`: three system prompts (fit / connection / context) each returning a small JSON.
- `JUDGE_SYSTEM`: fuses the three findings + facts into the full verdict with a `crew` block.

The fact block format (exact):
```
SITE <id> — <address>  (<lat>, <lon>)
Chosen station: <station>  (needs >= <required_frontage_ft> ft usable frontage)
User priority weights: {...}

MEASURED FROM THE SCAN (do not change these):
- usable frontage: <ft>   (required: <ft>)
- distance to nearest power: <m>
- ADA clearance: <ft|not measured>
- obstructions in frontage: <type @ offset_ft; ...|none detected>
- measurement confidence: <0-1>

DETERMINISTIC FACTS (Stage 1):
- pavement: <label> (PCI <score>)
- road class: <class>   traffic AADT: <n|unknown (road-class proxy only)>
- road width (proxy): <ft>
- nearest ADA ramp: <m|n/a>   sidewalk: <cond|n/a>
- marking flags: <comma list|none>
- Stage 1 score: <0-1>  breakdown: {...}

The street photo is attached. Use it to catch photo-only disqualifiers the numbers miss.
```

### `providers.py` — model call + mock
- `have_key()`: `bool(ANTHROPIC_API_KEY)`. Decides real vs mock everywhere.
- `_to_anthropic_content(content)`: turns our `{type:text}` / `{type:image_ref,url}` blocks into
  Anthropic blocks (`image` with `source:{type:url}`). The model sees the actual street photo.
- `_call_model(system, messages, model=None, temperature=0.1, max_tokens=1024)`: lazy-imports
  `anthropic`, calls Messages API, returns concatenated text. `model` defaults to `BREADTH_MODEL`.
- `_parse_json(text)`: strips ```` ```json ```` fences, slices the first `{` to last `}`, loads.
- `_mock_verdict(site, meas, prefs)`: the deterministic gate logic (section 4).
- `surveyor_verdict(...)`: public entry; real or mock; always returns a `Verdict`.

### `orchestrator.py` — waves, winner crew, cache
- `_cache_key(site, prefs)`: sha1 of `[site_id, station_size, weights, mode]` where mode is the
  breadth model id (real) or `"mock"` — so mock and real verdicts never collide.
- `_cache_get/_cache_put`: JSON files under `.swarm_cache/` (gitignored).
- `run_breadth(sites, measurements, prefs, wave_size=6, use_cache=True)`: generator. Processes in
  waves via `ThreadPoolExecutor(max_workers=wave_size)`, yields `Verdict`s as they complete.
  Cache hits yield immediately without a call.
- `pick_winners(verdicts, sites, n=3)`: sort by `(verdict_rank, -stage1_score, -confidence)`,
  return top n `site_id`s. `verdict_rank`: go=0, conditional=1, no_go=2.
- `run_crew(site, meas, prefs)`: real path = 3 specialist calls + 1 judge call (all `CREW_MODEL`);
  mock path = synthesize crew findings from the inputs and reuse the breadth mock verdict. Returns
  a `Verdict` with `source="swarm.crew.judge"` and a populated `crew` dict.

### `mock_data.py` — stand-ins for Saim + Max
Six Somerville finalists spanning every outcome: a clean go, two conditionals (bus stop /
hydrant), a too-narrow no-go (11 ft < 18 ft), a far-power no-go (41 m), a failed-pavement no-go
(PCI 18). Photo URLs are real Cyvl CDN frames so the real path has an image to look at.

### `run_demo.py` — CLI entry point
Loads mocks, runs breadth (clean message on auth failure), picks the winner, runs the crew, prints
verdicts + crew findings. `--limit N` caps finalists for frugal real-mode testing.

### `service.py` — HTTP surface (what the frontend calls)
FastAPI app, CORS open for dev. `SurveyRequest` (all fields optional; omit `finalists`/
`measurements` to use mocks) maps to our dataclasses via `_build()`, ignoring unknown keys so
field drift in the other lanes does not break us.
- `GET /health` → mode + model ids.
- `POST /survey` → full run, `{verdicts[], winners[], crew[]}`.
- `POST /survey/stream` → `text/event-stream`: a `verdict` event per finalist as agents finish,
  then a `winner` event per deep-dived winner, then `done`. This is what fills the map live.
Run: `uvicorn swarm.service:app --port 8000`.

---

## 4. The mock gate logic (deterministic, no LLM)

Used when there is no key, for dev and the demo safety net. Order matters; later gates override.

| Check | Effect |
|---|---|
| `usable_frontage_ft < required_frontage_ft` | `no_go` (does not fit) |
| `pavement_score < 25` | `no_go` (failed/serious pavement) |
| `pavement_score >= 56` | adds a positive |
| `distance_to_power_m > 30` | `no_go` (power too far) |
| any obstruction in frontage, or `bus_stop/loading_zone/fire_lane/no_parking` flag | downgrade a `go` to `conditional` |

`confidence = 0.55 + 0.4 * measure_confidence`. `verify_on_site` always includes final survey,
grid capacity, and curbside/parking permit. The mock mirrors what the real agent should conclude,
so the pipeline and UI look right before the model is wired in. **Mock verdicts are never shown in
the real demo** (PLAN.md §5.4 — fake data scores 0).

---

## 5. Caching

- Location: `.swarm_cache/<sha1>.json`, one file per verdict. Gitignored.
- Key: `site_id + station_size + weights + mode`. Changing the sliders, the station, or the model
  produces a fresh verdict; re-running the same config is free and identical.
- Purpose: reproducible rehearsals and the demo fallback. Delete `.swarm_cache/` to force fresh.
- Crew verdicts are not cached yet (only 1-3 per run); add it if rehearsals get expensive.

---

## 6. Cost model

- Breadth: 1 call per finalist on `BREADTH_MODEL` (haiku by default). ~hundreds of input tokens
  (fact sheet) + 1 image + short JSON out. Cheap; this is why breadth uses haiku.
- Crew: `3 specialists + 1 judge = 4` calls per winner on `CREW_MODEL` (sonnet), times
  `CREW_WINNERS`.
- A 15-finalist run + 1 deep-dive ≈ 15 haiku + 4 sonnet calls. A few dollars at most; the $200
  lasts many rehearsals because the cache means you pay once per (config, site).
- Frugality levers: `--limit`, `SWARM_MAX_BREADTH`, `CREW_WINNERS`, cheaper `BREADTH_MODEL`, and
  the cache.

---

## 7. Failure modes

| Symptom | Cause | Handling |
|---|---|---|
| `401 invalid x-api-key` | bad/expired key, or homoglyph corruption from an RTF copy | `run_demo` prints a clean message and stops; fix the key in `.env` |
| breadth shows mock while mode says REAL | stale cache from a prior mock run | fixed: cache key includes mode; or `rm -rf .swarm_cache` |
| model returns non-JSON | low-quality model / prompt drift | `_parse_json` salvages the `{...}` slice; tighten the prompt or raise `max_tokens` |
| image URL 404 | CDN frame moved | swap `street_photo_url`; the agent still has the numbers |
| non-deterministic verdicts across rehearsals | temperature / model variance | temp is 0.1; cache the demo verdicts; the gates make mock fully deterministic |

---

## 8. Integration steps (when Saim / Max land)

1. Write an adapter mapping Saim's Stage 1 objects to `SiteInput` (match field names in §3).
2. Write an adapter mapping Max's per-site output to `Measurements`; ensure `street_photo_url`
   and `evidence_image_url` resolve.
3. Replace `mock_data.finalists()` / `measurements()` with those adapters.
4. Stream `run_breadth(...)` verdicts to Thomas's survey endpoint (each `Verdict.to_dict()`).
5. Put the real `ANTHROPIC_API_KEY` in `.env`; confirm with `python -m swarm.run_demo --limit 1`.
6. Tune `SURVEYOR_SYSTEM` against real photos; keep the JSON schema stable so the frontend does
   not break.

---

## 9. Extension ideas (not built yet)

- Self-consistency: run a site twice, mark low confidence on disagreement.
- A follow-up "why was this rejected?" agent reusing the site payload (the demo chat beat).
- Streaming verdicts over SSE/websocket instead of a generator, for the live map.
- Per-criterion tool calls (let the context agent request a zoom/crop) if perception allows.
