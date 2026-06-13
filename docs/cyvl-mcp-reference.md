# Cyvl MCP | Infrastructure Data API Reference

Complete reference for the Cyvl Model Context Protocol (MCP) server — a read-only API exposing municipal infrastructure data (pavement condition, traffic signs, above-ground assets, road markings, and street-level imagery) for US cities.

**Server:** `https://i3.cyvl.app/mcp` (HTTP transport)
**Auth:** OAuth 2.1 Bearer — every tool requires authentication
**Access:** Read-only. There are no create/update/upload tools; you cannot write data back into Cyvl through this server.

---

## Quick Start

```bash
# Add the server to Claude Code
claude mcp add --transport http cyvl https://i3.cyvl.app/mcp

# Verify health
claude mcp list
# cyvl: https://i3.cyvl.app/mcp (HTTP) - ! Needs authentication
```

Then authenticate inside Claude Code:

```
/mcp        →  select "cyvl"  →  Authenticate   (opens browser OAuth flow)
```

Once OAuth completes the temporary `authenticate` / `complete_authentication` tools drop off and the full 20-tool surface becomes available.

Canonical first call — **always** start here, every other tool needs a `project_id`:

```
list_projects()
```

---

## Mental Model

Cyvl organizes everything under a **project** (one city/region delivery). A project exposes one or more **modules** of data. You discover projects, geocode a place name to coordinates, then run spatial queries scoped to a project + a bounding box / radius / polygon.

| Module | What it holds | Primary tools |
|--------|---------------|---------------|
| **pavement** | PCI condition scores, segment aggregations, distress details, inspection cells | `list_pavement_scores`, `list_pavement_segments`, `list_distresses`, `list_inspection_cells`, `get_pavement_score_detail` |
| **signs** | Traffic sign inventory with MUTCD codes, categories, conditions | `list_signs`, `get_sign` |
| **above_ground_assets** | Trees, poles, hydrants, manholes, signals, and other above-ground infrastructure | `list_above_ground_assets`, `get_above_ground_asset` |
| **markings** | Striping & pavement markings with line types, colors, conditions | `list_markings`, `get_marking` |
| **imagery** | Street-level image search via natural language (Qdrant + Voyage AI embeddings) | `search_imagery`, `search_imagery_by_image`, `get_asset_imagery` |

Cross-cutting: `geocode_location`, `assess_infrastructure`, `query_infrastructure`, `get_asset`, `get_project_overview`.

---

## Core Workflow

```
1. list_projects()                          → discover projects, get project_id
2. get_project_overview(project_id)         → project-wide inventory & stats (no spatial filter)
3. geocode_location("Davis Square, MA")     → place name → coords + bbox
4. list_*(project_id, radius/bbox/polygon)  → spatial query for a layer
5. get_*(id, project_id)                    → full detail for one feature
6. search_imagery(query, project_id)        → street-level photos (imagery projects only)
```

One-call shortcut for a location assessment (combines geocode + spatial query + PCI distribution + asset inventory):

```
assess_infrastructure(location="Davis Square, Somerville MA", project_id=...)
```

---

## Spatial Filter Rules

Three interchangeable spatial filters are accepted by spatial tools:

| Filter | Shape | Format |
|--------|-------|--------|
| `bbox` | Bounding box | `[west, south, east, north]` in WGS84 |
| `radius` | Circle | `{ "lat": 42.37, "lng": -71.09, "meters": 250 }` |
| `polygon` | Arbitrary area | GeoJSON `Polygon` (`{ "type": "Polygon", "coordinates": [[[lng,lat],…]] }`) |

**Spatial filter REQUIRED by:** `list_pavement_scores`, `list_pavement_segments`, `list_distresses`, `list_inspection_cells`, `list_above_ground_assets`, `list_markings`, `list_signs`, `query_infrastructure`.

**Spatial filter NOT required by:** `list_projects`, `get_project_overview`, `geocode_location`, `assess_infrastructure`, `get_asset`, `get_sign`, `get_above_ground_asset`, `get_marking`, `get_asset_imagery`, `search_imagery`, `search_imagery_by_image`.

