# EV Charging Site Selection Methodology — How Professionals Score & Rank Candidate Sites

**Prepared for:** Sonder (Cyvl Physical AI Hackathon) — curbside / on-street Level 2 EV charging site screening, Somerville MA
**Date:** 2026-06-13
**Purpose:** Ground Sonder's per-site rating criteria in documented professional EV-surveying and site-selection practice. Capture real taxonomies, weights, point systems, decision gates, and numeric thresholds, then map them to the data Sonder actually has.

---

## 0. Executive Summary of How Pros Actually Score Sites

There are two layers in real practice:

1. **GIS / desktop multi-criteria suitability scoring** (used by MPOs, cities, NREL/EVI-Pro modeling, and software vendors like EVpin/CARTO). This produces a *ranked shortlist* of candidate parcels/curb segments from public data layers — demand, equity, land use, proximity to existing chargers, traffic. Almost always a **weighted additive / point-based model** (most commonly normalized to a 0–10 per-criterion scale), sometimes formalized with AHP (Analytic Hierarchy Process) to derive weights and TOPSIS to rank.
2. **Engineering / feasibility go-no-go gating** (used by CPOs, EPCs, and consultants like Kimley-Horn, AECOM, HDR). This is *not* a smooth score — it is a sequence of **hard gates**: grid/electrical feasibility, ADA path-of-travel, permitting/zoning, make-ready cost vs. budget, and utilization breakeven. A site can score high on suitability and still be killed by a single failed gate (e.g., no nearby transformer capacity, or trench too long).

Sonder sits primarily in **Layer 1 plus the physical-feasibility portion of Layer 2** (proximity to power, frontage, obstructions, pavement, ADA-relevant geometry) — exactly the parts that street-level 3D scan data can fill. The parts Sonder *cannot* fill (true transformer capacity, permit status, parcel interiors) are precisely the gates pros flag for "verify on site / utility coordination."

---

## 1. Full Taxonomy of Site-Selection Criteria

Synthesized across the Joint Office checklist, SCAG scoring methodology, JointCharging CPO guide, EVpin, CARTO, Kimley-Horn, and the academic MCDM literature. Categories below are the consensus "ten buckets."

| Category | Criteria pros use | Typical data source |
|---|---|---|
| **Electrical / Utility** | Distance to service/transformer; transformer spare capacity; feeder/substation headroom; available voltage & phase (240V 1Φ for L2 vs 480V 3Φ for DCFC); demand-charge tariff; interconnection queue/timeline | Utility GIS, interconnection inquiry |
| **Physical / Space** | Usable frontage/stall count & dimensions; cartway width; pad/equipment footprint; trench length & surface to cut (pavement vs landscaping); grade/drainage; obstructions (hydrant, tree, catch basin, sign, vault) | Site survey / 3D scan |
| **Accessibility / ADA** | Accessible & van-accessible space ratio; clear floor space; access aisle; operable-part reach; sidewalk clearance; curb offset; path of travel | Site survey, ADA/ABA guidelines |
| **Demand / Utilization** | EV (BEV+PHEV) registration density; multifamily / no-driveway share; dwell-location type; population density; income/propensity-to-purchase | Registrations, census, parcel land use |
| **Traffic** | AADT; functional class (arterial vs local/residential); proximity to corridor/interchange; transit-rich context | State DOT, FHWA functional class |
| **Visibility / Access** | Lighting; safety perception; signage allowance; ease of ingress/egress; corner vs mid-block | Site survey |
| **Real Estate / Host** | Site control (lease/license/ROW); host willingness; parcel size; existing impervious surface (lowers civil cost); land cost | Assessor, negotiation |
| **Competition** | Proximity to existing/planned public chargers; coverage gap; network reliability of competitors | AFDC station data, NREL |
| **Permitting / Zoning** | Zoning as-of-right vs conditional; streamlined-permit status; encroachment/ROW license (curbside); historic district | Zoning maps, AHJ |
| **Environmental / Equity** | Disadvantaged-community (DAC) status; pollution & health burden; floodplain; environmental justice priority | CalEnviroScreen / EJSCREEN |

