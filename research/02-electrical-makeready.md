# Electrical & Utility Make-Ready Feasibility for EV Charging Sites

*Research brief for Sonder — curbside / on-street Level 2 EV charging site screening (Somerville, MA). Focus: how professionals assess the electrical and utility make-ready feasibility of a charging site, with real numbers. Compiled June 2026.*

---

## 0. Executive framing: why "make-ready" dominates the cost equation

For curbside L2 charging, the **charger hardware is usually NOT the expensive part**. The expensive part is "make-ready" — everything needed to get adequate power *to* the charger location:

- Utility-side: tapping the distribution system, a (possibly new) transformer, primary/secondary conductor, the service drop, and a meter.
- Customer-side: the service panel, the dedicated branch circuit, conduit, conductor, trenching, and surface restoration.

RMI's foundational study found these "soft" and infrastructure costs are *"poorly understood, very hard to quantify, and almost entirely undocumented in the literature,"* and that they — not hardware — are the main brake on deployment (RMI, *Reducing EV Charging Infrastructure Costs*, 2020). The single biggest swing factor on a per-site basis is **distance from the charger to an adequate power source**, which is exactly what Sonder can proxy from street-level scan geometry (distance-to-pole / distance-to-source).

---

## 1. The Electrical Assessment Checklist

A professional site assessment (done by an EPC/installer + utility engineering) evaluates whether the *existing* electrical infrastructure can carry the new charging load, and if not, what must be upgraded. Core checklist items:

### 1.1 Service & capacity
- **Available service capacity / spare amperage.** What is the main service rating (e.g., 200 A, 400 A, 800 A, 1,200 A, up to 4,000 A) and how much *headroom* is unused after existing loads? (SafetyCulture / JET Charge site-assessment template: document "transformer and MSB ratings, main switch, busbar chassis, spare capacity.")
- **Existing load measurement.** Either an NEC load calculation or a metered peak-demand reading (utilities increasingly want 12 months of interval data) to know real spare capacity, not nameplate.
- **Panel / switchgear.** Loadcenter vs. service-entrance switchgear; available breaker spaces; bus rating. Multi-port DCFC sites need switchgear, not residential-style loadcenters (National EV Charger Authority).

### 1.2 Voltage & phase
- **Single-phase vs three-phase.** L2 runs on **single-phase 208 V or 240 V**; DCFC almost always needs **three-phase 480 V** (or 208 V three-phase for low-power units). Phase availability at the candidate location is a hard gating factor. (Blink Charging; National EV Charger Authority)
- **Voltage at the point of connection.** Residential/secondary 120/240 V split-phase from a center-tapped pole transformer; commercial 208Y/120 or 480Y/277; distribution primary at ~4 kV–15 kV (needs a transformer to step down). (Mike Holt forum; National EV Charger Authority)

### 1.3 Transformer
- **Transformer capacity & headroom.** Is the serving distribution transformer large enough to add the new continuous load? Public EV charging typically wants three-phase, oil-immersed transformers; adding load may exceed transformer thermal limits and force replacement (Utility Dive / WoodMac; ScienceDirect on distribution-transformer EV loading).
- **kVA sizing.** Single-phase pole/pad transformers for residential L2 are typically ≤100 kVA. DCFC > 150 kW often needs a **dedicated pad-mount transformer**; > 250 kW may need medium-voltage service stepping down from 4/12/15 kV. (Daelim; National EV Charger Authority)

### 1.4 Load calculation & demand factors (NEC)
- **Continuous-load rule (NEC 625.42 / 625.41).** EVSE is a *continuous load*; branch circuit, conductors, and breaker must be sized at **125% of the EVSE rated current**. Examples: 32 A EVSE → 40 A breaker; 40 A EVSE → 50 A breaker; 48 A EVSE → 60 A breaker. (getneocharge; Kopperfield)
- **Energy Management Systems (EVEMS, NEC 625.48).** With an EVEMS you size the service/feeder to the *managed maximum demand* rather than the sum of nameplates — letting more ports share limited capacity. Under **NEC 2026**, when a conforming EVEMS actively manages the load, the 125% continuous multiplier no longer applies. This is the key lever for fitting curbside charging onto constrained circuits. (SparkShift; getneocharge)
- **Demand factors.** Multiple ports rarely all charge at full power simultaneously; load studies apply diversity/demand factors (or rely on EVEMS) so the service isn't sized to the worst-case sum.

