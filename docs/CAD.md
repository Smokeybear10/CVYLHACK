# CAD (Stage 3): the interactive payoff

This is Sonder's Autodesk path and Stage 3, the user-facing payoff (PLAN.md §4, §5.6). After the
swarm validates the narrowed curbs, CAD opens each one in 3D with the EV charger placed in the real
curb, so the report shows the physical fit at that exact spot. It is our second sponsor (NVIDIA +
Autodesk) and the closing beat of the demo: "we measured the site from the scan, here it is, build
here."

Lives on the `cad` branch (off `main`, not `swarm`).

---

## The one idea

Every other siting tool ranks demand on a flat map. None can show whether a charger physically
fits, because they never see the site. Cyvl's street-level 3D scan did. CAD turns that scan into an
editable 3D model of the chosen curb and drops the charger into it. The judge sees a real Somerville
block, the real curb, the real poles and hydrants, and the charger sitting where it would go. That
is the thing a map cannot be.

## What CAD operates on: the specific validated locations

CAD is not one generic scene. It runs once per location, for the exact curb segments the report is
about: the spots Stage 1 narrowed to, the swarm visited and validated, and that surface in the
report as Go or Conditional. For each, CAD reconstructs the physical building blocks of that curb
(ground, curb, sidewalk, poles, luminaires, hydrants, trees, parked cars, building faces) and places
the EV charger in it. We bake the winner plus the top one or two finalists; the same call runs for
any location in the report.

## Where it sits (PLAN.md §4 architecture)

```
Stage 1  SCREEN          (Saim)        region -> ranked candidate curbs
Stage 1.5 OBSTRUCTION CV (Max, SAM3)   drop curbs the data missed
Stage 2  SURVEY swarm    (swarm lane)  visit + validate finalists -> verdicts
Stage 3  INTERACTIVE     (this, CAD)   reconstruct each validated curb in 3D,
                                       place the charger, show the fit
```

Thomas's frontend drives the map and opens Stage 3 on a chosen location. CAD consumes only the small
per-location handoff below. It does not screen, measure, or judge.

---

## The Autodesk realization: align on this

Stage 3 can be shown three ways. They are different Autodesk products, not the same thing, so the
team must pick the headline. This is the one open decision for CAD.

| Realization | What it is | Interactive? | Effort / risk |
|---|---|---|---|
| SDK browser viewer | Cyvl point cloud rendered through the photo's calibrated camera, in-app | pan/orbit, not editable | low, ships with the SDK |
| Xavier's APS Viewer (`hackathonBuckets`) | reconstructed scene where the charger and every object are selectable and movable in the browser | yes, you can place and move the charger | medium, mostly built |
| Civil 3D export | ReCap then Civil 3D, a build-ready CAD file | no, a static deliverable | high, desktop, not live |

Recommendation: make Xavier's APS Viewer the headline Stage 3 and the Autodesk sponsor check. It is
the only option that does exactly what Stage 3 asks, place the charger in the real curb and let you
move it, it uses real Autodesk APS APIs end to end, and Xavier built it and wants us on it. Keep the
SDK viewer as the always-works fallback. Treat Civil 3D as an optional build-ready export artifact
(the plan names it in §7), pre-baked, never a live round-trip.

PLAN.md §7 currently names Civil 3D. The recommendation above is to lead with the APS Viewer instead;
get the team to confirm so the plan and CAD agree.

---

## What the tool is (`xavier-cyvl/hackathonBuckets`)

Xavier (Cyvl) built a pipeline that turns one raw Cyvl LiDAR tile into an interactive Autodesk Viewer
scene. End to end:

1. Take one raw LAZ tile (about 110M points, UTM 19N) from Cyvl's Somerville survey.
2. Crop an 80 m region, classify ground with PDAL SMRF, split road from sidewalk using the scan
   vehicle's drive paths.
3. Detect parked cars geometrically: keep points 0.3 to 2.5 m above local ground, cluster with
   DBSCAN, fit PCA-oriented boxes gated to real car dimensions.