The academic MCDM literature groups these into **five "perspectives"** — Demand, Grid, Land Use, Competitive Network, Economic — and weights them with expert panels via AHP/Fuzzy-AHP, then ranks alternatives with TOPSIS or a weighted-sum model (Energies 15(24):9445; ScienceDirect S2772370425000574; RSER S1364032124001783).

---

## 2. Published Scoring Frameworks (with exact weights/points)

### 2.1 SCAG (Southern California Assoc. of Governments) Site-Suitability Scoring — the most concrete public point system
Source: SCAG EV Charging Station Study — Final Scoring Methodology (PDF).

- **Per-criterion 0–10 point scale**, applied per parcel: Highest=10, High=7, Medium=5, Med/Low=3, Low=1, Lowest/N-A=0.
- **36 criteria**, summed (theoretical max ≈ 0–360). **No explicit cross-criterion weight multipliers** — all criteria contribute equally; a 0 on certain land-use/permit criteria excludes the parcel. Highest aggregate scores → further site evaluation.
- **Four scenario "weighting profiles"** re-score the *same* criteria differently by jurisdiction maturity: **Regionwide, Expanding, Progressing, Initiating** cities. ("Expanding" cities *reverse* demand/income scoring to chase equity gaps; "Initiating" cities chase high-income, high-adoption areas.)

Selected exact scoring bands (Regionwide / Expanding / Progressing / Initiating):

| Criterion | Band | R | E | P | I |
|---|---|---|---|---|---|
| Proximity to existing charger | <0.5 mi | 1 | 1 | 1 | 3 |
| | 1–3 mi | 3 | 5 | 10 | 10 |
| | >5 mi | 10 | 10 | 3 | 1 |
| BEV registrations / ZIP | 1–240 | 1 | 10 | 1 | 1 |
| | 961–1,200 | 10 | 1 | 3 | 10 |
| Disadvantaged Community | ≥75% DAC | 10 (all scenarios) | | | |
| Proximity to highway/arterial | <0.25 mi | 10 (all) | | | |
| | >1.0 mi | 1 (all) | | | |
| Near large employer (≥200 emp) | <0.25 mi | 10 (all) | | | |
| Multi-family residential land use | — | 10 (all) | | | |
| Streamlined-permit status | Green/Yellow/Red | 10 / 5 / 1 (all) | | | |
| Within High-Quality Transit Area | yes/no | 10 / 0 (all) | | | |

**Notably excluded by SCAG** (data unavailable): grid capacity, utility-infrastructure distance, public schools. This is the single most important parallel for Sonder — even a sophisticated MPO drops "distance to power" because they lack utility GIS, whereas **Sonder's 3D-scan distance-to-pole/luminaire is a genuine differentiator.**

### 2.2 JointCharging CPO "Multi-Criteria Framework" — five scoring categories
Source: jointcharging.com CPO site-selection & permitting guide (2026). Five categories pros score: **Demand, Grid, Land Use, Competitive Network, Economic.** Key stated finding: *"Transportation-based siting outperforms electrical-node-based siting"* — optimize for travel/demand patterns, not raw proximity to grid infrastructure.

### 2.3 Academic AHP→TOPSIS pattern
Source: Energies 15(24):9445; ScienceDirect S2772370425000574; RSER weighted-sum framework S1364032124001783. Four/five-stage method: (1) define ~14 criteria across 4–5 perspectives; (2) GIS spatial filtering; (3) AHP/Fuzzy-AHP expert weighting; (4) TOPSIS ranking; (5) capacity estimation. This is the rigorous version of what Sonder does heuristically.

---

## 3. Professional Workflow: Desktop → Site Visit → Feasibility

Source: JointCharging CPO guide; Joint Office Public EV Charging Station Site Selection Checklist (driveelectric.gov); Kimley-Horn.

