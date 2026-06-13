# Agent Swarm - Backend Development Plan

Stage 2 of Sonder. Takes the validated shortlist from screening, sends one Claude agent per
site, and produces a grounded rating plus a clean, structured, professional report as JSON.
This is backend only. The frontend (the visual swarm, the map) is wired later. PDF generation
is a stretch, kept separate at the end.

Standalone for now: this `swarm/` package consumes a screening-output contract (a JSON list of
sites with their measured data), it does not import the screening package yet. We merge and
clean up the integration later. Grounded in research/ (see research/00-SYNTHESIS.md).

---

## 1. Goal and non-goals

Goal: for each shortlisted curb site, output a reliable, non-hallucinated rating (Tier 1/2/3 or
No-go) and a structured, bulleted, professional report, as validated JSON, fast and reproducibly.

Non-goals (now): the frontend, the live map, the visual swarm animation, and anything that
requires data we do not have. PDF is a stretch (section 11).

The bar: a reviewer who knows EV siting should read a report and find it professional, specific,
and free of invented numbers. Every figure must trace to real input data, and every unknown must
be a named "verify on site" line, never a guess. This mirrors how real studies (SCAG, NYSERDA)
handle missing grid data.

---

## 2. The one reliability principle

Deterministic code does the math and the hard gates. The LLM does judgment, narrative, and
vision. We never ask the model to compute a distance, sum a cost, or decide a hard gate that code
can decide. Reasons: arithmetic and gating are where LLMs are least reliable and least
reproducible, and they are trivial in code. The model is reserved for what only it can do: weigh
trade-offs, write the rationale, and look at the photo for blockers the data does not capture.

So a site's gates and component scores are computed in code (reusing the screening logic). The
agent receives those as facts, validates them against what it sees, assigns the tier with a short
justification, writes the report prose and bullets, and flags anything uncertain.

---

## 3. Architecture (standalone components)

```
screening shortlist (JSON contract: sites + measured data)
   |
DATA BUNDLER  - assemble one self-contained bundle per site:
   screening facts + SDK measurement (frontage, clearances) + CV masks/findings
   + public layers (zoning, nearby chargers) + the evidence photo
   |
ORCHESTRATOR  - run agents in bounded concurrent waves, with retry/fallback
   |
PER-SITE AGENT  - system prompt = skills-file; input = bundle + photo
   -> emits report JSON (forced schema)
   |
VALIDATORS  - schema -> grounding/provenance -> consistency -> (optional) adversarial verify
   |
CACHE  - keyed by (site_id, data_hash, prompt_version); identical input -> identical output
   |
OUTPUT: a list of validated per-site report JSON objects
```

Each component is small and testable on its own. The orchestrator never trusts an agent's raw
output; it only emits objects that pass the validators.

---

## 4. The per-site data bundle (the contract)

The bundler produces one JSON object per site that is everything the agent is allowed to use.
Nothing outside the bundle may appear in the report. Contents:

- site: id, GPS lat/lon, street, region.
- measured (from screening + the SDK): usable_frontage_ft, road_width_ft, distance_to_power_m,
  pole_type, obstruction list with positions, pavement_pci, surface, clearance checks.
- derived (from screening): component scores, gate results, make-ready cost estimate + band,
  residential_suit, traffic_suit, functional_class.
- public: zoning flag, nearby_chargers, road_class/AADT where available.
- evidence: photo reference, CV segmentation findings.
- known_unknowns: the fixed verify-on-site set (grid/transformer capacity, phase/voltage, permit,
  ADA slope, parking regulations), passed in so the agent always carries them through.

The bundle is the single source of truth and the grounding allow-list. The validator later checks
that every fact in the report came from here.

---

## 5. The agent contract

- System prompt = the skills-file: the criteria, the hard gates, the Tier 1/2/3 bands, the
  report JSON schema, the anti-hallucination rule, the vision instructions, and the fixed
  verify-on-site set. Versioned, so caching and evals are stable. Derived from research docs 01
  and 03.
- Input = one site bundle plus the evidence photo (vision).
- Task = validate the provided facts, use vision to catch unmodeled blockers (bus stop, loading
  zone, driveway, construction), assign the tier with a one-line reason, and fill the report
  schema. Judge, do not compute. Route every unknown to verify-on-site.
- Output = the report JSON, forced via structured output, low temperature.

---

## 6. The reliability stack

An agent's output is accepted only after passing, in order:

1. Schema validation. Force structured output and validate against the report schema (pydantic
   or equivalent). On failure, retry once with the validation error fed back, then fall back.
2. Grounding / provenance guard. The key anti-hallucination layer. Every numeric and factual
   field in the report must trace to a value in the bundle. A deterministic check compares
   reported numbers against the allow-list and rejects (or quarantines to verify-on-site) any
   number not present in the input. This makes invented figures structurally impossible to ship.
3. Consistency checks. Tier matches the score band, a gated site is No-go, the cost band matches
   the distance, the verdict reason references a real driver. Cheap deterministic assertions.