4. Lift Cyvl's 2D CV detections (trees, utility poles, hydrants, manholes, signals) into 3D by
   cropping the cloud at each detection's coordinate and measuring ground elevation plus height.
5. Extrude OSM building footprints to point-cloud-measured heights.
6. Write everything as a multi-object OBJ + MTL, zip it, push it through Autodesk APS (OSS signed-S3
   upload, Model Derivative to SVF2) into the Autodesk Viewer, with the raw colored point cloud as a
   toggleable three.js overlay.

The detail that makes this perfect for us: each object is written as an OBJ `o <name>` group, and
Model Derivative turns every group into an individually selectable node (dbId) in the Viewer. So
move, delete, and hide work with zero extra metadata. "Move car" already works. Adding a movable EV
charger is one model and one placement.

Repo map:
- `aps/` auth (2-legged OAuth), OSS upload, Model Derivative client
- `pipeline/` crop, segment (ground/road/cars), lift_assets (2D to 3D), ground_mesh, buildings,
  `to_cad` (OBJ/MTL writer + parametric models)
- `viewer/` token server, viewer page, point-cloud overlay, select/move/delete interactions
- `run.py` end-to-end driver: LAZ tile to classified scene to APS to URN
- `docs/` Xavier's integration write-ups (read `export-handoff.md`, it lists every trap)

Proven demo scene already in the repo: College Avenue, Ball Square, West Somerville (42.399430,
-71.119058). Good fallback if our chosen winner gives trouble.

---

## The handoff: Sonder to CAD, per location

The chain is Stage 1 `top` / `candidates` (Saim) to the swarm to a validated location to CAD. One
JSON per location, pulling from both the screen (measured features) and the swarm (validated verdict
and true measurement):

```json
{
  "cand_id": "seg_001",                  // Saim's candidate id (= swarm site_id)
  "address_st": "Elm St near Davis Sq",
  "lon": -71.1221, "lat": 42.3966,       // Stage 1 'top' centroid: aim the crop, place the charger
  "bearing": 41.0,                        // street heading, to orient the charger
  "verdict": "go",                        // the swarm's validated verdict
  "usable_frontage_ft": 22.5,             // Stage 2 measured true frontage, beats Stage 1's proxy
  "dist_to_power_m": 12.0,                // Stage 1 'candidates'
  "est_make_ready_usd": 9000,             // Stage 1 'candidates', labels the connection cost
  "station_size": "small"                 // sets how many ports/stalls the charger model shows
}
```

Field sources, exact: `cand_id`, `address_st`, `lon`, `lat` come straight from Saim's Stage 1 `top`.
`verdict` and `usable_frontage_ft` are the swarm's validated outputs (our `Verdict` already carries
`lon` and `lat`). `dist_to_power_m` and `est_make_ready_usd` come from Stage 1 `candidates`. CAD
reads this to select the LiDAR tile, aim the ROI at the location, place the charger at that curb, and
label the connection cost.

---

## The integration work (small, because the pipeline already does the hard part)

### 1. The charger model

Add one parametric model to `pipeline/to_cad.py`, in the same style as Xavier's tree, pole, and
hydrant models (built from his `mesh_box` / `mesh_cylinder` primitives). Names carry no spaces so
each stays a selectable Viewer node:

```python
def ev_station_objects(stations):
    """stations: [{x, y, ground_z, yaw}] in local-shifted UTM. Pedestal + screen + connector."""
    objs = []
    for i, s in enumerate(stations, 1):
        x, y, z0, yaw = s["x"], s["y"], s["ground_z"], s.get("yaw", 0.0)
        nm = f"ev_station_{i:02d}"
        bv, bf = mesh_box((x, y, z0 + 0.60), (0.45, 0.30, 1.20), yaw)     # pedestal
        objs.append({"name": nm, "material": "ev_green", "verts": bv, "faces": bf})
        sv, sf = mesh_box((x, y, z0 + 1.28), (0.42, 0.10, 0.34), yaw)     # screen head
        objs.append({"name": nm + "_screen", "material": "signal", "verts": sv, "faces": sf})
        cv, cf = mesh_cylinder(x + 0.20, y, z0 + 0.95, 0.04, 0.30)        # connector stub
        objs.append({"name": nm + "_plug", "material": "metal", "verts": cv, "faces": cf})
    return objs
```

