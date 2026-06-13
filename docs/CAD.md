# CAD (Stage 3): the interactive 3D payoff

Sonder's Autodesk lane and the closing beat of the demo. After the swarm validates a curb, CAD
shows that exact block reconstructed in 3D from Cyvl's LiDAR, with EV chargers dropped on the open
curb so you see the physical fit. Lives on the `cad` branch.

Status: **LIVE.** A real Ball Square (Somerville) block is baked and viewable in the Autodesk Viewer
with two chargers placed.

---

## The one idea

A map ranks demand on a flat image. It cannot show whether a charger physically fits. Cyvl's
street-level 3D scan can. CAD turns the scan into an editable Autodesk scene and places the charger
on the real curb, in the real space, next to the real poles, hydrants, trees, and parked cars.

## View it

The viewer is the standalone APS viewer served by a tiny token endpoint (reads our APS keys from
`cad/.env`, gitignored).

```
cd cad
$HOME/miniconda3/envs/cad/bin/python viewer/token_server.py   # serves localhost:8080 + a data:read token
# open http://localhost:8080/index.html
```

On load the camera frames and highlights the chargers. No dragging, no editing, no buttons. Each
charger has a tall bright locator pillar so it is unmissable in the block.

## What is in the scene (real Cyvl LiDAR, ~14 M points in the ROI)

Reconstructed by Xavier's pipeline (`run.py`) from one real LiDAR tile:
- ground classified into road / sidewalk / grass (PDAL SMRF + drive-path split)
- parked cars detected geometrically (height band -> **DBSCAN** clustering -> PCA-oriented boxes)
- Cyvl 2D detections lifted to 3D (trees, poles, hydrants, manholes, signals)
- OSM building footprints extruded to point-measured heights
- **two EV chargers** placed on open curb spots

The demo block is **Highland Avenue, Ball Square, Somerville** (`42.39539, -71.11964`, Google Maps
order = lat, lon).

## The two chargers

Both are parametric, built from boxes/cylinders/cones in `pipeline/to_cad.py`
(`ev_charger_objects(chargers, style=..., start=..., beacon=...)`), each part a named OBJ group so
Model Derivative renders it in color.

| Style | Look | Based on | Locator |
|---|---|---|---|
| `pedestal` | dark charcoal pedestal, slim body, head with screen + teal status bar, **dual ports** (holster + J1772 each side) | ChargePoint CT4000 (6-8 ft pedestal) | magenta pillar |
| `futuristic` | sleek curved **white monolith**, rounded body + tapered cap, cyan light strip, connector | modern curbside fast charger (no branding) | cyan pillar |

The locator beacon is a visibility aid; pass `beacon=False` for a clean final-demo bake.

## Placement: automatic, on an open curb, never blocked

`run.py` does NOT place the charger by hand. It:
1. takes the validated site lon/lat (`cad/site.json` / the swarm handoff),
2. finds **sidewalk** points near it (from the classified ground),
3. keeps only points **>= 1.5 m clear** of every tree / pole / hydrant / car,
4. places charger 1 (pedestal) at the closest open curb to the target, and charger 2 (futuristic)
   at another open curb ~20-45 m down the block.

So the charger always lands on an open curbside spot, never inside an obstacle. It writes every
charger's lon/lat to `out/charger_placement.json` (copied to the committed `cad/charger_location.json`).

## Coordinates for the frontend (Thomas)

`export_spots.py` chunks every candidate spot by street into `cad/spots_by_street.json` (committed):
- **201 streets, 5080 spots** (e.g. Summer Street = 223).
- each spot has `lon`/`lat` (GeoJSON order) AND `latlon` (lat,lon for Google Maps) AND a `maps_url`,
  so the order can never be confused.

```
cd cad && python export_spots.py                 # all candidate curbs per street
cd cad && python export_spots.py --verdicts v.json # only the swarm-verified spots (the end goal)
```

End goal: one CAD scene per swarm-verified street. `run.py` already bakes per location; loop it over
the verified streets and you get a CAD file for each.

## Re-bake any location (the working pipeline)