4. Adversarial verify (recommended). A second, cheap pass (a critic agent prompted to find
   unsupported claims, or a deterministic claim-checker) audits the report before accept. Default
   to rejecting on doubt. Use for the demo finalists, skip for bulk if cost matters.
5. Determinism. Low temperature, fixed prompt version, and a cache keyed by
   (site_id, data_hash, prompt_version) so the same input always yields the same output. This is
   what keeps the demo stable across rehearsals.
6. Failure handling. Per-agent timeout and retry with backoff. If an agent still fails, fall back
   to a deterministic report assembled from the screening data alone (verdict from the score, no
   prose), so one bad agent never sinks the swarm. Dead agents resolve to a clearly-marked
   fallback, never to a crash.

---

## 7. Anti-hallucination (explicit guarantee)

The user requirement is no invented data. We guarantee it three ways, not one:

- Allow-list grounding: the bundle is the only permitted source, and the provenance guard
  (6.2) programmatically rejects any reported number not in it.
- Fill-or-flag rule: the agent is instructed to fill only fields it can ground, and to route
  everything else to verify-on-site. The schema has a required to_be_verified list, so the model
  is rewarded for deferring rather than guessing.
- Source tags: every report field carries a tag (have / partial / verify), so a thin field is
  visible as thin rather than dressed up. This is exactly the convention real reports use.

Net: a number either came from the scan and public data, or it is labeled verify-on-site. There
is no third path to a value.

---

## 8. Concurrency, rate limits, cost, determinism

- Run agents in waves of about six concurrent, with backoff on rate-limit errors. About 25 to 50
  finalists complete in a couple of minutes.
- Per-agent token budget and a swarm-size parameter, so a run is bounded and cheap. Screening
  already removed the bulk, so the swarm only spends tokens on the shortlist.
- Use the cheaper model for routine sites and reserve the stronger model for close calls and the
  adversarial verify, or run a single tier and measure before optimizing.
- Cache everything during development so we are not re-paying while iterating.

---

## 9. Evaluation harness (how we know the agents are reliable)

We do not trust the swarm until it is measured. Build a small eval harness early:

- Golden set: 8 to 12 real Somerville sites with hand-checked expected tiers and the obvious
  gate outcomes (a hydrant site should fail, a clean collector near power should be Tier 1).
- Metrics, run on every prompt or schema change:
  - schema-valid rate (target 100 percent after one retry),
  - hallucination rate: count report numbers not present in the bundle (target 0),
  - determinism: same input run N times yields identical output (target 100 percent),
  - gate and tier consistency rate (target 100 percent),
  - tier agreement with the golden labels (track, investigate misses),
  - latency and cost per site.
- This harness is the difference between "the agents seem fine" and "the agents are reliable."
  It also catches prompt regressions instantly.

---

## 10. Build order

1. Define the report JSON schema (from research/04 and 00-SYNTHESIS Artifact 2) and the
   skills-file (from research/01 and 03). These are content, write them first.
2. Build the data bundler against a sample screening output (standalone, a fixed JSON fixture).
3. One agent end to end: bundle in, validated report JSON out, stable across reruns.
4. Add the reliability stack (schema, grounding guard, consistency, retry/fallback).
5. Build the eval harness and the golden set, get the metrics green.
6. Scale to the batched swarm with caching and concurrency control.
7. Add the adversarial verify pass.
8. Stretch: the PDF (section 11).

Rule: one site fully grounded, validated, and reproducible before scaling to many. A reliable
single agent times N is a reliable swarm; an unreliable one times N is N problems.

---

## 11. Stretch: PDF generation (separate from the backend core)

From research/05. Render the same report JSON into a styled PDF with WeasyPrint plus Jinja2
(HTML and CSS to PDF in pure Python, supports @font-face, @page, running headers, page numbers).
Because the PDF renders from the validated JSON, it inherits the no-hallucination guarantee: it
can only show what passed the validators. The CSS skeleton, fonts, palette, and RAG scorecard
chips are specified in research/05. Keep this out of the critical path; the JSON is the product,
the PDF is the polish.

---

## 12. Standalone now, integrate later

This package talks to screening only through the bundle contract (a JSON list of sites with
measured fields). That lets us build and test the swarm against a fixture without touching the
screening branch. When we merge, the integration is one adapter that calls screening and maps its
output into the bundle. We clean up the shared pieces (config, the gate/score reuse, the .gitignore
divergence between branches) at merge time.

---

## 13. Open decisions

- Model choice per stage (single model vs cheap-bulk plus strong-for-close-calls plus verifier).
- Whether the adversarial verify is an agent or a deterministic claim-checker for the MVP.
- Where the skills-file lives and how it is versioned.
- Whether to compute SDK measurements (frontage, clearance) inside the bundler now or stub them
  from screening until the SDK measurement path is wired.

---

Last updated 2026-06-13. Build sections 1 and 2 of the order first; the eval harness (9) is what
makes "reliable" true rather than hoped.