> `geocode_location` returns a tight ~300 m bbox. For neighborhood-scale queries, widen it (e.g. ±0.015° per side) or pass a custom polygon. Never substitute coordinates from memory — always geocode.
>
> **Radius caps differ by tool.** The `radius` object's `meters` field on the spatial `list_*`/`query_infrastructure` tools allows up to **50,000 m (50 km)**. The separate `radius_m` scalar on `geocode_location` / `assess_infrastructure` caps at **5,000 m**; on `search_imagery` it's only bounded `> 0`.

---

## Pagination Rules

| Query family | Mechanism | How to page |
|--------------|-----------|-------------|
| Spatial `list_*` | Cursor-based | Pass `cursor` from the previous response; repeat until `has_more=false` |
| `search_imagery` / `_by_image` | Cache-based | Pass `search_id` + `page` from a previous response |
| `list_projects` | Offset-based | Pass `offset` + `limit` |

**Critical caveat — counts are unreliable.** Spatial `list_*` responses return `total_count` (observed `null` in practice); the server documents a `total_count_estimate` for *planning* page counts, but it may also be null/absent. Never trust either for exact figures. If `n == limit` and `has_more=true`, the API cap was hit and your result is a **lower bound only** — paginate to `has_more=false` before computing any aggregate (averages, %, totals).

Default / max page sizes per tool:

| Tool | Default `limit` | Max |
|------|------|-----|
| `list_projects` | 50 | 200 |
| `list_signs` | 50 | 200 |
| `list_above_ground_assets` | 50 | 200 |
| `list_markings` | 50 | 200 |
| `list_pavement_scores` | 25 | 200 |
| `list_pavement_segments` | 50 | 200 |
| `list_distresses` | 20 | 200 |
| `list_inspection_cells` | 10 | 200 schema — server caps each page to **20** regardless |
| `query_infrastructure` | 50 | 200 |
| `search_imagery` / `_by_image` | 25 (`page_size`) | 200 |

---

## PCI Scoring System (ASTM D6433)

Pavement Condition Index runs **0 (worst) → 100 (best)**.

| Label | Score range | Midpoint | Policy meaning |
|-------|-------------|----------|----------------|
| Failed | 0–10 | 5 | Reconstruction candidate (critical) |
| Serious | 11–25 | 18 | Reconstruction candidate (critical) |
| Very Poor | 26–40 | 33 | Structural intervention (needs major repair) |
| Poor | 41–55 | 48 | Mill-and-overlay (needs preventive) |
| Fair | 56–70 | 63 | Routine maintenance (acceptable) |
| Satisfactory | 71–80 | 75.5 | Routine maintenance (acceptable) |
| Good | 81–85 | 83 | Acceptable |
| Very Good | 86–90 | 88 | Acceptable |
| Excellent | 91–100 | 95 | Acceptable |
| Not Scored | — | — | No survey |

**Policy thresholds:**
- **Critical** — PCI < 25 (Failed + Serious) → immediate reconstruction
- **Needs major repair** — PCI < 40 (Failed + Serious + Very Poor) → structural intervention
- **Needs preventive** — PCI 40–55 (Poor) → mill-and-overlay
- **Acceptable** — PCI ≥ 56 (Fair or better) → routine maintenance

**Length-weighted average (use this, not a simple mean):**

```
weighted_avg_PCI = Σ(midpoint × total_length_ft) / Σ(total_length_ft)
```

Length weighting is more accurate for policy because one long Failed segment impacts more road-miles than many short ones. For outlier detection, compare an area's `%(PCI<40)` against the citywide baseline; flag areas >2× the citywide rate.

---

# Tool Reference

20 tools. Conventions below: **R** = spatial filter required, **—** = not required.

## Discovery & Overview

### `list_projects` — ENTRY POINT
Lists all projects accessible to your org. Every other tool needs a `project_id` from here.

| Param | Type | Notes |
|-------|------|-------|
| `name` | string | Fuzzy search by city |
| `module` | string | Filter by module (`Pavements`, `TrafficSigns`, `Trees`, …) |
| `has_embeddings` | bool | `true` = imagery-searchable projects only |
| `archived` / `is_processing` | bool | Status filters |
| `delivered_before` / `delivered_after` | ISO-8601 | Delivery date bounds |
| `service_tier` | string | Filter by tier |
| `project_id` | string | Look up a single project by UUID |
| `limit` / `offset` | int | Pagination (max 200) |

Key response fields: `id`, `name`, `modules[]`, `length_miles`, `embedding_count` (>0 ⇒ imagery searchable), `bounds` `[w,s,e,n]`, `location{city,stateCode,coordinates}`, `date_delivered`, `service_tier`.

