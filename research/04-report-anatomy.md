# Report Anatomy: Professional EV / EVSE Site Assessment, Feasibility & Site-Survey Reports

**Research deliverable for the Sonder project** — anatomy + content of real professional EV charging site assessment, feasibility study, and site-survey reports, mapped to a canonical one-site report template that a developer can convert directly into a JSON schema.

Date: 2026-06-13. Sources read in depth (full PDFs / pages) are listed in §D with inline citations throughout.

Scope reminder — Sonder screens **curbside / on-street Level 2** sites in **Somerville, MA** and emits one **structured (bulleted/tabular)** report per site, filling only fields we actually have. Tags used below:
- **[have]** — Sonder produces this directly from its data.
- **[partial]** — Sonder has a proxy / partial value; present it but label the limitation.
- **[verify-on-site]** — real reports include this field; Sonder cannot derive it and must explicitly defer it (this is the single most important convention in this domain — see §A.5).

---

## A. Overview of Conventions

### A.1 Three overlapping document genres (and which one Sonder is)
Professional practice blends three deliverable types. Sonder is a hybrid of (1) and (3), at the screening end of the maturity curve.

| Genre | Purpose | Typical author | Granularity | Example read |
|---|---|---|---|---|
| **Feasibility / planning study** | Network-wide: how many chargers, where, phasing, business model | Consulting/engineering firm (HNTB, Kimley-Horn, Cadmus, WXY) | Many sites, ranked | Sky Harbor / HNTB; Somerville/Cadmus; NYSERDA "Curb Enthusiasm" |
| **Electrical / make-ready assessment** | Can power reach this site, at what cost, what upgrades | EE / utility | One site, deep electrical | Prism Engineering electrical planning report |
| **Site survey / field checklist** | Field-verified inventory of one site's conditions | Field tech / installer | One site, exhaustive checklist | SafetyCulture / popprobe ADA checklist; DOT planning checklist |

The **per-site "mini-report" block** that recurs inside a feasibility study (Sky Harbor §6: each facility gets *Distribution Approach* + *ROM Cost Estimate*) is the single closest analog to a Sonder one-site report. Sonder should mirror that block structure: a short narrative recommendation, then itemized cost, then assumptions.

### A.2 The "Rough Order of Magnitude (ROM)" framing is the professional norm
The Sky Harbor / HNTB study labels every cost a **"ROM cost estimate"** and states explicitly that costs are *"hard construction costs and do not include any soft costs"* and *"do not include any potential offsite upgrades that may be required"* (Sky Harbor §6, pp. 6-1). This is the gold-standard convention: **always name the cost class (ROM / Class 5 screening estimate / planning-level), and bound it with explicit exclusions.** Sonder's make-ready number should be presented identically: a ROM/screening number with a stated basis and explicit exclusions (no soft costs, no transformer/grid upgrades, no permits).

### A.3 Scoring & recommendation is almost always *tiered*, not pass/fail
None of the real reports use a binary "go/no-go." They use:
- **Point bins on a 0–10 scale per criterion**, summed/weighted to a composite (SCAG: 0,1,3,5,7,10 levels labeled Lowest→Highest; Somerville composite 0.00–0.88).
- **Priority Groups / Tiers 1–3** for the recommendation layer (Sky Harbor "Priority Group 1/2/3 with Priority 1 as the most critical need"; SFMTA/CILI "five priority tiers").
- **Weighted overlay**: each criterion reclassified to a common 1–10 scale, multiplied by a weight, summed to a composite suitability score (GIS multi-criteria practice).

So Sonder should output **(a) a tiered recommendation (e.g., Tier 1 / 2 / 3 or Recommended / Conditional / Not Recommended)** plus **(b) a per-criterion scorecard table** with sub-scores. See §C for layouts.

### A.4 Executive-summary conventions for this domain
Observed pattern (Somerville/Cadmus ES, Sky Harbor ES-1..ES-13, NYSERDA abstract):
- **Length:** 1 page for a single site; for a study, a multi-page ES that itself contains summary *tables* (Sky Harbor ES uses Tables ES-2..ES-5 of cost & stalls by priority).
- **What leads:** the *objective* sentence first ("The objective of this report is to identify…"), then the *headline finding/recommendation*, then the *number* (Somerville leads with "the installation of just five level 2 public chargers could put the majority of residents within 0.5 mile").
- **Form:** opens in short prose (2–4 sentences) then pivots to **bulleted "key decisions / next steps"** and **summary tables**. The ES is where the single recommendation and the headline cost live.
- For Sonder: ES = 3–5 bullet "verdict" lines (tier, headline reason, ROM cost, top risk, single next step) + the scorecard table. Lead with the verdict.