### 1.5 Documentation deliverable
A site assessment / load study typically produces: a **single-line diagram (SLD)**, panel schedule, measured/calculated peak demand, phase and amperage at the connection point, spare-capacity finding, the proposed circuit/conductor/breaker sizing, a site plan showing charger location and the cable run/trench path, and a make-ready scope + cost estimate. (SafetyCulture EV site-survey template; Capital Buildcon NEC 625 load/panel schedule template)

---

## 2. Utility Make-Ready & Interconnection

### 2.1 What "make-ready" means
**Make-ready** = the electrical infrastructure that brings power to the point where the EVSE will be installed, *short of* the charger itself. National Grid (MA) defines make-ready infrastructure as including: *"a distribution primary lateral service feed, a transformer and transformer pad, a new service meter, a new service panel, and conduit and conductor necessary to connect each piece of equipment."* (National Grid MA Public/Workplace program)

### 2.2 Line-side / load-side and the meter boundary
- The **utility side ("line-side"/utility-side make-ready)** is everything from the distribution system up to and including the meter — the primary lateral, transformer, transformer pad, and service drop. The **customer side ("load-side"/customer-side make-ready)** is from the meter onward — service panel, conduit, conductor, and the charger circuit.
- In MA, utilities *build and own the utility-side* make-ready and *reimburse* the host for some/all of the customer-side. (National Grid: *"constructing upgrades on the utility side of the meter and reimbursing the site host."*)

### 2.3 Primary vs secondary; new service vs upgrade
- **Secondary connection** (existing 120/240 V or 208/480 V secondary already present near the site) is cheapest — you tap existing secondary or a nearby transformer.
- **Primary connection / new service** (no adequate secondary nearby) requires a **new transformer** and primary lateral — much more expensive and slower.
- **Upgrade vs new service:** upgrading an existing service (bigger panel/transformer) is cheaper than a brand-new service drop and meter. RMI notes grid upgrades are "future-proofed by type" — once a transformer/feeder/substation upgrade is done, the same type isn't needed again for the station's life.

### 2.4 Process, queue & who pays
- **Process (MA, Eversource 7 steps):** pick a qualified installer → feasibility review by the utility's EV + Distribution Engineering teams → design/interconnection application → utility builds utility-side make-ready → customer/installer builds customer-side + installs EVSE → inspection → utility issues Permission to Operate (PTO) / energizes. (Eversource MA rebates process)
- **Interconnection studies / queue:** grid-connected projects undergo impact studies before construction to determine required upgrades; this "can take a year or more." Utilities lack tools to manage large queues of high-power (>50 kW–5 MW) EV requests on low-capacity networks — DOE's i2x/iQMS program is awarding **$11.2M across 25 utilities** specifically to speed these timelines. (DOE Joint Office; Microgrid Knowledge)
- **Who pays:** Utility funds line-side make-ready (in MA programs, up to 50–100% depending on program/segment). Customer pays for the charger and may be reimbursed for customer-side work. Applicants generally pay for upgrades to bring capacity *into* their facility plus their own switchgear. (National Grid; Utility Dive)

### 2.5 Massachusetts program specifics (most relevant to Sonder)
- **Eversource (MA, Phase II, DPU-approved Dec 30 2022; ~$188M, 4 yr):** up to **100% of the infrastructure (make-ready) cost** to bring electric service to L2/DCFC sites. Make-ready *"may include the trenching, conduits, wires, meter, and if necessary, a transformer."* Additional rebates for some segments: up to 100% for L2 stations; **up to $80,000 per port for DCFC** at light-duty fleet/workplace/public/MUD (5+ unit) sites. (Eversource; Green Energy Consumers; PowerOptions)
- **National Grid (MA):** funds **up to 50% of make-ready** for approved L2 projects and **up to 50% of eligible L2 EVSE hardware.** Public DCFC EVSE rebate cap **$100,000/project**; Public Fleet cap **$400,000/project**. L1 ports eligible for customer-side infrastructure incentives in long-dwell scenarios only (no EVSE rebate). (National Grid Public/Workplace)