### `get_project_overview` — data inventory
Project-wide stats; no spatial filter. Call after `list_projects` before spatial queries.

| Param | Type | Notes |
|-------|------|-------|
| `project_id` | string | **required** |
| `sections` | enum[] | Subset of `pci`, `signs`, `assets`, `markings`, `inventory` (default: all) |

Returns: `pci_distribution` (segment_count + total_length_ft per label), `asset_inventory` (counts by type), `sign_statistics`, `above_ground_asset_statistics`, `markings_statistics`.

### `geocode_location` — place → coords
| Param | Type | Notes |
|-------|------|-------|
| `location` | string | **required** — place name or address (max 200 chars) |
| `radius_m` | number | Bbox radius in meters (default 300, max 5000) |

Returns `lat`, `lon`, `display_name`, `bbox` `[w,s,e,n]`, `radius_m`. Uses Nominatim — single best match, accuracy varies for ambiguous names.

### `assess_infrastructure` — one-call location assessment
Combines geocode + spatial query + PCI distribution + asset inventory. Takes 3–5 s.

| Param | Type | Notes |
|-------|------|-------|
| `location` | string | **required** |
| `project_id` | string | **required** |
| `radius_m` | number | Default 300, max 5000 |
| `asset_types` | enum[] | `pavement`, `sign`, `above_ground_asset`, `distress`, `striping`, `centerline` |
| `include_imagery` | bool | Include image search count |

## Cross-Layer

### `query_infrastructure` — all layers at once `[R]`
Query across layers with one spatial filter. Returns a GeoJSON FeatureCollection. Use individual `list_*` tools when you need richer per-layer filters.

| Param | Type | Notes |
|-------|------|-------|
| `project_id` | string | **required** |
| `bbox` / `radius` / `polygon` | — | **one required** |
| `asset_types` | enum[] | `pavement`, `sign`, `above_ground_asset`, `distress`, `striping`, `centerline` |
| `condition_min` / `condition_max` | int 0–100 | **PCI filter — applies to pavement only**, not distresses/signs |
| `severity` | enum[] | `low`, `medium`, `high` (distresses) |
| `functional_class` | string[] | Road functional class |
| `surface_type` | string[] | Surface type |
| `include_geometry` | bool | Default false |
| `limit` / `cursor` | — | Pagination (max 200) |

## Pavement

### `list_pavement_scores` — inspection-level PCI `[R]`
One record per inspection (multiple per segment over time). Use for individual scores with geometry.

| Param | Type | Notes |
|-------|------|-------|
| `project_id` + spatial filter | — | **required** |
| `score_min` / `score_max` | int 0–100 | Numeric PCI filter |
| `label` | string[] | PCI label filter (Failed…Excellent) |
| `era` | string | Inspection era/period |
| `include_geometry` | bool | LineString geometry |
| `limit` / `cursor` | — | Default 25, max 200 |

Real response feature `properties`: `inspect_id` (e.g. `IA00202`), `condition_score` (e.g. `80.8`), `condition_label`, `length_ft`, `area_sqft`, `address_st`, `client_seg_id`, `inspect_cell_id`, `asset_type`. Extract `condition_score` for averages.

### `list_pavement_segments` — aggregated segments `[R]`
One record per road segment, latest condition only. Use instead of `list_pavement_scores` for a current snapshot. Same params as `list_pavement_scores` minus `era`. Default `limit` 50.

### `list_distresses` — cracks, potholes, rutting `[R]`
| Param | Type | Notes |
|-------|------|-------|
| `project_id` + spatial filter | — | **required** |
| `distress_type` | string[] | See distress-types reference (e.g. `alligator_cracking`, `potholes`, `rutting`) |
| `severity` | enum[] | `low`, `medium`, `high` |
| `limit` / `cursor` | — | Default 20, max 200 |

> **Distress features have `null` geometry** — they attach to pavement segments, no own coordinates.
> **Performance warning:** on large projects (millions of records), a bbox >1 km in either dimension **without** a `severity` or `distress_type` filter hits `statement_timeout`. Always include `severity=['high']` or a `distress_type` for wide bboxes.