### A.5 How uncertainty / assumptions / "to be verified on site" are handled (critical)
This is pervasive and explicit in every credible report. Patterns to copy verbatim in tone:
- **A dedicated Assumptions block** stating what was assumed for costing (Sky Harbor: *"A split between single and dual port… was assumed… The actual distribution… will need to be determined during the design process."*).
- **Explicit data-limitation disclaimers.** SCAG *excluded grid capacity and utility infrastructure entirely* because *"a reliable dataset was not available"* and noted these *"can be evaluated as needed during project development"* — exactly Sonder's situation. Somerville flagged it *"did not [account for]… curb cuts, bike share, and electric distribution capacity."*
- **"Mandatory site survey / load letter" deferral.** NYSERDA: *"Proposed sites should have a mandatory site survey in coordination with utilities (Con Edison) to determine financial feasibility of bringing power to the site"* — i.e., true power feasibility is always punted to a utility step.
- **A formal disclaimer/notice page** (NYSERDA, INL/PNNL) absolving accuracy and stating non-endorsement.

**Sonder rule:** every field Sonder cannot truly know (transformer/grid capacity, true parking-stall count, permit outcome, real traffic counts, subsurface utilities) must appear in the report **as a named line tagged "To be verified on site"** rather than be silently omitted — omission looks like negligence; explicit deferral looks professional. Provide a single consolidated **"Assumptions & To-Be-Verified" section** near the end.

### A.6 Data-field / table conventions (what real per-site records carry)
Common identity + measurement fields seen across sources: Site ID/label, address (and **GPS coordinates — NYSERDA notes curb sites "may not have an associated address," so lat/long is preferred**), facility/user group, charger type & port count, EV-installed stall count, dimensions (space ≥ 8 ft wide; aisle ≥ 5 ft; ADA clear floor 30"×48"), distances (to panel/power, trench length), ratings/scores (PCI, suitability sub-scores), costs (infrastructure vs charger install vs total), and **photo callouts/figure references** (every site gets a labeled figure/photo). Standards refs cited as boilerplate: ADA Standards for Accessible Design, MUTCD, AASHTO Green Book, NEC, local street design manual.

---

## B. Canonical Section-by-Section Template for a Sonder One-Site Report

Order below follows the professional convention (cover → executive verdict → context → scored conditions by discipline → cost → risks → next steps → evidence → appendix). Each section lists real-world content, then maps Sonder data with tags.

### 0. Cover / Title Block
Real content: report title, site name/ID, address, client/jurisdiction, prepared-by, date, version, a hero site photo, a disclaimer footer.
Sonder mapping:
- Report title + Site ID **[have]**
- Address / nearest cross-streets **[have]** (Somerville street)
- Coordinates (lat/long) **[have]** — lead with this for curb sites (NYSERDA convention)
- Jurisdiction = City of Somerville **[have]**
- Prepared-by = "Sonder automated curbside screening" + run date **[have]**
- Hero image = the evidence street photo **[have]**
- Standard disclaimer footer (auto-screening, not a substitute for engineering survey) **[have]** (boilerplate)

### 1. Executive Summary / Recommendation (the verdict)
Real content: objective sentence; the single recommendation; headline cost; top constraint; next step. Leads the document; bulleted + one summary table (per A.4).
Sonder mapping (bulleted, ≤5 lines + scorecard):
- **Recommendation tier** (Tier 1 Recommended / Tier 2 Conditional / Tier 3 Not Recommended now) **[have]** — derived from composite score
- **Composite suitability score** (e.g., 0–100 or 0–10) **[have]**
- **One-line rationale** (top 1–2 drivers, e.g., "ample 60 ft frontage, power asset 18 ft away") **[have]**
- **ROM make-ready cost** (with "screening estimate" label) **[partial]** — from trench distance; exclude soft costs/grid
- **Top risk / blocker** (e.g., hydrant within space; poor PCI) **[have]**
- **Single recommended next step** (e.g., "request Eversource load letter; field-verify ADA aisle") **[verify-on-site]** (boilerplate next-step text)