### Stage 1 — Desktop Pre-Screen (rejects on demand/zoning/competition)
Checks: AADT from state DOT; EV-registration density (ZIP); zoning verification; utility territory + initial grid-capacity inquiry; **competitive network audit within a 2-mile radius**; NEVI corridor eligibility; local incentive availability; streamlining-ordinance status. **Go/no-go before lease:** zoning compatible; grid-capacity inquiry returned; AADT + EV density assessed; interconnection timeline estimated.

### Stage 2 — Physical Site Visit (rejects on space/ADA/trench)
Checks: service-entrance location, voltage, phase; **estimated trench length to the EVCS pad**; ADA path-of-travel feasibility; physical constraints (trees, drainage, grade, structures); parking-stall dimensions; photo-document utility markings & transformer location. **Go/no-go before permit:** service-upgrade scope finalized; ADA path documented; demand-charge analysis done; storage-integration decision made.

### Stage 3 — Full Feasibility / Interconnection (rejects on cost/timeline)
Electrical plan (single-line, NEC 625 load calcs); utility interconnection application (parallel track); demand-charge & utilization economics; make-ready cost vs. budget. **Go/no-go before construction:** permits issued; utility work order scheduled; backend tested; inspection scheduled.

**Interconnection gating thresholds (utility-dependent):** transformer at **~60% utilization = feasible, ~90% = upgrade required**; study typically triggered at **50–200 kW**; transformer upgrade adds **+6–12 months**, feeder/substation **+18–36 months**.

---

## 4. Concrete Numeric Thresholds (the table to steal from)

| Parameter | Threshold / value | Source |
|---|---|---|
| **Curb offset** (charger to curb face) | ≤ **10 inches** from face of curb | US Access Board ADA-EV recs |
| **Sidewalk obstruction rule** | Charger NOT in middle 50% of sidewalk adjacent to the parking space | Access Board |
| **Clear floor/ground space** | **30 in × 48 in** minimum | Access Board |
| **Access aisle width** | ≥ **60 in (5 ft)**, full length of space | Access Board |
| **Accessible vehicle space** | ≥ **132 in (11 ft)** wide × **240 in (20 ft)** long (van); standard accessible ≥ 96 in (8 ft) + 60 in aisle | Access Board |
| **Operable-part height** | ≤ **48 in** above floor; reach 15–48 in fwd, 9–54 in side | Access Board / CBC 11B |
| **Accessible-space ratio** (CA model) | ≥ **1 accessible EVCS per 25** total charging spaces; van: 9-ft space + 8-ft aisle (17 ft total) | CBC 11B-228.3 (via JointCharging) |
| **L2 power** | 240V; ~**3–20 kW** (curbside units often **7.4–9.6 kW**) | NYC DOT pilot; Seattle (9.6 kW); JointCharging |
| **DCFC power** | **480V 3-phase**, 150–350 kW | JointCharging; Blink |
| **Per-port hardware cost** | L2 **$1,500–$5,000/port**; DCFC **$20,000–$100,000/port** | Blink / industry |
| **Trenching cost** | **$5–$12 / linear ft** (typical), up to $15/ft long runs | HomeGuide |
| **Make-ready retrofit penalty** | Retrofit costs **3–5× higher** than designed-in | Kimley-Horn |
| **Distribution transformer upgrade trigger** | peak load **>200 kW**; feeder **>3 MW**; substation **>7 MW** | JointCharging |
| **Utilization: loss vs breakeven** | **15% port utilization = loss**; **35% = breakeven within ~3 yrs** | JointCharging |
| **L2 retail sessions/day (healthy)** | **4–8 sessions/day**; profitable L2 needs consistent **30–50% utilization** | Solidstudio / AMPPAL |
| **Demand-charge cost premium** | adds **30–50%** to monthly opex at DCFC; LCOE $0.31→$0.43/kWh (+39%) | JointCharging |
| **Competitive buffer** | audit existing chargers within **2 miles**; GIS filter often drops cells **<4 km** from an existing charger | JointCharging / CARTO |
| **Walk-access coverage target (curbside)** | all residents within a **5-minute walk** of a charger by 2030 (Boston) | Boston.gov |