### `list_inspection_cells` — photographed road areas `[R]`
Inspection-cell polygons with imagery metadata. Use to find street-level photos covering a spatial area. **The schema allows `limit` up to 200, but the server silently caps each page to 20 regardless.** Heavy payloads (image URLs, distress summaries). For full cell detail use `get_pavement_score_detail`.

### `get_pavement_score_detail` — single inspection detail
| Param | Type | Notes |
|-------|------|-------|
| `inspect_id` | string | **required** — e.g. `IA01492` (from `list_pavement_scores` / `list_inspection_cells`) |
| `project_id` | string | **required** |

Returns scores + related distresses + inspection-cell imagery.

### `get_asset` — generic single-asset detail
| Param | Type | Notes |
|-------|------|-------|
| `asset_id` | string | **required** — `client_seg_id` for pavement, UUID for others |
| `project_id` | string | **required** |
| `include` | enum[] | `history` (PCI time series, pavement only), `distresses`, `imagery` |
| `max_distresses` | int | Default 20, max 200 |

> **Size warning:** with all includes, the response can reach **100K+ chars**. Request only the related data you need.

## Signs

### `list_signs` — traffic sign inventory `[R]`
| Param | Type | Notes |
|-------|------|-------|
| `project_id` + spatial filter | — | **required** |
| `mutcd` | string[] | MUTCD code — e.g. `R1-1` Stop, `R1-2` All-Way Stop, `R2-1` Yield, `W1-1L` Turn (Left), `S1-1` School Crossing (per `cyvl://reference/mutcd-codes`) |
| `category` | string[] | Sign category (Regulatory, Warning, Guide, Marker, School, …) |
| `condition` | string[] | Condition filter (Good / Fair / Poor) |
| `include_geometry` | bool | Point geometry |
| `limit` / `cursor` | — | Default 50, max 200 |

Real feature `properties`: `mutcd`, `category`, `condition`, `image_url`, `feature_id`, `mutcd_category`, `asset_type`, `__neighborhoods`, plus raw fields (`fid`, `FEAT_ID`, `__group`, `location_`, `image_base`). Invalid MUTCD codes return empty results.

> **ID gotcha:** the feature's top-level `id` (32-char hex) is what `get_sign` expects — **not** the `feature_id` field.

### `get_sign` — single sign detail
| Param | Type | Notes |
|-------|------|-------|
| `sign_id` | string | **required** — the `id` field from `list_signs`, NOT `feature_id` |
| `project_id` | string | **required** |

Returns full record: `id`, `feature_id`, `category`, `mutcd`, `condition`, `image_url`, `basename`, nested `properties`, `geometry` (with CRS), `created_at`, `updated_at`.

## Above-Ground Assets

### `list_above_ground_assets` — trees, poles, hydrants… `[R]`
| Param | Type | Notes |
|-------|------|-------|
| `project_id` + spatial filter | — | **required** |
| `asset_type` | string[] | See asset-types reference (e.g. `TREE`, `HYDRANT`, `UTILITY_POLE`, `TRAFFIC_SIGNAL`) |
| `condition` | string[] | Condition filter |
| `include_geometry` | bool | — |
| `limit` / `cursor` | — | Default 50, max 200 |

Real feature `properties`: `asset_type`, `type`, `condition`, `material`, `length`, `image_url`, `feature_id`, `Type`, `__neighborhoods`. (Note many condition values are `unknown` in current data.)

### `get_above_ground_asset` — single asset detail
`asset_id` = the `id` (UUID) from `list_above_ground_assets`, **not** `feature_id`. Returns asset_type, condition, geometry, extended attributes.

## Markings

### `list_markings` — striping & markings `[R]`
| Param | Type | Notes |
|-------|------|-------|
| `project_id` + spatial filter | — | **required** |
| `category` | string[] | See line-types reference (`BIKE_LANE`, `CROSSWALK`, `LINE_STYLE`, `SPECIAL_PURPOSE`, …) |
| `type` | string[] | Marking type/subtype |
| `color` | string[] | `White`, `Yellow`, `Green`, `Red`, … |
| `condition` | string[] | Good / Fair / Poor / etc. |
| `include_geometry` | bool | LineString geometry |
| `limit` / `cursor` | — | Default 50, max 200 |

Real feature `properties`: `type` (e.g. `CONTINENTAL CROSSWALK`), `color`, `length`, `category` (`striping`/`markings`), `condition`, `line_type`, `line_subtype`, `feature_id`, `asset_type`.

