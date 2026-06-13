# Agent-swarm research synthesis

Five deep-research passes feed the agent swarm: how pros judge sites, the electrical/make-ready
reality, curbside right-of-way standards, real report anatomy, and report typography/PDF. This
file ties them into the three artifacts we build next: the judging skills-file, the report JSON
schema, and the PDF style spec.

Source docs:
- 01-site-selection-methodology.md  (how pros judge and score)
- 02-electrical-makeready.md  (electrical, utility, cost)
- 03-curbside-standards.md  (ROW clearances, ADA, municipal checklists)
- 04-report-anatomy.md  (real report sections and tables)
- 05-report-style-and-pdf.md  (typography, color, PDF generation)

## What all five converged on

1. Tiered rating, not binary go/no-go. SCAG scores criteria on 0/1/3/5/7/10 bands, Somerville's
   Cadmus study uses a 0.00 to 0.88 composite index, Sky Harbor and SFMTA use Tiers 1 to 3.
   Sonder should output a composite score banded into Tier 1 / Tier 2 / Tier 3.
2. Two layers in real practice: a GIS weighted-suitability score to rank a shortlist, plus a
   separate engineering go/no-go gate (grid, ADA, permit, clearances). A site can score high and
   still die on one failed gate. Sonder does the score plus the physical-feasibility gates.
3. The decisive convention is explicit deferral of unknowns. SCAG deliberately excluded grid
   capacity "because a reliable dataset was not available." NYSERDA defers true power to a
   mandatory site survey and utility load letter. Every unknown becomes a named "verify on site"
   line, never omitted and never guessed. This is our anti-hallucination rule, and it is what
   real reports do, so it raises credibility rather than lowering it.
4. Curbside L2 inverts DC fast charge. Residential and local streets are a positive, demand is
   EV-ownership density times multifamily / no-driveway share (not traffic volume), dwell is
   hours, and power usually taps an existing pole or luminaire.
5. Distance to power is the biggest, most predictable cost swing, and it is exactly what our
   scan proxies. That is the core of our electrical story.

## Artifact 1: the judging skills-file (how the Claude agent rates a site)

A skills/criteria file the agent reads, derived from doc 01 and 03. Shape:

- Hard gates (Tier No-go regardless of score):
  - No power within the cost-justified distance (our existing screen gate).
  - Clearance violations from detected assets: hydrant (Portland 10 ft; flag MA may differ),
    driveway 5 ft, bus stop 30 ft, intersection 25 ft, stop sign 20 ft. (doc 03)
  - Frontage too small for the chosen station size.
  - Pavement failed; or a fire-lane / no-parking marking present.
  - Zoning prohibits (when the layer is wired).
- Weighted score on survivors, banded into Tier 1/2/3, across: make-ready cost (from power
  distance + surface), physical fit, demand (residential + traveler blend), clearance margin,
  pavement/trench, competition (existing chargers within ~2 mi).
- The agent judges the provided measured facts plus the street photo (vision) against this
  rubric. It never invents numbers. It uses vision to catch what the data misses (bus stop,
  loading zone, driveway, construction) and routes those to gates or to verify-on-site.
- A fixed "verify on site" set the agent always emits: true grid/transformer capacity, phase and
  voltage, permit status, ADA running/cross slope, parking regulations, snow/tree-root issues.
  (docs 01, 02, 03)

## Artifact 2: the report JSON schema (structured output the agent emits)

From doc 04's 14-section canonical template. Each field tagged for honesty: [have] computed,
[partial] proxy, [verify] deferred. Proposed top-level structure:

- site: id, GPS lat/lon (curb sites have no street address, use coordinates), street name,
  region.
- verdict: tier (1/2/3 or No-go), composite_score, one_line_reason.
- executive_summary: a short objective line, the verdict + headline number, then bullets.
- scorecard: per-criterion rows {criterion, value, rating (GO/CAUTION/NO-GO), source_tag}.
- physical_fit: usable_frontage_ft, ports_that_fit, road_width_ft, layout_note. [have/partial]
- connection_and_make_ready: distance_to_power_m, pole_type, trench_len_ft, surface,
  rom_cost_usd with explicit exclusions (utility-side make-ready, soft costs, transformer if
  needed). Labeled ROM / screening estimate. [have/partial + verify]
- demand: residential_suit, traveler_suit, functional_class, nearby_chargers. [have/partial]
- site_conditions: pavement_pci, obstructions [{type, distance}], clearance_checks. [have]
- accessibility: near_curb_ramp, ground_space_note, ADA items flagged. [partial/verify]
- risks_and_constraints: bulleted.
- to_be_verified: the fixed deferral list above.
- evidence: photo_url, segmentation_masks, measured_line.
- next_steps: bulleted.

This is the backend's structured JSON. The PDF (stretch) renders from the same object, so there
is one source of truth and zero hallucinated fields.

## Artifact 3: the PDF style spec (stretch)

From doc 05. Generate with WeasyPrint + Jinja2 (HTML/CSS to PDF in pure Python, supports
@font-face, @page, running headers/footers, page numbers, repeating table headers). Spec:

- Typography: body 10-11pt sans (Calibri / Arial / Helvetica) or 11pt Times for a gov look;
  H1 24-28, H2 16-18, H3 13-14, captions 8-9; 2-3 fonts max; bold for emphasis, no underline.
- Layout: US Letter, 1 in margins, single column, cover page (logo, title, site coordinates,
  report id, prepared-for/by, date, accent band), running header/footer with report id and
  "Page X of Y", decimal section numbering, table captions above and figure captions below.
- Color: white background, near-black ink #1A1A1A, navy brand #14213D, one accent
  (orange #E76F00 or teal), grays #D0D5DD / #F2F4F7 for rules and zebra.
- Scorecard RAG chips, always color plus a letter/word so it survives grayscale:
  GO #2E7D32 (G), CAUTION #D69E2E (A), NO-GO #C62828 (R). Big verdict badge plus a per-criterion
  chip table. The copy-ready CSS skeleton is in doc 05.

## Honesty guardrail (applies to the whole swarm)

The agent fills only fields it can ground in the provided data. Anything else goes to
to_be_verified, never to an invented value. This mirrors how SCAG and NYSERDA handle missing
grid data, so a reviewer reads it as professional, not thin.

## Build order from here

1. Write the skills-file (criteria + gates + tier bands) as a file the agent reads.
2. Define the report JSON schema from Artifact 2 and force the agent to emit it (structured
   output, low temperature).
3. Wire the per-site data bundle (screening output + SDK measurement + CV masks + public layers)
   into the agent prompt.
4. Stretch: the WeasyPrint template that renders the JSON into the styled PDF.
