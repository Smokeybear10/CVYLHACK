# Sonder - Build Plan

Screen fast. Build smart. Instant EV charger site screening from street-level 3D scans.
Cyvl Physical AI Hackathon, Somerville MA, build day 2026-06-13.

This describes what each layer does and how we build it. It is not code. For exact endpoints
and SDK calls, see docs/CYVL_API.md, docs/SPATIAL_SDK.md, docs/cyvl-mcp-reference.md. For the
scoring criteria see docs/JUDGING.md.

---

## 1. Product

To build one EV charger an operator screens roughly 50 candidate locations, and almost every
one historically needs a physical site visit to measure fit, ADA, distance to power, and what
you would trench through. That is about $5k and weeks per site, mostly spent on sites that get
rejected. Sonder moves that physical screen to a 60 second desktop query. You circle a region
of Somerville, set what matters (station size, traffic, power), and Sonder ranks every curb
segment, then sends a swarm of AI surveyor agents to the finalists. Each agent measures the
site from Cyvl's 3D scan, looks at the real street photo, and returns a Go, Conditional, or
No-go verdict with reasons. We do not replace the final survey. We kill the screening truck roll.

Pitch arc: hook (50 to 1), insight (the measurements already exist in the scan), product
(circle a region, get ranked measured verdicts), close (same engine, any scanned street).

---

## 2. Scope, locked

- Charger type: curbside / street-frontage L2 only for the MVP, and this is a deliberate fit,
  not a limitation. Cyvl's data IS the curb. The scan is street level, so the curb is the one
  place we can measure everything that matters (usable frontage, ADA ramp, obstruction
  clearance, distance to the nearest pole, pavement to cut) with zero assumptions. For curbside
  the nearest pole is the actual interconnection point, and dense Somerville has little
  off-street parking, so the street literally is the site. Off-street lots and forecourt DCFC
  are a Cyvl scan away, not a rebuild (see "Why Cyvl, not Google Maps" and section 13): the day
  Cyvl captures a parking lot, the same engine screens it.
- Region: the data covers all of Somerville. For the demo we circle a small, well scanned area
  (Davis Square or Union Square). We do not claim coverage we have not checked.
- What we measure: usable frontage, distance to power, ADA path, obstruction clearance,
  pavement condition, road width.
- What we never claim: off-street lot interiors, anything behind a building, true grid
  capacity, final permit approval. These get flagged "verify on site." That is credibility.
- Selection method: a gated, weighted score, not a trained ranker. There are no ground-truth
  labels for "good site," the criteria are known and explainable, and the filters become
  live-tunable weights.
- Zoning: not a hard screen filter. It is fed to the survey agent as an input so it shows up in
  the verdict and report at the end.
- CV: the custom/advanced model is simulated during early build and made real later. The CV
  actually shown in the demo must be real (see section 7 and the rubric note there).

---

## 3. How we win the rubric

Four criteria, 25 percent each, out of 16 (docs/JUDGING.md). Build decisions map to them:

- Business Strength. Buyers are charging networks (ChargePoint, EVgo, Electrify America),
  site-acquisition and EPC firms, property hosts, utilities, and cities. The screen they pay
  ~$5k for becomes a query. Pricing: per-report, monthly SaaS, or API. It is a startup you
  could start now. Same engine retargets to small-cell siting and outdoor ad placement later.
- Technical. Not a "Google Maps clone" (named as a 0). The defense is measurement: we produce
  real dimensions from the scan that no map can. It runs live, end to end, nothing hidden.
- Use of Cyvl + sponsor data. The "remove it and does it die" test: remove Cyvl and there is no
  measurement, no power distance, no verdict. The product dies. That is central, not decorated.
- Presentation. 5 minute pitch plus 2 for questions, twice (booth at 5:30, finals at 6:30). A
  clean, rehearsed, live demo on a real Somerville block.

---

## Why Cyvl, not Google Maps (the moat)

This is the answer to the "Google Maps clone" 0 and the "remove it and does it die" test, so we
say it out loud in the pitch.

A map gives you a flat top-down image and an address. It cannot tell you any of the things a
siting decision actually turns on:

- Usable curb width and how many 2.7 x 5.5 m stalls physically fit. A map has no dimension off
  the curb.
- Whether an ADA ramp and accessible path exist. Cyvl carries the ramp as a labeled asset with
  truncated-dome, type, and condition attributes.