### `get_marking` — single marking detail
`marking_id` = the `id` (UUID) from `list_markings`, **not** `feature_id`.

## Imagery

> **Imagery only works on projects where `embedding_count > 0`.** Find them with `list_projects(has_embeddings=true)`.

### `search_imagery` — natural-language image search
| Param | Type | Notes |
|-------|------|-------|
| `query` | string | **required** — natural language (max 200 chars) |
| `project_id` | string | Strongly recommended (omitting is slow on large orgs) |
| `bbox` / `lat`+`lon`+`radius_m` | — | Optional spatial scoping |
| `city` / `state` | string | Geo filters |
| `detected_objects` / `detected_signs` | string[] | Filter by detected labels |
| `has_signs` | bool | Sign presence |
| `point_type` | string | `image`, `crop`, or `tile` |
| `scan_id` | string | Filter by scan ID (shared by `search_imagery_by_image`) |
| `min_score` | number | Confidence threshold (default 0.4) |
| `output` | enum | `metadata` (default), `urls`, `image_content` |
| `page_size` / `page` / `search_id` | — | Pagination (max 200) |
| `max_width` / `quality` | int | `image_content` only |

### `search_imagery_by_image` — reverse image search
Same params as `search_imagery` but takes `query_image` (base64 JPEG/PNG bytes) instead of `query`. Finds visually similar street-level imagery; text reranking is skipped.

### `get_asset_imagery` — photos/LiDAR for one asset
| Param | Type | Notes |
|-------|------|-------|
| `asset_id` | string | **required** |
| `project_id` | string | **required** |
| `output` | enum | `metadata`, `urls` (default), `image_content` |
| `max_width` / `quality` | int | `image_content` only |

### Imagery output modes & the token trick
| Mode | Cost | Use |
|------|------|-----|
| `metadata` | ~50 tokens/result | Filtering / counting — do this FIRST to get a `search_id` + count |
| `urls` | ~100 tokens/result | Download links (`image_url`) for curl/wget |
| `image_content` | ~1000–2000 tokens/image | Native MCP image blocks rendered in Claude Code — only after filtering |

**Token trick:** search `output='metadata'` + `page_size=200` first, then re-call with the **same `search_id`** + `output='image_content'` + `page_size=3-5` (and `max_width=400`) to view only the few images you want. Projects hold 5,000–200,000+ images; usually 1–2 pages suffice.

---

# Reference Data (live from `cyvl://reference/*`)

These are the authoritative valid filter values. Read the live resource if in doubt — invalid codes return empty results, not errors.

| Resource URI | Contents |
|--------------|----------|
| `cyvl://reference/api-capabilities` | Module overview, spatial filters, pagination, imagery modes |
| `cyvl://reference/pci-labels` | PCI label → score range |
| `cyvl://reference/pci-computation` | Midpoints, weighted-avg formula, policy thresholds |
| `cyvl://reference/distress-types` | Valid `distress_type` values |
| `cyvl://reference/asset-types` | Valid `asset_type` values |
| `cyvl://reference/sign-categories` | Valid sign `category` values |
| `cyvl://reference/mutcd-codes` | Valid `mutcd` codes |
| `cyvl://reference/line-types` | Valid marking `category` / `type` values |

## Distress types (`distress_type`)

| Category | Values |
|----------|--------|
| BLEEDING | `bleeding`, `bleeding_flushing` |
| CRACKING | `alligator_cracking`, `block_cracking`, `edge_cracking`, `joint_reflection`, `lt_cracking` (longitudinal & transverse), `slippage_cracking` |
| DETERIORATION | `delamination`, `raveling`, `weathering` |
| EDGE_ISSUES | `curb`, `lane_shoulder_drop_off` |
| STRUCTURAL | `shoving`, `swelling` |
| SURFACE_DEFECTS | `bumps_sags`, `depressions`, `patching`, `potholes`, `rutting` |
| SURFACE_TREATMENTS | `polished_aggregate`, `sealant` |
| UNPAVED | `unpaved` |

## Above-ground asset types (`asset_type`)

