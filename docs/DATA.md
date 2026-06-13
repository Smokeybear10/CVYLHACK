# Data Reality - what we actually have

Verified live on hackathon day by querying the MCP and the public S3 bucket. This is the ground truth, not the brief's marketing.

## Two access paths, very different contents

### 1. The MCP / REST API (`i3.cyvl.app`)
Connected via OAuth. Org has ONE real project:
- `f15b854a-d203-49c7-bc25-1350dd4a1cd6` — "City of Somerville, MA Marketing Demo"

Through the API you get **structured detections with geometry**, but key labels are blank:
- Signs: 3,782 — locations + condition, but `mutcd` type is `unknown` for all.
- Above-ground assets: ~8,254 — type + location, condition `unknown`.
- Pavement: 5,080 scored segments (PCI Good→Failed) with line geometry.
- Markings: 7,116 with type/color/condition.
- **No imagery** (`embedding_count: 0`) — `search_imagery` returns nothing here.

Good for: live spatial queries, maps, "what's at this location" lookups, the demo's data layer.

### 2. The public S3 bucket (`cyvl-hackathon`, us-east-1) — the good stuff
Open with NO credentials for the duration of the event (`--no-sign-request` or plain HTTPS). Re-locked after.

```
https://cyvl-hackathon.s3.amazonaws.com/<key>
```

This has the **imagery AND the ground-truth labels** the MCP lacks. This is where any CV/ML work happens.

## What's in the bucket

Docs first: `README.md`, `index.md`, `schemas.md` at the bucket root.

GeoJSON + GeoParquet layers (`data/*.geojson`, `parquet/layers/*.parquet`, WGS84):

| Layer | Count | Geometry | Per-row image? | Labels |
|---|---|---|---|---|
| `rollup_v2` | 894 | LineString | no | condition score + render color |
| `pavements_v2` | 5,080 | LineString | no | PCI `score` 0-100 + `label` (city-wide) |
| `distresses_v2` | 84,612 | Polygon | **yes (`image`)** | `distress_type` (14 cls) + `severity` (low/med/high) |
| `distressInspectionCells_v2` | 21,141 | Polygon | yes (list) | per-cell distress summaries, FHWA class |
| `signs_v2` | 3,782 | Point | **yes (`image_url`)** | `mutcd` code + `category` (7) + `condition`. South/SE only |
| `sam_v2` | 7,116 | LineString | yes | marking `type`/`color`/`condition` |
| `aboveGroundAssets_v2` | 8,254 | Point | yes | `asset_type` |
| `plainImagery_v2` / `streetviewImages_v2` | 22,830 | Point | the photos themselves | lon/lat/bearing/timestamp, `prev_id`/`next_id` |
| `panoramicImagery_v2` | 38,469 | Point | 360 viewer links | geo-only |

SDK parquet (`parquet/`):
- `frames.parquet` — **311,784 posed camera frames**: 6-DoF `camera_to_utm` pose, intrinsics ref, public image URL. The thing that enables 3D↔2D projection.
- `cameras.parquet` — 16 calibrated pinhole intrinsics (3840x2160, plumb_bob distortion).
- `tiles.parquet` — 514 LiDAR tiles, LAZ + **COPC** (range-read a block in seconds) + Potree URLs. Point data ~473 GB, CDN-streamed.

## Label distributions (verified)

Distress types (84,612 total):
```
lt_cracking 53,482 · weathering 11,673 · edge_cracking 6,494 · patching 4,609 ·
alligator_cracking 2,021 · depressions 1,446 · raveling 1,383 · block_cracking 1,336 ·
sealant 1,315 · bleeding 284 · potholes 202 · bumps_sags 146 · rutting 120 · delamination 101
```
Severity: low 70,030 · medium 10,884 · high 3,698. (Heavily imbalanced — `lt_cracking`/`low` dominate.)

Sign MUTCD top: R7-2 687, R7-5 578, R7-1 430, D3-1 242, R1-1 (STOP) 150, ... Category: Regulatory 1,892, Other 900, Guide 257, Warning 254, School 19.

## The images are full 4K frames, not crops

Both `distresses.image` and `signs.image_url` point to full 3840x2160 frames with the target annotated (distress = pink mask overlay baked in; sign = a small drawn box). ~17 distresses per frame; 4,959 unique distress frames.

So to get tight per-object training crops you must project the feature's world geometry into the frame using the SDK poses. Verified working:
- `cyvl.load_scene("somerville")` downloads/caches ~120 MB, no creds.
- `scene.nearest_frame(lon,lat,facing='front')` / `scene.frames_near(lon,lat,radius_m=)`.
- `frame.project(lonlat=..., alt=...)` → `Projected(pixels, depth, in_view, points_utm)`.
- `frame.image()` → numpy RGB. Cropping around projected pixels works.

### The one wrinkle: elevation
`alt=0` is sea level. Somerville ground sits several meters up, so projecting features at `alt=0` lands them on the horizon, not the road. Fixes, easiest first:
1. **Use the LiDAR ground elevation.** `frame.points_in_view()` returns LiDAR points with both pixels and world XYZ — match the ones whose lon/lat fall inside the feature polygon to get correct pixels. This is what the SDK is built for.
2. Sample a constant local ground height (e.g. read `cam_z` and subtract camera height ~2.5m) as a rough approximation.
3. Sidestep projection: the distress `image` is already a **masked overlay** (defects in pink). Color-threshold the pink to derive masks, or train directly on the masked frames.

## Two paths to a training set

- **Path A (no projection, fastest):** download the masked distress frames, color-threshold the pink overlay → segmentation masks, train. Crude labels but zero projection work.
- **Path B (clean, the real version):** for each feature, use `points_in_view()` LiDAR to get correct pixels → tight bbox/crop labeled with `distress_type`/`severity` (or sign `mutcd`). Feeds a YOLO detector or a classifier. This is the strong NVIDIA story.

## NVIDIA track viability

Viable. Labels + images both exist. Compute can be a free Colab T4 (an NVIDIA GPU) for fine-tuning; confirm if the NVIDIA mentor offers TAO/NIM/better hardware. Recommended target: distress detection/classification (most labels) or sign MUTCD classification (cleaner per-object framing, partial coverage).

## Coverage gotchas (from bucket README)

- Signs cover the city's south/southeast only. Pavement/distress/imagery are city-wide.
- 360 panoramas have no poses (geo-only).
- LiDAR was ~85 passes days apart; moving vehicles are in the cloud. Use same-pass window.
- ~2.3% of frames have poses but no own-pass LiDAR.