- What obstructs the footprint (hydrant, tree, manhole, streetlight) and how far each one sits.
- Distance to the nearest real power asset (pole, luminaire), which is the curbside
  interconnection point and the top cost driver. A map shows none of these.
- The pavement you would cut and its condition, which sets the trench cost.

All of that requires a street-level 3D scan with labeled, located assets, which is exactly what
Cyvl is and a map is not. Remove Cyvl and Sonder has no measurement, no power distance, no
verdict. It is not a layer on top of Maps. It is the thing Maps cannot be, and it is curbside
precisely because the scan is the curb.

One line for the room: "Every other tool ranks demand on a map. None of them can tell you if a
charger fits, because they never see the site. We measure the site from Cyvl's scan."

---

## 4. Architecture

```
USER: circle a region on the Somerville map, set filters (size, traffic, power)
   |
STAGE 1  SCREEN  (deterministic, fast, no LLM cost)
   - candidates = pavement segments inside the region
   - enrich each with power distance, pavement, ADA, obstructions, road class
   - gated then weighted score -> heatmap + ranked list -> top ~25
   |
STAGE 2  SURVEY  (AI swarm, the truck-roll replacement)
   - per finalist: SAM3 segments the photo, lifted to 3D for real measurements
   - an agent reads measurements + public data + the photo + zoning -> verdict + why
   - verdicts fill the map live, finalists rank, top 1-3 are "build here"
   |
OUTPUT: verdict-first report, evidence photo with measured line, 3D viewer, CAD export
```

Component roles:

- Data, fast: Cyvl REST API for the app backend, Cyvl MCP for Claude Code during dev.
- Data, deep: cyvl-spatial-sdk for photo-to-3D measurement, LiDAR, and the browser 3D viewer.
- Public: MassDOT roads (traffic), DOE AFDC (existing chargers), Somerville open data (zoning).
- Compute: Python for candidate generation, scoring, and measurement orchestration.
- Agents: Claude via the Anthropic API ($200 credit) for the Stage 2 survey and verdict.
- Serve: a small API with a screen endpoint and a survey endpoint, plus a result cache.
- Show: the UI is yours to design and is intentionally left out of this plan.

---

## 5. The layers (what each does, and how)

### 5.1 Data layer

How we pull it:

- Backend uses the Cyvl REST API at https://i3.cyvl.app with the team bearer key
  (CYVL_API_KEY). The MCP server (added locally, OAuth) is for exploring during the build, not
  for the product runtime. Note: the repo docs call the MCP server `i3`; it is added locally as
  `cyvl`. Either works for dev.
- First call at kickoff: list projects with the team key to get the real project_id. The
  pre-kickoff project we verified is the "Somerville Marketing Demo"
  (f15b854a-d203-49c7-bc25-1350dd4a1cd6); the team key may expose a different or richer project.
- All list endpoints take the region (bbox or radius) as a spatial filter and paginate by
  cursor. We always page to the end before computing anything.
- Everything comes back as GeoJSON in WGS84. The SDK poses and LiDAR are UTM 19N. We keep one
  convention internally (lon/lat) and convert only at the moment we call SDK projection.

What the data gives us (verified live against the demo project):

- Pavement: about 5,180 scored segments with PCI, area, length, and street name. These double
  as our candidate units.
- Above-ground assets: utility poles (437), luminaires (790), traffic-signal poles (215), ADA
  ramps (748, with truncated-dome and type attributes), sidewalks, curbs, hydrants, trees,
  catch basins. Every asset carries a public evidence photo URL.
- Markings: crosswalks, stop bars, bike lanes, handicap, no-parking, fire-lane. Used to detect
  parking lanes and disqualifiers.
- Native filters worth using: functional_class (road hierarchy, a built-in traffic proxy that
  keeps Cyvl central) and surface_type (asphalt vs concrete, feeds trench-surface cost).
- Imagery semantic search: the demo project had zero embeddings, so MCP image search returned
  nothing. The REST embeddings endpoint exists, so re-check with the team project at kickoff.
  Do not depend on it; use per-asset photos and SDK frames for evidence.

Public sources we layer on:

- Traffic: MassGIS-MassDOT Roads is the best open source. It carries road functional class and
  AADT volume, is GIS-native, and is queryable by bbox. Primary signal. We cross-check with
  Cyvl's own functional_class to keep Cyvl central, and fall back to OpenStreetMap road class
  where AADT is missing.