**Pedestrian:** `ACCESSIBLE_PARKING`, `ADA_RAMP`, `CROSSWALK`, `CURB`, `CURB_CUT`, `NO_PUSH_BUTTON`, `OBSTRUCTION`, `PEDESTRIAN_HEAD`, `PEDESTRIAN_LCD`, `PEDESTRIAN_PUSH_BUTTON`, `RAMP`, `RAMP_DISTRESS`, `SIDEWALK`, `SIDEWALK_1`–`SIDEWALK_5`, `SIDEWALK_N_A`, `SIDEWALK_OBSTRUCTION`, `STAND_ALONE_PED_PUSH_BUTTON`, `STAND_ALONE_PEDESTRIAN_HEAD`

**Streetscape:** `BENCH`, `BOLLARD`, `BUS_STOP_TRASH_CAN`, `FENCE`, `MAILBOX`, `PLANTER`, `RETAINING_WALL`, `TRASH_BIN`, `TREE`, `TREELINE`, `WALL_FENCE`

**Traffic Control:** `BANNER`, `CCTV`, `CCTV_CAM`, `CROSS_SIGNAL`, `FLASHER`, `FLASHING_BEACON`, `FLASHING_BEACONS`, `SIGN`, `SIGNAL_POLE`, `TRAFFIC_CAM`, `TRAFFIC_SIGNAL`, `TRAFFIC_SIGNAL_POLE`

**Transportation & ROW:** `BIKE_FACILITY`, `BIKE_LANE`, `BIKE_POST`, `BIKE_RACK`, `BUS_BENCH`, `BUS_PAD`, `BUS_SHELTER`, `BUS_STOP`, `CHANGE_MAKER`, `DISTRESS`, `DRIVEWAY`, `FLEX_DELINEATOR`, `GUARDRAILS`, `JERSEY_BARRIER`, `LOADING_ZONE`, `PARKING`, `PARKING_WITHIN_20FT_OF_INTERSECTION`, `PAY_TO_PARK`, `SCOOTER_PARKING`

**Utility:** `BOX`, `CABINET`, `CATCH_BASIN`, `CELL_TOWER`, `GUTTER`, `HYDRANT`, `LUMINARIES`, `MANHOLE_COVER`, `OTHER_COVER`, `STREET_LIGHT`, `STREET_LIGHT_POLE`, `TELEPHONE_POLE`, `UTILITY_POLE`, `VALVE_COVER`, `WATER_VALVE`

**Survey / specialty:** `SURVEY_POLYGONS`, `ANAHEIM_PMP_PCI`, `ASSET_BUFFER`, `BANNER_POLE`, `BARRIER`, `BIKE_PATH`, `BUILDINGS_SURFACE`, `BUS_LANE`, `CONCRETE`, `DETAILED_SIDEWALK_1`–`5`, `DOWNSPOUT`, `IMPERVIOUS_SURFACE`, `INVALID_TRASH_PLACEMENT`, `KERB`, `MANAGED_LANDS`, `OTHER_VALVE`, `PARKING_LOT_GOOD`/`_FAIR`/`_POOR`/`_SATISFACTORY`/`_SERIOUS`/`_VERY_POOR`, `PERMEABLE_SURFACE`, `RIVERDALE_PARK_TREES`, `ROADSIDE_HAZARDS`, `SCHOOL_PARKING_LOT_GATE`, `SCHOOL_SAFETY_1_STAR`–`5_STAR`, `VALID_TRASH_PLACEMENT`

## Marking categories & types

**Line categories (`category`):** `BIKE_LANE`, `CROSSWALK`, `FLEXIBLE_INFRASTRUCTURE`, `HIGH_VISIBILITY`, `LINE_STYLE`, `OTHER`, `RAISED_MARKINGS`, `SPECIAL_PURPOSE`

**Line types (`type`):** `BIKE LANE`, `CROSSWALK`, `FLEXCURB`, `FLEXPOLE`, `HIGH VIZ`, `DASHED`, `DASHED WIDE`, `DOUBLE`, `SHORT DASHED`, `SINGLE`, `SOLID`, `SOLID WIDE`, `SOLID/DASHED`, `RAISED`, `FIRE LANE`, `GORE`, `PARKING`, `STOP BAR`, `YIELD`, `OTHER`