Add a charger color to `MATERIALS` in the same file and it flows through `write_mtl`:

```python
"ev_green": (0.10, 0.55, 0.30),
```

### 2. Place it at the location

In `run.py`, after assets are lifted and shifted to the local origin (`ox`, `oy`), read the handoff
and add one station at the curb (its ground height comes from the classified ground, so it sits on
the road, not the horizon):

```python
from pyproj import Transformer
loc = json.load(open(os.environ["SONDER_SITE"]))                      # the per-location handoff json
wx, wy = Transformer.from_crs(4326, crs, always_xy=True).transform(loc["lon"], loc["lat"])
gz = ground_ds[cKDTree(ground_ds[:, :2]).query([wx, wy])[1], 2]       # real ground elevation there
stations = [{"x": wx - ox, "y": wy - oy, "ground_z": gz, "yaw": math.radians(loc.get("bearing", 0))}]
objs = ground_objs + bld_objs + car_objects(cars) + asset_objects(assets) + ev_station_objects(stations)
```

Aim the crop at the location with `ROI_CX=wx ROI_CY=wy` (run.py honors these env vars), and pick the
tile for that coordinate with `pipeline/select_tiles.py`.

### 3. Wire the swarm to emit the handoff

A few lines in the swarm `service.py`: when a winner is chosen, write the JSON above from the
`Verdict` (it has `lon`, `lat`, `verdict`) plus the finalist's `dist_to_power_m` and
`est_make_ready_usd`. That is the entire contract between our two lanes.

### 4. Stretch: click-to-place in the Viewer

Xavier's viewer already moves a selected node via fragment proxies. To let the user drop a charger
(or car) by clicking the street: raycast the click to a ground point, then clone or show a station
node there. Viewer-side addition next to the existing move/delete handlers. The seeded charger in
step 2 already carries the demo, so this is a nice-to-have.

---

## The demo beat (rehearse this exact cut)

1. The swarm pins finish; click the winner.
2. The report shows measured frontage, distance to the pole, and the evidence photo with the mask.
3. Hit "open in 3D." Cut to the Autodesk Viewer of that block: real ground, poles, hydrants, cars,
   the charger standing at the curb.
4. Select the charger, nudge it along the curb. "This is the real curb from Cyvl's scan, and the
   charger fits. No map can show you this."
5. Toggle the raw point cloud overlay for the before/after. Optionally show the Civil 3D export as
   the build-ready handoff. Close: "Same engine, any scanned street."

Keep the pre-baked scene loaded and ready so this never depends on a live translate.

---

## Why it wins the rubric (PLAN.md §3, docs/JUDGING.md)

- Use of Cyvl + sponsor data (25%): real Autodesk APS APIs (Auth v2, OSS, Model Derivative, Viewer
  SDK) on real Cyvl LiDAR. Remove Cyvl and there is no scene to build. Two sponsors woven, NVIDIA in
  perception and Autodesk here, which is the cap. Load-bearing, not decorated.
- Technical (25%): an editable 3D reconstruction with a placeable charger and real measurements is
  the opposite of a "Google Maps clone" (the named 0). It runs live in the browser, nothing hidden.
- Presentation (25%): the 3D cut is the memorable close, the thing the room has not seen from another
  team.
- Business (25%): it makes the value physical. The buyer (a charging network, EPC firm, or city)
  sees the fit and the connection cost on the real curb, which is what the $1k truck roll was for.

---

## Setup and credentials

- Python 3.11 venv. `pip install -r requirements.txt`. PDAL must come from conda
  (`conda install -c conda-forge pdal python-pdal`); it fails on pip/macOS. Do this first, it is the
  main setup hazard.