- Existing chargers: DOE AFDC locator, free, for cluster/cannibalization context.
- Zoning: Somerville open data, used as a report input in Stage 2, not a screen gate.

### 5.2 Stage 1, the screening layer

What it does: turn a circled region into a ranked, color-coded set of candidate curb segments
in a couple of seconds, with no LLM cost.

How:

- Candidate units are the pavement segments inside the region. Each is roughly 30 ft and curb
  aligned, already carries geometry, PCI, area, and street name, so we get real candidates
  without arbitrary grid sampling. Caveat we state openly: their geometry follows the cartway
  centerline, so Stage 1 width is a coarse proxy; Stage 2 gets the true usable frontage.
- Enrichment per candidate, all deterministic from the REST API and public data: distance to
  the nearest power asset, pavement condition and derived road width, nearest ADA ramp and
  sidewalk condition, count of obstructions in the frontage, parking and fire-lane flags from
  markings, and road class plus AADT from MassDOT.
- Scoring is two steps. First, hard gates remove obvious No-gos: no power within range, frontage
  too small for the chosen station size, pavement failed. Then a weighted score over the
  survivors, where the filter sliders are the weights, and every score decomposes into its
  parts so the heatmap and report can explain it.
- Output: the region colored by score, a ranked list, and the top ~25 handed to Stage 2.

### 5.3 Stage 2, the survey swarm

What it does: send one AI surveyor agent to each finalist to measure it from the scan, look at
the photo, weigh the public data and zoning, and return a verdict with reasons. This is the
truck-roll replacement, and it is why we use agents at all.

How:

- Perception first (real CV). For each finalist we take the nearest posed photo, run SAM3 to
  segment the usable curb, obstructions, and the power asset, and lift those masks to 3D through
  the LiDAR to get real measurements: usable frontage in feet, obstruction positions, and
  distance to power. The masks drawn on the photo become the report's evidence image.
- Judgment second. The agent is given the measured numbers, the deterministic facts, the public
  data, the zoning status, the user's priorities, and the street photo itself. Its job is to
  judge, not to invent numbers: confirm or contextualize the measurements, use vision on the
  photo to catch what geometry missed (a bus stop, a loading zone, a driveway curb cut,
  construction), and output a verdict, a short rationale citing specific values, a confidence,
  and a list of "verify on site" flags including zoning.
- The agent reads pre-fetched data from its prompt rather than querying live, so the demo does
  not depend on a live API mid-run. We can allow a live query for effect with the cache as
  backup.
- Concurrency, latency, cost. Run the agents in waves of about six so the map fills in
  progressively and we stay under rate limits. About 25 finalists take one to two minutes; for
  the live show we run 12 to 15 (still a swarm, less risk) and say it scales. The screen costs
  no tokens; each agent is roughly 10 to 30 cents, so a demo run is a few dollars and the $200
  lasts. We cache results during the build so we are not re-paying, and the swarm size is a
  parameter.

### 5.4 CV / ML layer

Two different things, kept separate:

- Selection is the weighted score, not ML. No labels exist for "good site," and a trained ranker
  would look like the mock data the rubric scores 0.
- Perception is where CV belongs: turning pixels into measurements and features.

The reality ladder (cheapest-real to hardest):

- Real and cheap: two-pixel measurement through LiDAR depth. No model, no external key. This
  alone proves "measure from the scan."
- Real and easy: SAM3 segmentation via the SDK to get usable frontage and obstructions. Needs a
  free fal.ai key. This is the demo's CV.
- Advanced, simulate first: a custom model fine-tuned on Cyvl's labeled photos to detect the
  transformer or meter can on a pole (the one power-relevant thing the base layers do not
  label). This is the NVIDIA "trained on Cyvl data" piece. We stub its output behind a clean
  interface so the pipeline runs early, then train it for real if time allows.

Adversarial note, important: simulating is fine as build scaffolding, but the CV shown in the
demo must be real, because fake data scores 0 on a quarter of the total and "nothing hidden" is
a technical criterion. So keep at least the measurement and SAM3 real for the demo, and never
call the stubbed custom model "trained" unless we actually trained it. If it stays simulated,
present SAM3 as our CV and the custom detector as roadmap.

### 5.5 Report layer

What it does: present a verdict-first, comparative, measurement-led report, deliberately unlike
AskBoston.