**Subtypes:** crosswalk → `CONTINENTAL`, `DECORATIVE`, `HIGH-VIS`, `LADDER`, `STANDARD`, `ZEBRA`; material → `BRICK OR PATTERNED`, `PLASTIC`, `REFLECTOR`, `SEGMENTED`; line-style → `DASHED`, `DOUBLE`, `SHORT DASHED`, `SINGLE`, `SOLID`, `SOLID/DASHED`, `T`, `WIDE DASHED`, `WIDE STRIPE`; special → `STOP BAR`, `GORE`, `PARKING`, `FIRE LANE`, `YIELD TRIANGLE`

## Sign categories (`category`)

The authoritative `category` values in `cyvl://reference/sign-categories` are: `Emergency`, `Expressway`, `Guide`, `Information`, `Marker`, `Object Marker`, `Parking`, `Recreational`, `School`, `Other`, plus project-specific categories like `Beverly, MA Parking Signs`.

> Note: `Regulatory` and `Warning` are **not** sign-category filter values — they are *MUTCD-code* categories (from `cyvl://reference/mutcd-codes`). Filtering `list_signs` by `category="Regulatory"` returns empty. To get regulatory/warning signs, filter by `mutcd` code prefix (`R*` / `W*`) instead.

## MUTCD codes — common filters (`mutcd`)

| Code | Sign | Category |
|------|------|----------|
| `R1-1` | Stop | Regulatory |
| `R1-2` | All-Way Stop | Regulatory |
| `R2-1` | Yield | Regulatory |
| `R3-1` / `R3-2` | No Right / No Left Turn | Regulatory |
| `R3-4` | No U-Turn | Regulatory |
| `R3-8` | Do Not Enter | Regulatory |
| `R5-1` | Do Not Enter | Regulatory |
| `R6-1L`/`R6-1R` | One Way (L/R) | Regulatory |
| `R7-1` | No Parking Any Time | Regulatory |
| `R9-2` | Bike Lane | Regulatory |
| `R10-3` | No Parking (symbol) | Regulatory |
| `W1-1L`/`W1-1R` | Turn (L/R) | Warning |
| `W2-1` | Cross Road | Warning |
| `W3-1` | Stop Ahead | Warning |
| `W3-3` | Signal Ahead | Warning |
| `W11-2` | Pedestrian Crossing | Warning |
| `W11-1` | Bicycle | Warning |
| `S1-1` | School Crossing | School |
| `D3-1` | Street Name | Guide |
| `D1-1` | Destination | Guide |
| `M3-1`–`M3-4` | Horizontal Alignment (chevrons) | Marker |
| `OM3-L/C/R` | Object Marker | Marker |

The full code list (~230 entries spanning R1–R15, W1–W41, S1–S5, D1–D17, E1–E6, M1–M6, EM, OM, I-series, plus generic `Other_*`/`NON-MUTCD` buckets) lives in `cyvl://reference/mutcd-codes`. Use the regulatory `R*`, warning `W*`, school `S*`, guide `D*`, and marker `M*`/`OM*` prefixes to scope a category.

---

# Available Data (current org)

As of this writing the org exposes **one** live project:

### City of Somerville, MA — Marketing Demo
```
project_id:       f15b854a-d203-49c7-bc25-1350dd4a1cd6
centerline_id:    1d3f12e2-6dba-4018-8a02-9b0e028118db
modules:          ["TrafficSigns"]   (data inventory also includes pavement, assets, markings)
length:           119.9 miles
delivered:        2026-05-01
service_tier:     CyvlSigns
center:           [-71.096373, 42.37967]   (lng, lat)
bounds:           [-71.1343408, 42.3734084, -71.0752535, 42.4180395]
embedding_count:  0   ← NO street-level imagery searchable for this project
```

**Inventory:**
- **Pavement:** 5,080 scored segments — 1,762 Good · 1,572 Satisfactory · 806 Fair · 507 Poor · 314 Very Poor · 106 Serious · 13 Failed
- **Signs:** 3,782 (3,573 Good · 187 Fair · 22 Poor) — all `unknown` MUTCD category in stats, but individual records carry real MUTCD codes (e.g. `D3-1`, `R7-2`)
- **Above-ground assets:** 8,254 — 2,357 trees · 915 curbs · 864 sidewalks · 841 manholes · 790 luminaires · 748 ramps · 437 utility poles · 381 catch basins · 215 signal poles · 173 hydrants · 164 ped push-buttons · 149 traffic signals · + more
- **Markings:** 6,336 striping + 780 markings (continental crosswalks, bike lanes, stop bars, arrows, speed cushions…)