### 2. Site Overview / Location Context
Real content: location description, jurisdiction, functional road class & demand context, zoning/land-use, surrounding uses, existing chargers nearby, a locator map. (Somerville §2 "Background and Context"; SCAG land-use & proximity-to-existing-charger criteria.)
Sonder mapping:
- Street name, segment, coordinates **[have]**
- Locator map / context map **[have]** (public layers)
- FHWA functional class (residential vs. arterial/traveler-demand proxy) **[have]** — present as a *demand proxy*, label as proxy **[partial]** for true demand
- AADT / road class **[partial]** — "where available; proxy for utilization, not site-specific traffic count"
- Nearby existing chargers (count + nearest distance) **[have]** — mirrors SCAG "proximity to existing EVCS" criterion
- Zoning flag **[have]**
- Parcel interior / adjacent land use detail **[verify-on-site]** (no parcel interiors)

### 3. Site Suitability Scorecard (the scored table — see §C for layout)
Real content: the per-criterion scored matrix that feeds the recommendation (SCAG Table 4; Somerville priority index; weighted overlay). Each criterion → sub-score (0–10) → weight → contribution. This is the analytical heart of the report.
Sonder criteria (each [have] unless noted), each scored 0–10 with a weight:
- Usable curb frontage length vs. required stall+aisle footprint **[have]**
- Distance to nearest power asset (pole/luminaire) **[have]** — drives make-ready (NYSERDA: "Prioritize sites close to an electrical panel, as trenching… can render sites financially unfeasible")
- Make-ready ROM cost band (inverse score) **[partial]**
- Pavement condition (PCI) / surface type **[have]**
- Obstruction load (hydrant/tree/catch basin presence & proximity) **[have]**
- Road functional class / demand proxy **[partial]**
- Proximity to existing chargers (coverage-gap score) **[have]**
- Cartway width adequacy (room for EV stall without impeding travel/bike lane) **[have]**
- Equity / environmental-justice tier of the block group **[have]** (MA EJ framework — directly used in Somerville report)
- True grid/transformer capacity **[verify-on-site]** — show row as "Not scored — requires utility load letter" (mirror SCAG's explicit exclusion)

### 4. Demand / Utilization Context
Real content: who will use it, turnover, dwell-time logic, EV adoption/ownership context (NYSERDA §3.2.3 "Identify Street Conditions that Optimize Level 2 Utilization"; SCAG EV-ownership bins; Somerville commuting patterns).
Sonder mapping:
- Functional class as demand proxy **[partial]**
- Coverage gap (distance to nearest charger) **[have]**
- Block-group MUD density / commuting-by-car (if from public layers) **[partial]**
- Parking turnover regime (metered/time-limited favors turnover per NYSERDA) **[verify-on-site]** — present as a question if curb regulation unknown
- Actual session/utilization forecast **[verify-on-site]**

### 5. Electrical / Utility Assessment
Real content (Prism 6-step; Sky Harbor §5): existing service/panel/SES condition & spare capacity, upstream feeder/transformer capacity, distance from source to chargers, proposed distribution approach, required upgrades. **This is where real reports are deepest and where Sonder has the least true data — handle with explicit deferral.**
Sonder mapping:
- Nearest power asset type & distance (pole/luminaire) **[have]** — proxy for service availability
- Implied trench/conduit run length **[have]**
- Proposed distribution approach (1-line: "tap nearest luminaire/secondary; trench ~X ft to curb stall") **[partial]** — narrative proxy
- Transformer / secondary capacity, spare breaker availability, service voltage/phase **[verify-on-site]** — state "requires utility load letter (Eversource)" (NYSERDA mandatory-site-survey convention)
- Metering approach **[verify-on-site]**

### 6. Civil / Site Conditions
Real content: pavement condition & surface, cartway/right-of-way width, sidewalk width, grades/slopes, drainage, subsurface conflicts, obstructions. (Maine guide grades/slopes; NYSERDA setback 450mm / 2m sidewalk min from TfL; survey checklists.)
Sonder mapping:
- Pavement condition index (PCI) + surface (asphalt/concrete) **[have]** — note trenching restoration cost link
- Cartway / road width **[have]**
- Usable curb frontage **[have]**
- Detected obstructions with positions: hydrant, tree, catch basin **[have]** — CV-detected; list each with offset
- Sidewalk width / clear pedestrian path **[verify-on-site]** (unless CV provides) — NYSERDA 2 m min
- Slope / cross-slope (ADA ≤ 2% / 1:48) **[verify-on-site]**
- Subsurface utilities / drainage conflicts **[verify-on-site]**

### 7. ADA / Accessibility
Real content (Maine guide; popprobe 37-item / 7-section checklist; ADA Standards): accessible space 96" (8 ft) wide, access aisle ≥ 60" (5 ft) — Maine recommends 11 ft × 20 ft space + 5 ft aisle; clear floor 30"×48"; reach range 15–48"; slope ≤ 2%; ≥ 5% (≥1) of spaces accessible / "1 per 25"; "use last" signage model; curb-mounted chargers ≤ 10" from curb face.
Sonder mapping:
- Frontage sufficient for accessible space + aisle footprint **[have]** — geometric check from frontage length
- Cartway width allows aisle without blocking travel lane **[have]**
- Obstruction-free clear floor zone (no hydrant/tree in space) **[have]** — from obstruction detections
- Slope / cross-slope ≤ 2% **[verify-on-site]**
- Surface firm/stable/slip-resistant; gaps ≤ ½" **[partial]** (PCI proxy) → flag verify
- Reach range / mounting height / controls **[verify-on-site]** (equipment-dependent)
- Required accessible-stall count **[have]** (rule-based: 1 per 25 / ≥1)

### 8. Parking / Layout / Curb-Use Conflicts
Real content: stall count & geometry, parking regulation regime, conflicts with bus stops/bike lanes/loading/hydrant clearance, curb-management impact. NYSERDA "deployment challenges to avoid": transit-priority streets, bus layovers, protected bike lanes, frequent street-closure blocks, peak-period-restricted parking, historic districts.
Sonder mapping:
- Estimated stalls from usable frontage **[partial]** (geometry estimate, not surveyed count)
- Layout sketch / stall placement vs obstructions **[have]**
- Hydrant clearance conflict **[have]** (obstruction detection)
- Bike-lane / bus-stop / transit-priority conflict **[partial]** (if in public layers) → else **[verify-on-site]**
- Parking regulation (metered/time-limited/RPP) **[verify-on-site]** — note it affects turnover/utilization
- Historic-district / landmark trigger **[partial]** (if zoning layer flags) → else verify

### 9. Cost Estimate / Make-Ready Budget (ROM)
Real content (Sky Harbor §6; commercial cost guides): itemized — (a) charger hardware, (b) charger installation, (c) electrical infrastructure (panel/feeder/conduit/wire), (d) civil (trenching $50–150/LF saw-cut + restoration, conduit, concrete, bollards, striping, signage), (e) utility make-ready (service/transformer/metering), (f) soft costs (design, permits, PM). Always labeled ROM with explicit exclusions.
Sonder mapping (present as itemized table, see §C):
- Trench/conduit civil cost (from trench distance × unit rate) **[have]** — Sonder's core cost output
- Pavement restoration premium (PCI/surface-driven) **[partial]**
- Charger hardware + install allowance **[partial]** (typical-range allowance, label as allowance)
- Utility-side make-ready (transformer/service) **[verify-on-site]** — explicitly excluded, "TBD via load letter"
- Soft costs (design/permits/PM) **[verify-on-site]** — explicitly excluded line
- **ROM total + exclusions note** **[have]** (boilerplate exclusions per A.2)

### 10. Risks, Constraints & Permitting
Real content: site-specific risk register; permitting complexity (Seattle EVCROW lists ~7 permits; SFMTA "permitting… in the public right of way are complex"); deployment-challenge flags; vandalism (Berkeley CLEE: single curb chargers face more vandalism).
Sonder mapping (bulleted risk table — Risk / Severity / Note):
- Obstruction conflicts (hydrant/tree/catch basin) **[have]**
- High make-ready cost / long trench **[have]**
- Poor pavement (restoration cost / future repaving conflict) **[have]** — NYSERDA "identify future paving project conflicts"
- Narrow cartway / travel-lane impact **[have]**
- Curb-use conflict (bike/transit) **[partial]**
- Permitting complexity / utility load-letter dependency **[verify-on-site]** (boilerplate)
- Grid capacity unknown **[verify-on-site]**

### 11. Recommendation & Next Steps
Real content: restate tier; phased/priority placement; concrete next actions (Somerville next-steps bullets; NYSERDA "mandatory site survey… load letter"; Sky Harbor priority-group assignment).
Sonder mapping:
- Tier + composite score (restated) **[have]**
- Priority-group rank vs other screened sites **[have]** (if batch run)
- Next steps: request utility load letter; field ADA survey; confirm parking regulation; subsurface locate **[verify-on-site]** (boilerplate sequence)

### 12. Photos & Figures
Real content: every site gets labeled photo(s), a location map, a layout/concept figure, with figure numbers and captions.
Sonder mapping:
- Evidence street photo (with CV segmentation overlay) **[have]** — caption with detections labeled
- Annotated obstruction map (hydrant/tree/catch basin positions) **[have]**
- Locator/context map **[have]**
- Layout concept (stall + charger + trench run) **[partial]** (generated sketch)

### 13. Appendix: Data Sources, Assumptions & To-Be-Verified
Real content: data-source list & vintage (SCAG Table 2 lists every dataset + URL + metric + date), methodology notes, assumptions, disclaimers, glossary, standards list.
Sonder mapping:
- Data-source provenance table (Cyvl pavement/asset layers, public zoning/AADT, photo run date) **[have]**
- Methodology / scoring weights note **[have]**
- **Consolidated "To-Be-Verified on Site" list** **[have]** (gathers all verify-on-site fields) — *the professional credibility anchor*
- Assumptions (cost unit rates, footprint geometry) **[have]**
- Standards referenced (ADA, MUTCD, AASHTO, NEC) **[have]** (boilerplate)
- Glossary (ROM, EVSE, PCI, make-ready, EJ) **[have]**

---

## C. Example Scorecard / Table Layouts (copy these into the JSON schema)

### C.1 Per-criterion scoring scale (from SCAG Table 3 — the canonical bin scale)
```
Level        Points
Highest        10
High            7
Medium          5
Medium/Low      3
Low             1
Blank / N/A     0
```
Sonder should adopt this exact 0/1/3/5/7/10 banded scale per criterion (it reads as professional and avoids false precision).

### C.2 Site Suitability Scorecard table (the analytical core, §B.3)
| Criterion | Raw value | Sub-score (0–10) | Weight | Weighted | Confidence |
|---|---|---|---|---|---|
| Usable curb frontage | 62 ft | 10 | 0.15 | 1.50 | High [have] |
| Distance to power asset | 18 ft | 7 | 0.20 | 1.40 | High [have] |
| Make-ready ROM cost | $14k band | 5 | 0.15 | 0.75 | Med [partial] |
| Pavement (PCI) | 78 / good | 7 | 0.10 | 0.70 | High [have] |
| Obstruction load | 1 (tree, 9 ft off) | 7 | 0.10 | 0.70 | High [have] |
| Cartway width adequacy | 32 ft | 10 | 0.10 | 1.00 | High [have] |
| Demand proxy (func. class) | Local/residential | 3 | 0.10 | 0.30 | Low [partial] |
| Coverage gap (existing chgr) | 0.4 mi | 7 | 0.05 | 0.35 | High [have] |
| Equity / EJ tier | Tier 2 EJ | 7 | 0.05 | 0.35 | High [have] |
| Grid/transformer capacity | — | n/s | — | — | Not scored [verify-on-site] |
| **Composite** | | | **1.00** | **7.05 / 10** | |

Weights are illustrative; expose them in config (weighted-overlay convention). Always include a **Confidence/tag column** so consumers see which sub-scores rest on proxies.

### C.3 Tiered recommendation banding (from composite)
| Composite | Tier | Label | Meaning |
|---|---|---|---|
| ≥ 7.0 | Tier 1 | Recommended | Advance to utility load letter + field survey |
| 4.0–6.9 | Tier 2 | Conditional | Viable if specific blockers cleared |
| < 4.0 | Tier 3 | Not recommended (now) | Suboptimal near-term; revisit later |

(Mirrors SCAG "highest-scoring parcels recommended for further site investigation… lowest brackets suboptimal in near-term but could be future sites," and Sky Harbor Priority Groups 1–3.)

### C.4 ROM make-ready cost table (from Sky Harbor §6 line-item style)
| Line item | Basis | ROM cost | Notes |
|---|---|---|---|
| Trench / conduit / wire | ~18 LF saw-cut @ $/LF | $X | Civil; PCI-driven restoration |
| Pavement restoration premium | PCI 78, asphalt | $X | |
| Charger install (mounting/concrete) | 1 dual-port pedestal allowance | $X | Allowance |
| Charger hardware | typical L2 range | $X | Allowance |
| **ROM subtotal (in-scope)** | | **$X** | |
| Utility-side make-ready (xfmr/service) | — | TBD | **Excluded — load letter** |
| Soft costs (design/permits/PM) | — | TBD | **Excluded** |
| **ROM total (screening)** | | **$X** | Hard costs only; excludes soft + offsite |

Always carry the Sky Harbor-style footer verbatim in spirit: *"ROM total costs are hard construction costs and do not include soft costs or potential offsite upgrades."*

### C.5 Risk register table (§B.10)
| Risk / constraint | Likelihood | Impact | Source field | Mitigation / next step |
|---|---|---|---|---|
| Tree within 9 ft of stall | Med | Med | CV obstruction | Confirm clear floor space; possible shift |
| Grid capacity unknown | — | High | (no data) | Eversource load letter |
| Future repaving conflict | Low | Med | PCI/road class | Coordinate w/ DPW paving schedule |

### C.6 "To-Be-Verified on Site" block (§B.13) — flat list, professional credibility anchor
- Transformer / secondary capacity & service voltage/phase — *utility load letter (Eversource)*
- Subsurface utilities along trench route — *Dig Safe / locate*
- ADA slope & cross-slope (≤ 2%) — *field measurement*
- Actual on-street parking regulation / turnover regime
- Surveyed stall count & striping geometry
- Permit pathway (PROW / electrical / historic-district review)

### C.7 Executive-summary block (§B.1) — lead-with-verdict shape
```
RECOMMENDATION: Tier 1 — Recommended (composite 7.05/10)
WHY: 62 ft usable frontage; power asset 18 ft away; good pavement (PCI 78).
ROM MAKE-READY (screening, hard costs only): ~$14,000 (excludes utility upgrades & soft costs).
TOP RISK: Street tree 9 ft from candidate stall; grid capacity unverified.
NEXT STEP: Request Eversource load letter; field-verify ADA aisle & slope.
```

---

## D. Sources (URLs)

Read in depth (full PDF text extracted):
- SCAG EV Charging Station Study — Site Suitability Analysis Methodology (scoring bins, weights, explicit grid/utility exclusions): https://scag.ca.gov/sites/default/files/2024-05/scag_ev_charging_station_study_-_final_scoring_methodology.pdf
- NYSERDA / NYSDOT "Curb Enthusiasm: Report for On-Street Electric Vehicle Charging" (Report 19-11) — curbside siting principles, street-condition criteria, deployment-challenge avoidance list, mandatory site-survey/load-letter convention, ADA references: https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/Research/Transportation/19-11-Curb-Enthusiasm.pdf
- Phoenix Sky Harbor (PHX) EV Charging Feasibility Study, May 2023 (prepared by HNTB) — professional TOC, per-site Distribution Approach + ROM Cost Estimate blocks, priority groups, assumptions/disclaimer conventions: https://www.skyharbor.com/media/tibfn1tk/2023_june_ev_study_final_report.pdf
- City of Somerville — "Public Electric Vehicle Charging in Somerville: Status, Options, and Considerations" (Cadmus, June 2020) — exec-summary form, Key-Decisions table, curbside priority-index (4 criteria), MA EJ tiering, data-limitation disclaimers: (City of Somerville OSE; via municipal records)
- Berkeley CLEE — "City Public and Curbside EV Charging Strategies" brief (Mar 2024) — curbside site-selection criteria, streetlight/utility-pole leverage, capacity & curb-use conflicts, equity vs utilization tradeoff: https://www.law.berkeley.edu/wp-content/uploads/2024/03/City-Public-and-Curbside-EV-Charging-Strategies_CLEE-Brief_Mar2024.pdf
- Seattle DOT — EV Charging in the Right-of-Way Permit Pilot (EVCROW) 1.0 Evaluation Report — permitting load, EVCROW siting criteria: https://www.seattle.gov/documents/Departments/SDOT/CapitalProjects/EVCROW/EVCROWEvaluationReport.pdf
- City of Portland — EV Charging in the Public Right-of-Way Code Project report (Feb/Mar 2023): https://www.portland.gov/transportation
- US DOE Joint Office / Volpe — "Community Charging: Emerging Multifamily, Curbside, and Multimodal Practices" (Feb 2024, DOE/EE-2806): https://driveelectric.gov/files/community-charging.pdf
- Maine guide — "Installing EV Chargers for Everybody: Ensuring Accessible EV Charging Stations in Maine" (Jan 2024) — ADA dimensions, on-street/curb-mounted specifics, number-of-spaces, "use last" signage: (Maine DEP/Governor's Energy Office)
- INL/PNNL — "EV Charging Infrastructure Energization" (Jan 2025) — energization/load-service-request process, disclaimer-page convention: https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-37179.pdf

Read via web (HTML):
- Prism Engineering — Electrical Assessment & Planning Report (6-step process; summary report of options/upgrades/cost): https://www.prismengineering.com/why-you-need-an-electrical-assessment-and-planning-report-before-ev-charging-stations/
- popprobe — EV Charging Station ADA Accessibility Inspection Checklist (7 sections / 37 items, with dimensions): https://www.popprobe.com/checklist-library/ev-charging-infrastructure/compliance/b27-evc-ada-accessibility-inspection-checklist
- SafetyCulture — EV Site Survey Checklist template (field-survey section list): https://safetyculture.com/library/energy-and-utilities/ev-site-survey-ykxtk0dwqvowqyfz
- US DOT Rural EV Toolkit — EV Infrastructure Project Planning Checklist (utility site assessment, scope/budget/timeline): https://www.transportation.gov/rural/ev/toolkit/ev-infrastructure-planning/project-planning-checklist
- PACE Clean Energy — EV Charging Site Assessment (7 considerations, 3-step process, DRVE tool): https://www.pacecleanenergy.org/path-to-100/transportation/municipal-action/ev-charging-site-assessment/
- GreenLancer — Commercial EV Charging Station Cost & Installation (make-ready cost line items & ranges): https://www.greenlancer.com/post/guide-commercial-electric-vehicle-charging-stations
- SFMTA — Curbside EV Charging Feasibility Study (curbside-specific study; PROW permitting complexity): https://www.sfmta.com/projects/curbside-ev-charging-feasibility-study
- Kimley-Horn — A Developer's Guide to EV Charging & ZEV Infrastructure Services (site selection→feasibility→design→permitting→utility coordination workflow; TREDLite EV scoring tool): https://www.kimley-horn.com/news-insights/perspectives/developer-guide-ev-charging/ ; https://www.kimley-horn.com/markets/energy/zero-emission-vehicles/
- Joint MCDA / GIS weighted-overlay practice (reclass to 1–10, weight, sum to composite suitability): https://www.sciencedirect.com/science/article/pii/S2666691X25000259 ; https://nccleantech.ncsu.edu/2023/02/27/mapping-ev-charging-station-suitability/

---

### Key takeaways for the Sonder JSON schema
1. Structure each report as: **cover → executive verdict (tier + score + ROM + risk + next step) → site overview → suitability scorecard → demand → electrical → civil → ADA → parking → ROM cost → risks/permitting → recommendation → photos → appendix (sources/assumptions/to-be-verified)**.
2. Score per-criterion on the **SCAG 0/1/3/5/7/10 band**, weighted-sum to a composite, and band the composite into **Tier 1/2/3** — never binary go/no-go.
3. Label every cost a **ROM/screening estimate** with explicit **exclusions** (no soft costs, no grid/transformer upgrades).
4. Carry a **Confidence/[have|partial|verify-on-site] tag on every field**, and consolidate all verify items into a **"To-Be-Verified on Site"** appendix block — this is what makes auto-generated output read as professional rather than hallucinated.
