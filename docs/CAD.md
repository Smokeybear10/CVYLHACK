# CAD — what it is, why, and where it's going

Lives on the `cad` branch (off `main`, not `swarm`). This is Sonder's Autodesk path and **Stage 3,
the interactive payoff** (see PLAN.md §4 and §5.6): open the winning curb in 3D/CAD with the EV
charger placed in the real curb segment, so the user sees the fit in 3D space. It is our second
sponsor (NVIDIA + Autodesk) and the closing beat of the demo.

## Aligned with the current PLAN.md (read this first)

PLAN.md changed. Stage 3 is now explicit and the architecture is Stage 1 (screen) → 1.5
(obstruction CV) → 2 (swarm) → **3 (interactive 3D/CAD)**. The plan names two Autodesk-adjacent
realizations for Stage 3, and Xavier's tool is a third. They are not the same product — this is the
one thing the team must align on:

| Realization | What it is | Plan ref | Live? |
|---|---|---|---|
| **SDK browser viewer** | point cloud through the photo's calibrated camera, in-app | §5.6 "live in-app" | yes, ships |
| **Xavier's APS Viewer** (`hackathonBuckets`) | reconstructed editable scene, EV station **placeable + movable** in-browser | (not yet in plan) | yes, interactive |
| **Civil 3D export** | ReCap → Civil 3D build-ready CAD file | §7 Autodesk, §5.6 "export" | no, pre-baked artifact |

**Recommendation:** make **Xavier's APS Viewer the primary interactive Stage 3 + the Autodesk
sponsor check** — it is the only one that literally "places the EV charger in the real curb and lets
you see/move the fit," which is exactly what Stage 3 asks for, and Xavier built it and wants us on
it. Keep the SDK viewer as the lightweight always-works fallback, and treat Civil 3D as the
heavier "build-ready export" handoff artifact the plan mentions in §7 (pre-baked, not live). That
keeps us aligned with §5.6/§7 while using the better interactive tool.

**Open decision for the team:** confirm APS Viewer (Xavier) as the Stage 3 demo, with Civil 3D as
an optional export. If the team insists on Civil 3D as the headline, that is a heavier, riskier
desktop round-trip and we should say so.

## The purpose in one line

After the swarm picks the best curb, we show it as a real, measured, editable CAD model in the
Autodesk Viewer with an EV station placed at the curb — proof that "we measured the physical site
from the scan" and the natural "export to CAD, same engine any scanned street" close.

## What the tool is (xavier-cyvl/hackathonBuckets)

Xavier (Cyvl) built a pipeline that turns one raw Cyvl LiDAR tile into an interactive Autodesk
Viewer scene. He wants us to use it. What it does, end to end:

1. Take one raw LAZ tile (~110M points, UTM 19N) from Cyvl's Somerville survey.
2. Crop an ~80 m region, classify ground (PDAL SMRF), split road vs sidewalk using the scan
   vehicle's drive paths.
3. Detect parked cars geometrically (height band above ground + DBSCAN + PCA-oriented boxes).
4. Lift Cyvl's 2D CV detections (trees, poles, hydrants, manholes, signals) into 3D by cropping
   the cloud at each detection's coordinate and measuring ground elevation + height.
5. Extrude OSM building footprints to point-cloud-measured heights.
6. Write everything as a multi-object **OBJ + MTL**, push it through **Autodesk APS** (OSS upload →
   Model Derivative → SVF2) into the **Autodesk Viewer**, with the raw point cloud as a toggleable
   overlay.

The decisive detail for us: each object is written as an OBJ `o <name>` group, which Model
Derivative turns into an individually **selectable, movable, deletable** node in the viewer, with
zero extra metadata. "Move car" and "delete" already work.

Repo map: `aps/` (auth, OSS upload, Model Derivative), `pipeline/` (crop, segment, lift_assets,
ground_mesh, buildings, `to_cad` = OBJ/MTL writer + parametric models), `viewer/` (token server +
viewer + interactions), `run.py` (driver), `docs/` (his integration write-ups).

## Why this is the right Autodesk play (scoring)

