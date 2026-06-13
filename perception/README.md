# Perception stage (Stage 1.5, the obstruction filter)

Takes the screening finalists and measures each one from Cyvl's 3D scan: usable
frontage, obstructions the point-asset layer misses, and distance to power, with a
refined Go / Conditional / No-go and an annotated evidence photo. This is the
truck-roll replacement, and the real CV that defends against "Google Maps clone."

Stage 1 (`screening/`) ranks. Stage 1.5 (here) measures and narrows. Stage 2 (the
agent swarm) reads these measurements and writes the final verdict.

## Interface (all a frontend or the swarm needs)

```python
from screening import screen
from perception import perceive_finalists, perceive

result = screen(region=[-71.1015, 42.384, -71.0976, 42.396], top_n=25)
sites = perceive_finalists(result, limit=10)   # measure the finalists
# or one candidate feature at a time:
site = perceive(result["candidates"]["features"][0])
```

`perceive_finalists` uses `result["top"]` to pick which finalists and
`result["candidates"]` for the geometry it measures. Both functions return plain
JSON-serializable dicts.

## Output schema (one site)

```jsonc
{
  "cand_id": "…",
  "station_size": "small",
  "required_frontage_ft": 20.0,
  "screening_verdict": "Go",          // what Stage 1 thought
  "measured": true,
  "method": "sam3" | "lidar" | "geometry",  // how the measurement was obtained
  "frame_id": "…",
  "image_url": "https://…",           // the street photo used
  "segment_frontage_ft": 31.2,        // measured length of the curb segment
  "frontage_source": "scan" | "geometry",
  "usable_frontage_ft": 19.2,         // segment minus on-curb blockers
  "fits_station": false,
  "dist_to_power_m": 18.0,
  "power_source": "sam3" | "screening",
  "obstructions": [                   // [] unless SAM3 ran
    {"label": "driveway curb cut", "lon": …, "lat": …, "distance_m": 7.4,
     "on_segment": true, "offset_m": 1.2, "source": "sam3"}
  ],
  "obstruction_count": 1,
  "sam_used": true,
  "refined_verdict": "No-go",         // narrows the screening verdict
  "flags": ["verify on site: grid capacity", "…zoning", "…host willingness", "…final permit"],
  "evidence_image_path": "perception/_evidence/<cand_id>.png",
  "notes": [ … ]
}
```

## What is real vs flagged (matches PLAN.md honesty lines)

- Real, no key: frontage and distances measured off the LiDAR through the
  calibrated camera (`cyvl.measure`, `frame.project/unproject`). Falls back to the
  segment's own Cyvl geometry length when the endpoints are outside the frame view.
- Real, needs `FAL_KEY`: SAM3 (`cyvl.segment.locate`) discovers blockers the asset
  layer misses (driveways, bus stops, loading zones, construction) and locates the
  power asset, lifted to 3D. Without the key the pipeline still measures with LiDAR
  and marks `sam_used: false` and the verdict `Conditional` (we did not fully verify
  blockers). Never faked.
- Flagged, never claimed: grid capacity, zoning, host willingness, final permit.

## Run

```bash
uv pip install -r perception/requirements.txt      # or pip
export FAL_KEY=…          # optional; enables SAM3 obstruction discovery
python -m pytest tests/test_perception.py -q                 # 9 unit tests
PERCEPTION_SDK_TEST=1 python -m pytest tests/test_perception.py -q   # + live scene
```

Measurements cache to `perception/_cache/<cand_id>.json` and evidence images to
`perception/_evidence/` (both gitignored), so a pre-warmed demo region loads
instantly and never fails live.

## Boundaries

No screening logic (that is Stage 1), no agent / verdict prose (that is Stage 2),
no frontend. The output dict is the contract; everything under it can change.