```
cd cad
# 1. download the LiDAR tile covering your lon/lat into cad/laz/ (see pipeline/select_tiles.py)
# 2. set the site (cad/site.json: lon, lat, bearing)
LAZ_DIR="$PWD/laz" SONDER_SITE="$PWD/site.json" SCENE_KEY="sonder_real_vN.zip" \
  $HOME/miniconda3/envs/cad/bin/python run.py     # prints the URN + charger lat/lon
LAZ_DIR="$PWD/laz" $HOME/miniconda3/envs/cad/bin/python export_points.py   # optional point-cloud overlay
# paste the URN into viewer/index.html (const URN=...). BUMP SCENE_KEY every re-bake.
```

## How it goes to Autodesk (proven with our APS app)

Generated meshes -> multi-object **OBJ + MTL** -> zip -> OSS signed-S3 upload -> Model Derivative
**SVF2** translate (`compressedUrn` + `rootFilename`, `x-ads-force`) -> manifest poll -> Viewer
loads the URN. Code: `pipeline/to_cad.py` + `aps/upload.py` + `aps/translate.py`, driven by `run.py`.
Our APS client id/secret live in `cad/.env`. Verified end to end (token, bucket, upload, translate).

## APS traps that decide demo day (from Xavier's export-handoff, all honored)

- OBJ `o <name>` groups become selectable nodes; **names must have no spaces**.
- Colors survive only via zipped OBJ+MTL with `compressedUrn:true` + `rootFilename:"scene.obj"`.
- SVF2 is cached per OSS key -> **version the object key every re-bake** (`sonder_real_vN.zip`).
- Survey data is Z-up; the viewer fixes it with `setWorldUpVector(0,0,1)`, not by rotating geometry.
- Geometry is shifted to a local origin to avoid Viewer precision jitter.
- 2-legged scopes: upload/translate need `data:read data:write data:create bucket:create
  bucket:read`; the viewer token must be `data:read` only.

## Why it scores (PLAN.md §3, docs/JUDGING.md)

- **Sponsor data (25%)**: real Autodesk APS APIs (Auth v2, OSS, Model Derivative, Viewer SDK) on real
  Cyvl LiDAR. Remove Cyvl and there is no scene. NVIDIA (perception lane) + Autodesk (this) = two
  sponsors, woven.
- **Technical (25%)**: an editable 3D reconstruction with chargers placed and real measurements is the
  opposite of a "Google Maps clone" (the named 0). Runs live in the browser.
- **Presentation (25%)**: the 3D cut is the memorable close.
- **Business (25%)**: the buyer sees the fit and connection cost on the real curb.

## Files

```
cad/
  pipeline/to_cad.py     OBJ/MTL writer + parametric models incl. ev_charger_objects (both styles)
  pipeline/...           crop, segment (ground/road/cars via DBSCAN), lift_assets, ground_mesh, buildings
  run.py                 LiDAR tile -> reconstructed scene -> place 2 chargers -> APS -> URN
  export_points.py       point-cloud overlay for the viewer (optional)
  export_spots.py        per-street candidate coordinates for the frontend
  viewer/                token_server.py + index.html + viewer.js (frames/highlights chargers, no drag)
  aps/                   APS auth + OSS upload + Model Derivative
  charger_location.json  the placed chargers' coordinates (committed)
  spots_by_street.json   per-street spot coordinates for Thomas (committed)
  tests/                 8 to_cad tests green (charger models, scene OBJ, materials)
  .env                   APS_CLIENT_ID / APS_CLIENT_SECRET (gitignored)
```

## Setup / env

- conda env `~/miniconda3/envs/cad`: PDAL 3.5.3 (py 3.11) + laspy/scipy/sklearn/geopandas/pyproj/matplotlib.
- PDAL must come from conda (`-c conda-forge`); it does not pip-install on macOS.
- `cad/.env`: `APS_CLIENT_ID` / `APS_CLIENT_SECRET` (our own Autodesk app, free tier).
- Cyvl LiDAR + layers come from the public `cyvl-hackathon` S3 bucket (anonymous).

## Honest limitations

- The APS Viewer has no native point cloud; the raw cloud is a three.js overlay (visual only).
- Street-side scan sees facades only: cars are heuristic, buildings are extruded footprints. The
  chargers are placed from exact coordinates, so they are precise regardless.
- Everything is real Cyvl scan data. No mock geometry on the demo path.
- The full LiDAR->APS bake is not run live; pre-bake each demo location and load its URN.