Adversarial read of AskBoston (a sponsor tool the judges may know): it is a descriptive,
single-address civic info card (Cyvl road condition plus 311, crashes, sidewalks, streetlights).
We diverge on purpose. We answer "should I build here and which spot is best," not "what is the
state of this street." We are region-in, ranked-out, not address-in, card-out. We lead with
measurement, fit, and connection cost, which AskBoston does not have. We include a civic stat
only if it changes the EV verdict, not the whole kitchen sink. We borrow only the good parts:
instant any-location lookup, per-datum source citation, and an honest "estimates, verify on
site" disclaimer.

Report anatomy: a verdict chip with the one-line reason and rank in the region; physical fit
(measured frontage, stalls that fit, ADA pass/fail, a small layout sketch); connection
(distance to power, trench length, surface, cost band); the evidence photo with the SAM3 mask
and measured line; the agent's rationale and what it saw in the photo; selective context
(traffic, nearby chargers); the "verify on site" flags including zoning; and the embedded 3D
view. The starred items (fit, connection, evidence, 3D) are what no map tool can produce.

### 5.6 3D / measurement layer

We use the SDK's built-in browser viewer, which renders the point cloud through the photo's
exact calibrated camera. We do not build a Potree pipeline; the viewer ships. We pre-cache the
LiDAR and frames for the demo region so it loads instantly, and we export a colored point cloud
of the winning block for the Autodesk path.

### 5.7 Backend layer

A small service with two jobs and a cache. One endpoint takes the region and filters and returns
the Stage 1 ranked result and heatmap. One endpoint takes the finalists and runs the survey
swarm, streaming verdicts back as they finish. A disk cache keyed by region and filters holds
pre-warmed results as the demo safety net. The backend talks to Cyvl over REST with the bearer
key and runs the SDK measurement step; the API key lives in a gitignored .env, never committed.

---

## 6. Filters: which are feasible

- Station size: strongest, because it is measured. Size maps to a required frontage length, used
  as a gate and a weight, and Stage 2 measures the real frontage. This is our wedge, lead with it.
- Traffic: feasible. Real volume from MassDOT AADT where it exists, road hierarchy from Cyvl
  functional_class and MassDOT class everywhere, OSM as fallback. We say "proxy" where it is one.
- Power: feasible as proximity to scanned poles and luminaires, which for curbside is the real
  interconnection point. True grid capacity is utility-private and gets flagged, not faked.

Bonus filters, all real and from Cyvl, low effort: pavement condition, ADA, obstruction
clearance, and existing-charger proximity.

---

## 7. Sponsor tools (use two, woven in)

- NVIDIA: SAM3 perception in Stage 2 (a real model on real Cyvl imagery, load-bearing) plus, if
  time allows, the fine-tuned transformer/meter detector trained on Cyvl's labeled photos. That
  is the genuine "train on Cyvl data" check, and it sharpens the power distance.
- Autodesk: export the winner's point cloud to the Recap then Civil 3D path for a conceptual
  layout. The desktop pipeline will not run reliably live, so we pre-export one site as an
  artifact and present it as the path.

Two is the cap. Ask Boston is not needed for Somerville and we skip it.

---

## 8. The demo (5 minutes, twice)

Booth round at 5:30, finals on the big screen at 6:30, same 5 plus 2 format.

- Open with the 50-to-1 problem and the truck roll.
- Circle a region in Somerville and set filters.
- The heatmap washes over the region. "Screened the segments in seconds, from the scan."
- The swarm dispatches to the finalists; pins light up with verdicts live.
- Click the winner: measured frontage, distance to the pole, evidence photo with the mask and
  the measured line. "Real measurements, not a map guess."
- The vision moment: an agent flagged something in the photo the numbers missed, so Conditional.
  This single beat justifies the agents.
- Flip to the 3D viewer on the winner, then show the CAD export. "Same engine, any scanned street."

Rehearse three times. Keep the cached run ready as a fallback for every live step.

---

## 9. Timeline (build 9:30 to 5:30, eight hours)

- Setup first: uv plus a modern Python, SDK installed and loading the scene, team REST key
  working, fal.ai key set, demo region chosen, region data and LiDAR pre-cached.