- **Real, load-bearing sponsor use:** real APS APIs (Auth v2, OSS, Model Derivative, Viewer SDK) on
  real Cyvl LiDAR. Remove Cyvl and there is no scene. Not bolted on.
- **Not a Google Maps clone:** an editable 3D reconstruction with a placeable charger and real
  measurements is something no map produces.
- **Two sponsors, woven:** NVIDIA (perception, Max's lane) + Autodesk (this). That's the cap; we
  skip Ask Boston.

## The feature you asked for: place a car / EV station curbside

The viewer already moves and deletes objects. We add one thing: an **EV station** model, placed at
the curb the swarm picked. Then the user can move it around like the cars.

### 3a. Seed the station at the winning curb (small, pipeline side)

Add a parametric model to `pipeline/to_cad.py` next to his tree/pole/hydrant models (same
`mesh_box`/`mesh_cylinder` primitives):

```python
def ev_station_objects(stations):
    """stations: [{x, y, ground_z, yaw}]. Pedestal + screen head."""
    objs = []
    for i, s in enumerate(stations, 1):
        x, y, z0, yaw = s["x"], s["y"], s["ground_z"], s.get("yaw", 0.0)
        nm = f"ev_station_{i:02d}"            # no spaces -> stays a selectable node
        bv, bf = mesh_box((x, y, z0 + 0.6), (0.5, 0.3, 1.2), yaw)     # pedestal
        objs.append({"name": nm, "material": "pole", "verts": bv, "faces": bf})
        sv, sf = mesh_box((x, y, z0 + 1.25), (0.45, 0.08, 0.35), yaw) # screen/head
        objs.append({"name": nm + "_screen", "material": "signal", "verts": sv, "faces": sf})
    return objs
```

Place it at the winner in `run.py` (after assets are lifted and shifted to local origin):

```python
from pyproj import Transformer
win = json.load(open(os.environ["SONDER_WINNER"]))      # the handoff json below
wx, wy = Transformer.from_crs(4326, crs, always_xy=True).transform(win["lon"], win["lat"])
gz = ground_ds[cKDTree(ground_ds[:, :2]).query([wx, wy])[1], 2]   # ground elevation there
stations = [{"x": wx - ox, "y": wy - oy, "ground_z": gz, "yaw": math.radians(win.get("bearing", 0))}]
objs = ground_objs + bld_objs + car_objects(cars) + asset_objects(assets) + ev_station_objects(stations)
```

Aim the crop at the winner with `ROI_CX=wx ROI_CY=wy` (run.py honors these), and pick the tile with
`pipeline/select_tiles.py` for that coordinate.

### 3b. Click-to-place in the viewer (stretch, "place it wherever")

His viewer already moves a selected node via fragment proxies. To let the user drop a new station
(or car) by clicking the street: raycast the click to a ground point, then clone/show a station
node there. Viewer-side addition next to the existing move/delete handlers. Nice-to-have; 3a alone
carries the demo.

## What CAD operates on: the specific validated locations

CAD is not one generic scene. It runs **per location** — the specific curb segments the report is
about: the places Stage 1 narrowed to, Stage 2 (the swarm) visited and validated, and that land in
the report as Go / Conditional. For each of those locations CAD reconstructs the **physical building
blocks** of that exact curb (ground, curb, poles, hydrants, trees, buildings) and places the EV
charger in it, so the report's 3D view is that real spot. Typically we bake the winner plus the top
1-2 finalists; the same call runs for any location in the report.

## The Sonder → CAD handoff (per location)

The chain is: Stage 1 `top`/`candidates` (Saim) → swarm validates → a validated location → CAD. The
handoff for one location pulls from both Stage 1 (the screen's measured features) and Stage 2 (the
swarm's validated verdict + true measurement):

```json
{
  "cand_id": "seg_001",                 // Saim's candidate id (= swarm site_id)
  "address_st": "Elm St near Davis Sq",
  "lon": -71.1221, "lat": 42.3966,      // Stage 1 'top' centroid -> aim the crop + place the charger
  "bearing": 41.0,                       // street heading, to orient the charger
  "verdict": "go",                       // the swarm's validated verdict
  "usable_frontage_ft": 22.5,            // Stage 2 measured (true frontage), beats Stage 1's proxy
  "dist_to_power_m": 12.0,               // from Stage 1 'candidates'
  "est_make_ready_usd": 9000,            // from Stage 1 'candidates' (informs the layout/label)
  "station_size": "small"                // how many stalls/ports the charger model shows
}
```

`cand_id`/`lon`/`lat` come straight from Saim's Stage 1 `top`; `verdict` and `usable_frontage_ft`
are the swarm's validated outputs (our `Verdict` now carries `lon`/`lat`); `dist_to_power_m` and
`est_make_ready_usd` come from Stage 1 `candidates`. The CAD pipeline reads this to (a) select the
LiDAR tile + aim the ROI at that location and (b) place the charger at that curb. One json per
location in the report.

## How it fits the whole product (PLAN.md §4 architecture)

```
Stage 1 SCREEN (Saim)  ->  Stage 1.5 OBSTRUCTION CV/SAM3 (Max)  ->  Stage 2 SWARM (swarm lane)
picks the winner  ->  Stage 3 INTERACTIVE (this, CAD): reconstruct the winner's curb from the
Cyvl scan + place the EV charger in it -> Autodesk APS Viewer (movable), with the SDK viewer as
the light fallback and a Civil 3D export as the build-ready artifact.
```

Frontend (Thomas) drives the map and opens Stage 3 on the winner. CAD consumes only the tiny
winner handoff below; it does not screen, measure, or judge.

## Status — how it's going

- **Read and understood** Xavier's repo end to end; the integration is genuinely small (the ~15
  lines above) because his pipeline already does the hard part.
- **Not yet run here.** It needs setup we don't have on this machine yet:
  - **PDAL** must come from conda (`conda install -c conda-forge pdal python-pdal`); it fails on
    pip/macOS. Do this first; it's the main setup hazard.
  - **APS credentials** (`APS_CLIENT_ID` / `APS_CLIENT_SECRET`) in `.env`, separate from the
    Anthropic key. Xavier can hand us working ones since he built it.
  - Pull the winner's LAZ tile + `pavements_v2` / `aboveGroundAssets_v2` / `streetviewImagePaths_v2`
    from the public `cyvl-hackathon` S3 bucket.
- **Plan is set** (sections above). Next action is environment + APS creds, then prove the round
  trip with `write_dummy_scene()`, then add the EV station, then bake the demo site.

## Demo safety

The full 110M-point pipeline will not run reliably live. Pre-bake one winning site: run the
pipeline, upload, get the URN, paste it into the viewer. **Bump the OSS object key every re-bake**
(`scene_cad_vN.zip`) or APS serves the stale cached model. Live demo: swarm picks the winner → cut
to the pre-baked Autodesk Viewer of that block with the station at the curb → move it / toggle the
point cloud overlay.

## Honest limitations (Xavier's notes, don't fight them)

- APS Viewer has no native point cloud; the raw cloud is a three.js overlay (visual only).
- Street-side scan sees facades only: cars are heuristic, buildings are extruded footprints. Our EV
  station is placed from the exact swarm winner coordinate, so it's precise regardless.
- This is real Cyvl scan data — no mock geometry on the demo path.

## Build order (when we pick this up)

1. Sibling-clone `xavier-cyvl/hackathonBuckets`, conda env + PDAL, APS creds in `.env`.
2. Prove the dummy round trip (`write_dummy_scene()` → upload → translate → viewer).
3. Add `ev_station_objects` + a `MATERIALS` entry; re-run dummy with a station, confirm it's
   selectable and movable in the viewer.
4. Pick the demo winner; pull its tile + vectors; run `run.py` with `SONDER_WINNER` + ROI center.
5. Wire the swarm winner → handoff json (a few lines in the swarm `service.py`).
6. Pre-bake, paste the URN, rehearse the swarm → viewer cut.
7. (Stretch) viewer click-to-place.