### 2.6 The long-lead-time problem (transformers)
- **Distribution transformers:** lead times improved from a >100-week peak in 2023 to ~30 weeks (US) by mid-2025 — but **pad-mount three-phase** units (what public DCFC needs) recorded *increasing* lead times in Q2 2025 and remain the bottleneck. Vendor quotes commonly cite **16–24 weeks** for pad-mount distribution transformers, with rush fees of 10–25%. (PowerMag; Utility Dive/WoodMac; transformer4u/Daelim)
- **Power transformers:** ~128 weeks; GSUs ~144 weeks (Q2 2025); switchgear ~44 weeks.
- **Prices since 2019:** power transformers +77%, distribution transformers up to +95% for some classes, MV switchgear +50%, circuit breakers +47%. Demand vs supply: power-transformer demand +119% / distribution +34% since 2019, while supply capacity grows only ~3–4%/yr against 7–9% demand growth. EV charging is named as a competing demand driver alongside data centers. (PowerMag)
- **Practical takeaway:** *if a candidate needs a new/replacement transformer, the project timeline is dominated by transformer procurement (months), not construction.* Sites that can run off existing secondary avoid this entirely.

---

## 3. Cost Breakdowns (real figures)

### 3.1 Trenching, conduit & conductor ($/linear foot) — the distance-driven core