- `.env` (gitignored) needs `APS_CLIENT_ID` and `APS_CLIENT_SECRET` (Autodesk app credentials,
  separate from the Anthropic key). Xavier can hand over working ones since he built the app.
- Data from the public `cyvl-hackathon` S3 bucket (anonymous works): the location's LAZ tile, plus
  `pavements_v2`, `aboveGroundAssets_v2`, `streetviewImagePaths_v2`.

## APS traps that decide whether demo day works (from Xavier's export-handoff)

These are the non-obvious things that break a scene silently. Honor all of them.

- OBJ `o <name>` groups are what make objects selectable. Names must have no spaces. Use
  `ev_station_01`, `car_03_cabin`. A space splits the name and breaks the node.
- Colors survive only when OBJ + MTL are zipped together and the job is submitted with
  `compressedUrn: true` and `rootFilename: "scene.obj"`. A bare OBJ renders gray. `mtllib scene.mtl`
  must be the first OBJ line.
- SVF2 derivatives are cached per OSS object key. Re-uploading changed geometry under the same key
  serves the stale model. Version the key every re-bake (`scene_cad_v1.zip`, `_v2`, ...) and set
  `x-ads-force: true`. If you demo an old scene, this is why.
- Survey data is Z-up, the Viewer defaults Y-up. Fix in the viewer, not the geometry:
  `navigation.setWorldUpVector(0,0,1)` plus a street-level initial camera. Do not pre-rotate the OBJ.
- Shift geometry to a local origin before export. Raw UTM coords (about 330000, 4690000) cause Viewer
  precision jitter; run.py subtracts `ox`, `oy`.
- 2-legged OAuth scopes: translate/upload need `data:read data:write data:create bucket:create
  bucket:read`. The viewer token must be `data:read` only; `viewer:read` returns 400 invalid_scope.
  The token is served from a tiny local endpoint so credentials never reach the browser.

## Demo safety

The full 110M-point pipeline will not run reliably live. Pre-bake each report location: run the
pipeline, upload, get the URN, paste it into the viewer. Bump the OSS object key on every re-bake.
On stage, the swarm picks the winner live, then we cut to the pre-baked Viewer of that block. Keep a
cached fallback for every step.

## Honest limitations (Xavier's notes, do not fight them)

- The APS Viewer has no native point cloud ingestion. The raw cloud is a three.js overlay, visual
  only, not part of the editable model. That is fine; the OBJ objects are what we interact with.
- A street-side scan sees facades only. Car detection is heuristic and buildings are extruded
  footprints, not reconstructed roofs. Our charger is placed from the exact validated coordinate, so
  it is precise regardless of the surrounding reconstruction.
- This tile's RGB is empty; point colors are synthesized from elevation and LiDAR intensity.
- Everything is real Cyvl scan data. No mock geometry on the demo path.

## Status

- Read and understood Xavier's repo end to end. The integration is small (the model and placement
  above) because his pipeline already does the heavy lifting.
- Not yet run here. Blocked only on environment setup (conda + PDAL) and APS credentials from Xavier.
- Plan and contract are set. Next action: get the creds, prove the round-trip with
  `write_dummy_scene()`, add the charger, bake the demo location.

## Build order

1. Sibling-clone `xavier-cyvl/hackathonBuckets`. conda env + PDAL. APS creds in `.env`.
2. Prove the dummy round-trip: `write_dummy_scene()` to upload to translate to viewer.
3. Add `ev_station_objects` plus the `ev_green` material. Re-run the dummy with a charger and confirm
   it is selectable and movable in the viewer.
4. Pick the demo location (start with the swarm's winner, or Xavier's proven Ball Square scene). Pull
   its tile and vectors. Run `run.py` with `SONDER_SITE` and the ROI center.
5. Wire the swarm winner to the handoff JSON (a few lines in the swarm `service.py`).
6. Pre-bake the report locations, paste the URNs, rehearse the swarm-to-viewer cut three times.
7. Stretch: viewer click-to-place; the Civil 3D export artifact.