---

## 5. Curbside / On-Street L2 vs. DC Fast Charging — How Criteria Differ

| Dimension | Curbside / On-street L2 | DC Fast Charging |
|---|---|---|
| **Primary demand driver** | Residential overnight need: EV density × **multifamily / no-driveway share** in walking radius | Through-traffic / corridor AADT, interchange proximity |
| **Dwell time** | **Hours** (overnight; NYC median session **3h49m**) | **20–45 min** |
| **Power / electrical** | 240V single-phase, 7–10 kW; *often attaches to existing utility pole or luminaire* → minimal/no transformer upgrade | 480V 3-phase, 150–350 kW; usually needs transformer/feeder upgrade |
| **Site geometry** | Linear curb frontage, parallel parking, narrow sidewalk; **curb offset ≤10 in** is binding | Off-street lot, pull-in stalls, large pad + cabinet footprint |
| **Traffic class preference** | **Residential / local streets** (where people live & park overnight); transit-rich neighborhoods | Arterials, highway corridors |
| **Visibility** | Less critical (residents know their block) | Critical (impulse/route stops) |
| **Key risks** | ICE blocking (NYC: blocked **~20%** of the time), enforcement, ROW/encroachment permit, pedestrian/ADA conflict | Demand charges, grid capacity, queueing |
| **Economics** | Low per-session revenue; justified by access/equity more than ROI | Throughput-driven revenue; demand-charge-sensitive |
| **Selection emphasis** | Demand + equity + physical feasibility (frontage, pole proximity, obstructions) | Grid capacity + traffic + real estate |

Authoritative siting rule of thumb (JointCharging / Blink): **DCFC = short high-traffic stops (corridors, fleet depots, c-stores); L2 = long-dwell destinations (workplace, hotel, retail w/ grocery anchor) and residential/curbside.** NREL's 2030 network: ~**1 million public L2 ports** targeted at *high-density neighborhoods/offices/retail*, ~**8 million private L1/L2** at homes/multifamily/workplaces, vs only **182,000 DCFC** — i.e., curbside/neighborhood L2 is the dominant volume play.

---

## 6. Demand / Utilization Modeling Factors (curbside-specific)

The strongest empirical evidence is the **NYC DOT Curbside Level 2 Pilot** (100 chargers, 35 locations, 18 months) — directly analogous to Somerville (dense, Northeastern, low off-street parking).

**NYC pilot demand findings:**
- **System utilization 34%**; sites broke the 5% utilization floor after the first 1–2 months.
- **Top-10 sites: 54–69% utilization.** Shared traits: **median household income >50% above city average** AND **EV adoption ≥2× citywide**, transit-rich, near commercial corridors/employment hubs. Nearly half of chargers did **>120 sessions/month**.
- **Bottom-10 sites: <22% utilization** — neighborhoods with **~1/3 the citywide EV ownership**.
- On-street parkers ("no driveway") were the most frequent users; ~**50%** of surveyed users lived in multi-unit dwellings. **44%** cited lack of local charging as the top barrier to going electric.
- Equity caveat (also Seattle, ScienceDirect S0966692325002601): curbside in low-adoption areas *increases access equity* but **utilization will be lower in the near-to-medium term** — so demand score and equity score pull in opposite directions and must be handled as separate axes.

**Amenity / performance signal (Paren, 4,105 DCFC stations Q4 2025 — DCFC but instructive):** no nearby amenity → median **3 sessions/day**; ≥1 amenity → **9/day**; 11+ amenities within 0.1 mi → **28/day**. Grocery-adjacent → **42/day**. Reliability ≥90 score → **17/day** vs **3/day** below 90.