- Hours 0 to 2: Stage 1 end to end, region to ranked heatmap.
- Hours 2 to 3: the SDK measurement path on one candidate, validated by eye.
- Hours 3 to 4: one agent end to end, data and photo in, structured verdict out, stable.
- Hours 4 to 5: scale the agent to the batched swarm, wired to the map.
- Hours 5 to 7: build your UI and wire it to the screen and survey endpoints.
- Hours 7 to 8: hardwire and cache the demo region, stub the custom CV, polish, rehearse.

Rule: get one region to one measured, surveyed candidate shown in the UI bulletproof by midday.
Everything after is multiplication.

---

## 10. Risks and mitigations

Data:
- Imagery search may be empty (demo project had no embeddings). Use per-asset photos and SDK
  frames; re-check the team project at kickoff.
- Signs cover only the south/southeast. Pick a demo region with coverage; do not rely on signs.
- No transformer asset type. Power is pole and luminaire proximity, plus SAM3 or the custom
  detector for the actual can.
- No parcel or lot geometry yet, so curbside scope only today. This is a Cyvl coverage gap, not
  an architecture limit: when Cyvl scans a parking lot or parcel, the same engine screens it.
  Frame off-street as roadmap, never fake it.
- Coordinate mismatch (WGS84 vs UTM 19N). Convert only at projection time.

Agents:
- Non-determinism across rehearsals. Low temperature, strict output schema, cache demo verdicts.
- Rate limits and latency with many agents. Run in waves, show 12 to 15 live, pre-cache the rest.
- Cost. Tokens only on the shortlist, cache during build, swarm size is a parameter, and the
  $200 only arrives at kickoff.
- Hallucinated numbers. The agent judges provided facts and never invents values.

CV and infra:
- Training from scratch is infeasible. Fine-tune a pretrained model; SAM3 is the workhorse.
- A stubbed model read as fake. Keep the demo CV real (measurement and SAM3); never call a stub
  trained.
- SDK install is slow on system Python 3.9 (we saw it build wheels for 20-plus minutes). Use uv
  with Python 3.11 or 3.12 for prebuilt wheels.
- LiDAR streaming latency. Pre-cache the demo region.

Demo and narrative:
- Live API or network failure. Cached fallback for every step.
- "Google Maps clone" or "agents bolted on." Lead with measurement and the vision moment.
- Idea collision. Lean on measured frontage and distance to power, which are hard to copy.
- Overclaim. We kill the screening truck roll, not the final survey.

---

## 11. Honesty lines (saying these raises the score)

- Real Cyvl scans of Somerville, no mock data on the demo path.
- Traffic is a road-class and AADT proxy; Cyvl has no live traffic volume.
- Power is proximity to scanned poles; true grid capacity is private and flagged.
- The scan is street level, so we screen street-visible curbside sites today; lot interiors are
  flagged, and they come into scope the moment Cyvl scans the lot, same engine.
- It is a snapshot, not a live feed.

---

## 12. Environment and pre-build checklist

Environment: use uv with Python 3.11 or 3.12 (not system 3.9), install the SDK with the viz and
sam extras, set FAL_KEY for SAM3 and CYVL_API_KEY for the REST API, keep both in a gitignored
.env. MCP `i3` (or `cyvl` locally) is authenticated for Claude Code dev.

Checklist before building:
- [ ] SDK imports and loads the Somerville scene
- [ ] FAL_KEY works (a SAM3 locate returns a distance)
- [ ] REST API reachable with the team key; pavement query in a Davis Square bbox returns data
- [ ] Confirm the team project_id and whether it has imagery embeddings
- [ ] Demo region chosen and its data plus LiDAR pre-cached
- [ ] MassDOT roads and AADT fetch for the region works
- [ ] One known-good frame and two measurement pixels validated by eye

---

## 13. Stretch and open decisions

Stretch: a real Stage 1 CV classifier, the fine-tuned detector, a Gaussian splat of the winning
block, a zoning gate, a refined trench-cost model, and forecourt / parking-lot mode. Forecourt
is the big one: the moment Cyvl captures off-street parcels and lots, the same screening engine
runs on them with no architecture change, which extends Sonder from curbside L2 to off-street
DCFC and the ChargePoint / EVgo / Electrify America pad buyers. "Every street Cyvl scans, and
every lot they scan next, is a market we can screen."

Open: confirm Davis Square as the demo region; decide whether to train the detector or ship
SAM3 only for the demo.

---

Last updated 2026-06-13. Build sections 5.2 and 5.3 first; read section 10 before the demo.