| Item | Cost ($/linear ft) | Notes / source |
|---|---|---|
| Trench in dirt/soil (hand, 18") | $4–$12/ft | Labor only; DEVCO / HomeGuide |
| Trench in dirt/soil (machine) | $5–$15/ft | Utility trenching baseline; DEVCO |
| Trench through **asphalt** | $12–$24/ft | Surface type roughly doubles cost; DEVCO |
| Trench through **concrete** | $15–$30/ft | DEVCO |
| Combo (dirt + asphalt/concrete crossing) | $18–$36/ft | DEVCO |
| **Surface restoration / repaving add-on** | +$4–$12/ft | T-cut, grind, repave; DEVCO/HomeGuide |
| Sawcut asphalt (by depth) | $1–$10/ft | Shallow $1–3, moderate $2–5, deep $4–10; We Love Paving |
| EV-specific trenching (industry rule) | $15–$30/ft | EnergySage/installer guides for EV make-ready |
| Conduit (materials) | +$1–$2/ft | Plus labor for bend/mount/pull; Angi/Accutech |
| Electrical run (wire + conduit, mat'l+labor) | $10–$20/ft | EVquoter / KSB Electric |
| **Directional bore (HDD) instead of trench** | varies | Avoids surface restoration entirely — "saves thousands" where pavement crossing would otherwise be required; L&N Zimmerman |

**Worked distance examples (residential-scale, illustrative):** 50 ft run ≈ $500–$1,000; 100 ft run ≈ $2,000–$4,000 (HomeGuide). EnergySage: distance from panel is *"the single biggest cost driver"*; a 60–80 ft interior run can add $1,000–$1,500.
**NEC burial depth:** 18–24 in for conduit-protected cable. Long runs also force **conductor upsizing for voltage drop**, adding wire cost beyond the linear-foot rate.

### 3.2 Service / panel / transformer upgrades

| Item | Typical cost | Source |
|---|---|---|
| Add a new branch circuit (existing panel) | $60–$150 | EnergySage |
| Install a sub-panel | $500–$1,500 | EnergySage |
| **Main service upgrade 100→200 A (residential)** | $1,500–$4,500 (some markets $2,000–$6,000) | EnergySage / HomeAdvisor / regional |
| **Upgrade to 400 A service** | $8,000–$12,000 | HomeAdvisor / GreenBuildingAdvisor |
| New meter + service drop | $100–$650 | HomeAdvisor |
| Permits & inspection | $50–$800 (avg ~$297) | EnergySage |
| **Pad-mount three-phase transformer, 75 kVA (equipment)** | $16,000–$26,000 | npcelectric / transformer4u |
| Distribution transformer 15–500 kVA (equipment range) | $1,500–$20,000 | Daelim |
| Three-phase vs single-phase premium | +40–70% same kVA | transformer4u |
| **On-site transformer upgrade for a DCFC site (all-in assumption)** | ~$100,000 | RMI / NREL modeling assumption |

### 3.3 Charger hardware (for contrast — usually the *smaller* line item for curbside L2)

| Charger | Hardware cost | Source |
|---|---|---|
| Residential L2 unit | $300–$800 (some $100–$800) | EnergySage |
| L2 install (labor only, ex-equipment) | $800–$3,000 (US avg ~$2,442) | EnergySage |
| DCFC 50 kW | ~$20,000–$35,800 (avg $28,401); ~$30,000 typical | RMI (Nelder & Rogers) |
| DCFC 150 kW | ~$81,000 | RMI |
| DCFC 350 kW | ~$140,000 | RMI |

### 3.4 Order-of-magnitude total make-ready ranges

- **Curbside L2 off existing secondary (best case):** dominated by trench distance + a modest circuit. Pole-mounted chargers can cut installation cost **55%, up to 70%, vs ground-mounted** (mounting up the pole, less concrete, shorter run). (WRI)
- **Curbside L2 needing a new/upgraded transformer:** add transformer ($16k–$26k equipment + install + months of lead time) → can dwarf the charger.
- **DCFC:** dedicated 480 V three-phase service, switchgear (1,000–4,000 A at 480 V for multi-port), and frequently a dedicated/MV transformer; on-site transformer upgrades modeled at ~$100k; utility-side lead times **6–24 months** for >500 kW aggregate. (National EV Charger Authority; NREL/RMI)

**Distance-to-power is the dominant, most predictable swing variable.** Everything else (transformer, phase, panel) is a step-function: either the existing infrastructure has the headroom (cheap) or it doesn't (expensive + slow).

---

## 4. Curbside-Specific Electrical Considerations

This is the crux for Sonder, because curbside sites interconnect at the **nearest utility pole or streetlight**, not a building service.

### 4.1 Utility pole vs streetlight pole — a critical distinction
- **Streetlight poles typically carry only ~110–120 V** on a lighting circuit — **enough for Level 1 only, not Level 2.** (Utility Dive, KC pilot analysis)
- **Utility poles carry distribution voltage (thousands of volts / ~4 kV primary)** and have (or can get) a transformer dropping to 120/240 V split-phase — *this* is what supports **Level 2 (208–240 V)**. A center-tapped pole transformer gives two 240-V-apart hots + neutral (120 V each leg). (Utility Dive; Mike Holt forum)
- **Implication:** a "usable" pole for curbside **L2** is generally a **utility/distribution pole with an existing or addable secondary**, or a streetlight that has been *upgraded* to a higher-capacity feed. A bare LED streetlight head alone ≈ L1.

### 4.2 Tapping streetlight circuits — why it's limited
- **LED-conversion headroom:** converting HID streetlights to LED frees energy capacity that often *wasn't* reduced on the circuit, creating a "gap" that can power a charging port. This is the main enabler of streetlight charging. (Utility Dive; WRI)
- **But the limits are real:**
  - **Low voltage** (120 V) → Level 1 speeds only unless the circuit is upgraded.
  - **Night-only energization:** many lighting circuits are only powered at night (photocell/contactor control), so daytime charging needs upgrades to keep the circuit live. (Utility Dive — KC poles "only carry power at night… would need upgrades to enable daytime charging.")
  - **Shared / un-metered circuits:** lighting circuits are often unmetered and shared across many poles, so adding a charger requires a **dedicated meter** and a way to separate charging energy from lighting energy.
  - **Limited spare capacity:** the freed LED headroom is small — supports a low-power port, not multiple high-power ports.
- **Pole-selection criteria used in practice (KC pilot):** screened streetlights by **voltage, control mechanism (night-only vs always-on), and proximity to the curb.** Of ~300 candidate sites, only **30–60** were planned for install "depending on final costs." (Utility Dive)

### 4.3 Metering & secondary connections
- Curbside chargers need their own **revenue meter** (the charging energy must be billed separately from municipal lighting). National Grid make-ready explicitly includes "a new service meter."
- **Secondary connection** (tap existing 120/240 V or add a small pole transformer) is the cheap path; needing a **new transformer + primary tap** is the expensive path.

### 4.4 What makes a pole "usable" for curbside L2 (synthesis)
1. It is (or is near) a **distribution pole with secondary** at 208/240 V — not a bare 120 V lighting circuit.
2. There is **transformer/secondary capacity headroom** to add a continuous L2 load (≈7–19 kW per port).
3. The circuit is **always-on** (or upgradeable to always-on).
4. A **dedicated meter** can be added.
5. The pole is **close to the curb / parking** so the cable/trench run to the charger is short.
6. Mounting the charger up the pole is structurally feasible (and yields the 55–70% cost savings).

---

## 5. How an Electrical Site Assessment / Load Study Is Documented (the deliverable)

A professional make-ready feasibility package typically contains:
1. **Single-line diagram (SLD)** of existing + proposed.
2. **Panel schedule / switchgear inventory** with bus rating, breaker spaces, existing loads.
3. **Load calculation** (NEC 220 + 625) or **metered peak demand** (12-mo interval data), showing spare capacity; EVEMS managed-demand basis if used.
4. **Point of connection details:** voltage, phase, available amperage; transformer kVA and headroom.
5. **Conductor/conduit/breaker sizing** at 125% continuous (NEC 625.42) and voltage-drop check for the run length.
6. **Site plan** with charger location, cable route, **trench path + length + surface types** (the distance figure that drives cost).
7. **Make-ready scope** split utility-side vs customer-side, with **cost estimate and lead-time risks** (esp. transformer).
8. **Interconnection application** + utility study/PTO milestones.

---

## 6. Mapping to Sonder

Sonder screens curbside sites from street-level 3D scan data, estimating make-ready cost largely from **distance to the nearest pole/source**. Here is what we can credibly *proxy* from geometry vs. what we must *flag for on-site/utility verification*.

### 6.1 What we CAN proxy from the scan (distance-to-pole + visual features)
- **Trench / cable-run length** → the dominant, most predictable cost driver. Multiply distance by the $/ft band for the observed surface type.
- **Surface type along the run** (asphalt road vs concrete sidewalk vs dirt/grass) → selects the $/ft band ($5–$15 dirt vs $12–$24 asphalt vs $15–$30 concrete) and restoration add-on (+$4–$12/ft). 3D scans see pavement type directly.
- **Pole type heuristic** → distinguish a **utility/distribution pole** (has transformer cans, primary crossarms, multiple wires → likely L2-capable) from a **bare streetlight** (single luminaire, thin pole → likely L1-only / needs upgrade). This is visible in scan imagery.
- **Presence of an existing pole-mount transformer** near the candidate → strong positive signal that secondary L2 power is available cheaply (no new-transformer lead time).
- **Proximity of charger location to curb/parking** and mountability up the pole → flags the 55–70% pole-mount cost-savings opportunity.
- **Whether a pavement crossing is required** (run must cross the road) → flag for directional-bore vs open-trench cost.

### 6.2 What we MUST flag as "verify on-site / with utility" (NOT inferable from geometry)
- **True available service/transformer capacity & headroom** — requires utility data or metered load; nameplate ≠ spare capacity. *Always a verify-on-site flag.*
- **Single vs three-phase** at the pole — can't be reliably read from a scan; gates DCFC entirely and affects some L2. Verify with utility.
- **Voltage at the connection point** (120 V lighting vs 240 V secondary vs primary needing a transformer) — infer a *likelihood* from pole type, but confirm.
- **Night-only vs always-on streetlight circuit** — only known from utility control records.
- **Whether a new/replacement transformer is needed** — the biggest schedule risk (16–24+ week lead time). Geometry can't see transformer loading.
- **Metering feasibility / circuit ownership** (municipal lighting vs utility distribution).
- **Interconnection queue & utility make-ready cost share** (Eversource up to 100%; National Grid up to 50%) — program- and case-specific.

### 6.3 Suggested Sonder scoring signals
- **Green (low make-ready):** distribution pole with visible transformer ≤ short distance, soft-surface run, no road crossing → cheap secondary L2 tap.
- **Yellow:** longer run and/or pavement crossing (higher trench $/ft + restoration), or streetlight that may need a circuit upgrade.
- **Red / verify:** bare 120 V streetlight (L1-only), long run across concrete, or any indication a new transformer/phase change is needed (→ months of lead time + step-function cost). Always pair the geometry score with a "utility-capacity unknown" flag.

---

## Sources

1. Green Energy Consumers — Massachusetts EV charging / DPU: https://blog.greenenergyconsumers.org/blog/more-ev-charging-in-mass.-say-yes-at-the-dpu and https://blog.greenenergyconsumers.org/blog/400-million-for-electric-car-charging-in-massachusetts
2. Eversource — MA EV Charging Rebates Process (7 steps, make-ready scope): https://www.eversource.com/business/save-money-energy/clean-energy-options/electric-vehicles/business-ev-charging-rebates/massachusetts-ev-charging-rebates-process
3. PowerOptions — Eversource MA Make-Ready Program summary: https://poweroptions.org/massachusetts-make-ready-program/
4. National Grid (MA) — Public/Workplace EV Programs (make-ready definition, 50% funding, rebate caps): https://www.nationalgridus.com/MA-Business/Commercial-and-Fleet-EV-Programs/Public/Public-Workplace-Programs
5. National Grid (MA) — Make-Ready Program application requirements (PDF): https://www.nationalgridus.com/media/pdfs/bus-ways-to-save/cm8215-ev-application-requirement-ma.pdf
6. Mass.gov — DPU EV charging resources: https://www.mass.gov/info-details/dpus-electric-vehicle-charging-resources
7. RMI — *Reducing EV Charging Infrastructure Costs* (Nelder & Rogers, 2020): https://rmi.org/insight/reducing-ev-charging-infrastructure-costs and PDF https://rmi.org/wp-content/uploads/2020/01/RMI-EV-Charging-Infrastructure-Costs.pdf
8. CleanTechnica — coverage of the RMI report: https://cleantechnica.com/2020/01/22/reducing-ev-charging-infrastructure-costs/
9. NREL — Distribution Transformer Demand report (FY25): https://docs.nrel.gov/docs/fy25osti/92076.pdf
10. PowerMag — *Transformers in 2026: Shortage, Scramble, or Self-Inflicted Crisis?* (lead times, price increases, demand/supply): https://www.powermag.com/transformers-in-2026-shortage-scramble-or-self-inflicted-crisis/
11. Utility Dive — Transformer supply bottleneck (WoodMac lead-time data): https://www.utilitydive.com/news/electric-transformer-shortage-nrel-niac/738947/
12. transformer4u — Padmount transformer cost guide by kVA: https://transformer4u.com/padmount-transformer-cost/
13. npcelectric — 75 kVA 3-phase transformer pricing: https://www.npcelectric.com/news/75-kva-3-phase-transformer-specifications-price-applications-complete-buying-guide.html
14. Daelim — EV charging station transformers / price list: https://www.daelimtransformer.com/guide-to-ev-charging-station-transformers.html
15. WRI — *Pole-Mounted EV Charging: Preliminary Guidance* (55–70% savings): https://www.wri.org/research/pole-mounted-electric-vehicle-charging-preliminary-guidance
16. Utility Dive — Kansas City streetlight-mounted EV charger pilot (120 V = L1, night-only circuits, pole criteria): https://www.utilitydive.com/news/kansas-city-streetlight-mounted-ev-charger-pilot-aims-for-equity-accessibi/604445/
17. pv magazine USA — Kansas City streetlight EV charger pilot: https://pv-magazine-usa.com/2021/08/05/kansas-city-pilots-streetlight-mounted-ev-chargers/
18. Metropolitan Energy Center — Streetlight EV Charging (23 chargers, LED spare capacity): https://metroenergy.org/current-projects/streetlight-ev-charging/
19. UBC Sustainability — On-Street EV Charging from Light Poles (Puentes): https://sustain.ubc.ca/sites/default/files/2019-60_On-Street%20Electric%20Vehicle%20Charging_Puentes.pdf
20. National EV Charger Authority — DC Fast Charging Electrical Infrastructure Requirements (tiers, kVA, switchgear, 6–24 mo lead): https://nationalevchargerauthority.com/dc-fast-charging-electrical-infrastructure
21. Blink Charging — Electrical Requirements for L2 and DCFC: https://blinkcharging.com/blog/what-are-the-electrical-requirements-for-level-2-and-dc-fast-charging-stations
22. getneocharge — NEC 625 Continuous Load (125% rule): https://getneocharge.com/a/blog/nec-625-continuous-load-125-percent-rule-ev-charging
23. SparkShift — NEC 2026 EV charger changes (625.42, 625.48 EVEMS): https://sparkshift.app/learn/nec-2026/ev-charger-changes
24. Kopperfield — EV chargers and load calculations for electricians: https://www.kopperfield.com/blog/ev-charger-load-calc
25. Capital Buildcon — EV Charger Load & Panel Schedule Template (NEC 625): https://capitalbuildcon.com/ev-charger-load-panel-schedule-nec-625/
26. SafetyCulture — EV site survey / JET Charge site-assessment templates: https://safetyculture.com/library/energy-and-utilities/ev-site-survey-ykxtk0dwqvowqyfz
27. DEVCO — Utility Trenching Cost (per-foot by surface, restoration): https://developmentandengineering.com/utility-trenching-cost/
28. HomeGuide — Trenching cost per foot: https://homeguide.com/costs/trenching-cost
29. We Love Paving — Asphalt cutting cost per linear foot: https://www.welovepaving.com/the-cost-of-asphalt-cutting-per-linear-foot-what-to-expect/
30. L&N Zimmerman — Bore (HDD) vs Trench cost: https://lnzimmermanboring.com/blog/cost-to-bore-hdd-vs-trench/
31. EnergySage — EV charger installation cost (distance as biggest driver, panel upgrade costs): https://www.energysage.com/ev-charging/how-much-does-ev-charger-installation-cost/
32. EVquoter — "What is electrical run?" ($/ft run): https://evquoter.com/learn/what-is-run
33. HomeAdvisor — Electrical panel upgrade cost 2025: https://www.homeadvisor.com/cost/electrical/upgrade-an-electrical-panel/
34. DOE Joint Office of Energy & Transportation — Utility programs / iQMS ($11.2M queue mgmt): https://driveelectric.gov/utility-programs and https://driveelectric.gov/news/iqms-funding-opportunity
35. Microgrid Knowledge — Interconnection queues getting longer: https://www.microgridknowledge.com/grid/article/55021683/no-fast-passes-in-the-waiting-line-interconnection-queues-are-getting-longer
36. INL — EV Charging Infrastructure Energization: An Overview of Approaches (PDF): https://inldigitallibrary.inl.gov/sites/sti/sti/Sort_151131.pdf
37. AFDC / DOE — Procurement and Installation for EV Charging Infrastructure: https://afdc.energy.gov/fuels/electricity-infrastructure-development
38. Mike Holt forum — pole transformer secondary / 240 V split-phase, EV transformer sizing: https://forums.mikeholt.com/threads/ev-chargers-service-calculation.2582188/