**Core curbside demand variables to model (consensus):**
1. EV (BEV+PHEV) registration density in walk radius (≈¼–½ mile).
2. **Multifamily / no-driveway share** (the defining curbside variable; EVpin and the academic "siting for demand & equity" model both center on it).
3. Dwell-location type (residential overnight vs. destination).
4. Population density.
5. Income / propensity-to-purchase (UCLA-Luskin-style PEV propensity in SCAG).
6. Proximity to transit, commercial corridors, employment hubs.
7. Existing-charger competition / coverage gap.
8. Equity / DAC overlay (treated as a *separate* objective, often with reversed scoring).

---

## 7. Software-Vendor & Consultant Practice (what the tools actually compute)

- **EVpin:** aggregates traffic volume, BEV/PHEV registrations (to ZIP), utility & circuit-level power capacity (select regions), rebates, property/zoning, **nearby multifamily-unit locations**, population density, income, and **competitor utilization** → outputs a **utilization/profitability score**. Toggleable map layers per site type; criteria differ for public vs fleet/workplace.
- **CARTO:** H3-hex GIS model; filters out cells **<4 km** from existing chargers; flags **>97th-percentile population** cells; overlays POIs. Demonstrates the "spatial filter then score" pattern.
- **Kimley-Horn (TREDLite EV):** planned/designed/permitted **>15,000 chargers**; services = site selection → feasibility → design → permitting → utility coordination. Emphasizes transformer lead times and the make-ready 3–5× retrofit penalty.
- **Driivz / Sitetracker:** lifecycle + data-driven placement (traffic, income, tariffs, EV ownership, amenities, ML demand forecast).

---

## 8. Mapping to Sonder — What We Can Compute, Partial, or Must Verify On-Site