**Worked PCI baseline** (length-weighted, from `pci_distribution`):
```
weighted_avg_PCI ≈ 69.4  →  "Fair" (top of range, near Satisfactory)
scored length     ≈ 152,273 ft  (28.8 mi)
needs major repair (PCI<40)  ≈ 8.6% by length  (Failed+Serious+Very Poor)
critical (PCI<25)            ≈ 2.3% by length
acceptable (PCI≥56)          ≈ 81.5% by segment count
```

> A second project, *"fake project to help track hackathon contestants"*, exists but is **archived and empty** (no modules, no bounds).

---

# Cookbook

```python
# 1. Find the project
list_projects()
#   → f15b854a-... = City of Somerville, MA

# 2. Project-wide condition snapshot
get_project_overview(project_id="f15b854a-...", sections=["pci"])

# 3. Pin a neighborhood
geocode_location("Davis Square, Somerville MA")
#   → lat 42.3964, lon -71.1222, bbox [...]

# 4. Worst pavement in that area
list_pavement_scores(
    project_id="f15b854a-...",
    radius={"lat": 42.3964, "lng": -71.1222, "meters": 400},
    score_max=40,           # Very Poor or worse
    include_geometry=True,
)

# 5. All stop signs in a bbox
list_signs(project_id="f15b854a-...", bbox=[-71.10,42.37,-71.09,42.38], mutcd=["R1-1"])

# 6. High-severity potholes (always filter wide bboxes!)
list_distresses(
    project_id="f15b854a-...",
    radius={"lat": 42.3964, "lng": -71.1222, "meters": 800},
    distress_type=["potholes"], severity=["high"],
)

# 7. Crosswalks in poor condition
list_markings(project_id="f15b854a-...", bbox=[...], category=["CROSSWALK"], condition=["Poor"])

# 8. Hydrant locations
list_above_ground_assets(project_id="f15b854a-...", bbox=[...], asset_type=["HYDRANT"])

# 9. One-shot location assessment
assess_infrastructure(location="Union Square, Somerville MA", project_id="f15b854a-...")

# 10. Drill into one inspection
get_pavement_score_detail(inspect_id="IA00202", project_id="f15b854a-...")
```

---

# Gotchas & Field Glossary

- **`id` vs `feature_id`.** The `get_*` detail tools want the top-level GeoJSON `id` (32-char hex UUID), **never** the `feature_id` property. Passing `feature_id` returns "not found".
- **Pavement asset_id is special.** `get_asset` uses `client_seg_id` for pavement, UUID for everything else.
- **Distresses have `null` geometry.** They reference a pavement segment; they have no own coordinates.
- **Counts are unreliable on spatial queries.** `total_count` comes back `null` and `total_count_estimate` is only an estimate; `has_more=true` ⇒ your result is a lower bound — paginate to `has_more=false` before aggregating.
- **Wide distress bboxes time out** without a `severity`/`distress_type` filter.
- **`get_asset` with all includes can hit 100K+ chars.** Request only what you need.
- **`condition_min/max` on `query_infrastructure` filters pavement only**, not signs/distresses/assets.
- **Imagery requires `embedding_count > 0`** — the current Somerville project has none.
- **Coordinates are WGS84 (EPSG:4326)**, always `[lng, lat]` in GeoJSON order; bbox is `[west, south, east, north]`.
- **This server is read-only** — no tool writes, creates, uploads, or mutates Cyvl data.

**Common response field meanings:**

| Field | Meaning |
|-------|---------|
| `condition_score` | Numeric PCI 0–100 (pavement) |
| `condition_label` | PCI label (Failed…Excellent) |
| `inspect_id` | Pavement inspection ID, e.g. `IA00202` |
| `client_seg_id` | Road segment ID (groups inspections) |
| `inspect_cell_id` | Inspection cell (photographed area) ID |
| `length_ft` / `area_sqft` | Segment dimensions |
| `address_st` | Street name |
| `mutcd` | MUTCD sign code |
| `line_type` / `line_subtype` | Marking classification |
| `image_url` | CloudFront URL to annotated street photo |
| `__neighborhoods` | Comma-separated neighborhood names |
| `embedding_count` | # of searchable street-level images (project level) |

---

*Generated from the live Cyvl MCP server (`https://i3.cyvl.app/mcp`) — 20 tools + 8 reference resources, verified against real API responses.*