| Pro criterion | Sonder data | Status | Notes |
|---|---|---|---|
| **Distance to power asset** (pole/luminaire) | distance to nearest utility pole / luminaire (3D scan) | ✅ **Compute** | Strong differentiator — SCAG and most MPOs *omit* this for lack of utility GIS. Proxy for make-ready trench length. |
| **Make-ready / trench cost** | trench distance × cost/ft estimate | ✅ **Compute (estimate)** | Use $5–$12/ft; flag retrofit 3–5× note. Real cost needs utility coordination → partial. |
| **Usable frontage / stall count** | usable curb frontage length | ✅ **Compute** | Frontage ÷ ~20–22 ft = parallel stalls; check ≥1 stall + ADA geometry. |
| **Cartway width** | road/cartway width | ✅ **Compute** | Feeds ingress/egress + whether equipment encroaches; also a residential-street fit check. |
| **Obstructions** (hydrant, tree, catch basin) | detected obstructions w/ positions | ✅ **Compute** | Penalize/exclude if within stall or ADA clear-space; curb offset ≤10 in & no mid-50%-sidewalk placement. |
| **Pavement condition** | PCI 0–100 + surface type | ✅ **Compute** | Trenching/restoration cost & disruption proxy; good PCI = higher restoration cost if cut, but better install surface — frame explicitly. |
| **Traffic / functional class** | FHWA functional class (residential vs traveler) | ✅ **Compute** | For *curbside L2*, residential/local is a **positive** (overnight residents), inverse of DCFC. |
| **Competition** | nearby existing chargers (public layer) | ✅ **Compute** | Apply 2-mi audit / coverage-gap logic. |
| **Zoning flag** | zoning layer | 🟡 **Partial** | Have flag, not permit-as-of-right vs conditional; ROW/encroachment for curbside is municipal → verify. |
| **EV / demand density** | AADT + road class (public layers) | 🟡 **Partial** | AADT ≠ residential overnight demand. *Need:* BEV/PHEV registration density + **multifamily/no-driveway share** by block — the #1 curbside demand variable. Recommend adding from MA RMV/ACS/parcel data. |
| **ADA accessibility** | obstruction positions + frontage + sidewalk width (partial) | 🟡 **Partial** | Can check curb offset & clear-space geometry from scan; full path-of-travel/cross-slope = verify on site. |
| **Grid / transformer capacity** | — | ❌ **Verify on-site / utility** | Hard gate; even SCAG omits it. Flag every site for utility interconnection inquiry. |
| **Real estate / ROW control / host** | — | ❌ **Verify** | Curbside = municipal license/encroachment; assume city-owned ROW but flag permit status. |
| **Utilization / breakeven** | — (derive from demand proxies) | 🟡 **Partial/model** | Use NYC-pilot analogs: 34% system, 54–69% top sites; flag bottom-quartile risk where EV density low. |
| **Equity / DAC** | — (could overlay EJSCREEN) | 🟡 **Partial** | Recommend adding EJSCREEN/MA EJ block-group overlay as a *separate* axis (don't blend with demand). |

### Recommended Sonder scoring shape (grounded in the above)
1. **Hard go/no-go gates first** (mirror Stage-2 engineering gating): if no power asset within trench-feasible distance, or a hydrant/obstruction occupies the only stall, or frontage < 1 usable stall → flag/reject regardless of demand score.
2. **Then a weighted additive 0–10-per-criterion score** (SCAG pattern), with curbside-tuned weights emphasizing: distance-to-power (make-ready), usable frontage/obstruction-free geometry, residential demand proxy, competition gap, pavement/restoration cost.
3. **Carry equity and grid-capacity as explicit flags, not blended points** — equity because it inverts demand (NYC/Seattle/SCAG-Expanding evidence), grid because Sonder can't measure it (verify-on-site).
4. **Surface a "confidence / verify-on-site" list** per site naming the gates Sonder cannot close (transformer capacity, permit/ROW, full ADA path) — this matches exactly how pros hand off from desktop screen to feasibility study.

---

## Sources

- Joint Office of Energy & Transportation — Public EV Charging Station Site Selection Checklist: https://driveelectric.gov/files/ev-site-selection.pdf
- Joint Office — Public EV Charging Infrastructure Playbook: https://driveelectric.gov/ev-infrastructure-playbook
- Joint Office — Community Charging: Emerging Multifamily, Curbside, and Multimodal Practices (DOE/EE-2806): https://driveelectric.gov/files/community-emobility-charging.pdf
- Joint Office — Permitting & Site Selection Strategies webinar: https://driveelectric.gov/webinars/permitting-site-selection-strategies?view=text-version
- SCAG EV Charging Station Study — Final Scoring Methodology (36-criterion 0–10 point system, 4 scenarios): https://scag.ca.gov/sites/default/files/2024-05/scag_ev_charging_station_study_-_final_scoring_methodology.pdf
- JointCharging — EV Charging Site Selection & Permitting: 2026 Complete Guide (multi-criteria framework, gates, thresholds): https://jointcharging.com/cpo/ev-charging-site-selection-permitting/
- NYC DOT — Curbside Level 2 Charging Pilot Evaluation Report (utilization, top/bottom sites, ICE blocking): https://www.nyc.gov/html/dot/downloads/pdf/curbside-level-2-charging-pilot-evaluation-report.pdf
- Seattle City Light — Curbside Level 2 EV Charging program (9.6 kW, request-based criteria, equity): https://www.seattle.gov/city-light/in-the-community/current-projects/curbside-level-2-ev-charging
- City of Boston — Curbside EV Charging (5-minute-walk-by-2030 target, equity goals): https://www.boston.gov/departments/transportation/curbside-ev-charging
- US Access Board — Design Recommendations for Accessible EV Charging Stations (curb offset, clear space, aisles): https://www.access-board.gov/tad/ev/
- AFDC — ADA Compliance for EV Charging Infrastructure: https://afdc.energy.gov/fuels/electricity-ada-compliance
- AFDC — Procurement & Installation for EV Charging Infrastructure: https://afdc.energy.gov/fuels/electricity-infrastructure-development
- Federal Register — ADA/ABA Accessibility Guidelines; EV Charging Stations (2024-18820): https://www.federalregister.gov/documents/2024/09/03/2024-18820/americans-with-disabilities-act-and-architectural-barriers-act-accessibility-guidelines-ev-charging
- Kimley-Horn — Five Considerations for Planning EV Charging Infrastructure (make-ready 3–5×, transformer lead times): https://www.kimley-horn.com/news-insights/perspectives/considerations-planning-ev-charging-infrastructure/
- Kimley-Horn — TREDLite EV site-selection tool brochure: https://www.kimley-horn.com/wp-content/uploads/2023/09/TREDLiteEV_Brochure_10.2023.pdf
- Kimley-Horn — Eliminating the guesswork of EV charger site selection (15,000+ chargers): https://www.prnewswire.com/news-releases/kimley-horn-eliminates-the-guesswork-of-electric-vehicle-charger-site-selection-301924399.html
- EVpin — site-qualification data points & utilization scoring: https://www.evpin.com/ ; profile: https://chargedevs.com/features/choosing-the-perfect-sites-for-ev-charging-projects-evpins-all-in-one-site-selection-and-design-tool/
- CARTO — Optimizing Site Selection for EV Charging Stations (H3, 4 km filter, 97th-pct demand): https://carto.com/blog/ev-charging-stations-optimizing-site-selection/
- Driivz — Data-Driven Site Selection for Maximum ROI: https://driivz.com/blog/optimal-ev-charger-placement-data-driven-site-selection/
- Paren — Where EV Drivers Charge: 4,105 Stations on Retail Location & Performance (sessions/day by amenity): https://www.paren.app/blog/where-ev-drivers-charge-retail-location-and-performance
- NREL — The 2030 National Charging Network (28M ports; ~1M public L2; 8M private; 182k DCFC): https://docs.nrel.gov/docs/fy23osti/85654.pdf ; DOE FOTW #1334: https://www.energy.gov/eere/vehicles/articles/fotw-1334-march-18-2024-2030-us-will-need-28-million-ev-charging-ports
- NREL — Evaluating EV Public Charging Utilization: https://docs.nrel.gov/docs/fy24osti/85902.pdf
- NREL — EVI-Pro (Electric Vehicle Infrastructure Projection Tool): https://www2.nrel.gov/transportation/evi-pro
- ICCT — Quantifying the EV Charging Infrastructure Gap across U.S. Markets: https://theicct.org/publication/quantifying-the-electric-vehicle-charging-infrastructure-gap-across-u-s-markets/ ; EV CHARGE model docs: https://theicct.github.io/EVCHARGE-doc/versions/v1.0/
- ICCT — EV charging at multifamily homes: barriers, solutions, equity: https://theicct.org/publication/promoting-equity-ev-transition-barriers-and-solutions-to-charging-at-multi-family-homes-us-apr24/
- Energies 15(24):9445 — Multi-Criteria placement of EV charging on highways (AHP/TOPSIS): https://www.mdpi.com/1996-1073/15/24/9445
- ScienceDirect S2772370425000574 — Planning urban EV charging with GIS-based MCDM: https://www.sciencedirect.com/science/article/pii/S2772370425000574
- ScienceDirect / RSER S1364032124001783 — Comprehensive framework for EVCS siting using weighted-sum method: https://www.sciencedirect.com/science/article/abs/pii/S1364032124001783
- ScienceDirect S0966692325002601 — Siting for demand and equity: optimizing Level 2 EV charger placement: https://www.sciencedirect.com/science/article/abs/pii/S0966692325002601
- McKinsey — Can public EV fast-charging stations be profitable in the US?: https://www.mckinsey.com/features/mckinsey-center-for-future-mobility/our-insights/can-public-ev-fast-charging-stations-be-profitable-in-the-united-states
- SolidStudio / AMPPAL — L2 vs DCFC breakeven & utilization (15% loss / 35% breakeven; 4–8 sessions/day): https://solidstudio.io/blog/ev-charging-station-profit-margin ; https://anfuenergy.com/are-ev-charging-stations-profitable/
- Blink — Level 2 vs DC Fast Charging (power, cost-per-port): https://blinkcharging.com/blog/level-2-charging-vs-dc-fast-charging-explained
- SEPA — Disparities in Residential Charging Access: https://sepapower.org/knowledge/disparities-in-residential-charging-access/
