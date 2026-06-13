# Screening stage

Stage 1 of Sonder. Region in, ranked candidate curb segments out. Deterministic,
no LLM, no network at call time once the data is cached. Stage 2 (the agent swarm)
consumes the top list this produces.

## Interface (the only thing other sections / a frontend depend on)

```python
from screening import screen, Filters

result = screen(
    region=[-71.1015, 42.384, -71.0976, 42.396],   # bbox, GeoJSON polygon, or shapely geom; None = demo region
    filters={"station_size": "small", "weights": {"power": 0.5}},  # or a Filters object, or None
    top_n=25,
)
```

`result` is a plain JSON-serializable dict:

- `candidates`: GeoJSON FeatureCollection, one feature per segment, sorted best
  first. Each feature carries `score`, `verdict`, `gated`, `gate_reasons`,
  `components` (the per-factor breakdown), and the measured features
  (`dist_to_power_m`, `road_width_ft`, `pci`, `obstruction_count`,
  `functional_class`, `est_make_ready_usd`, `connection_cost_band`, ...).
- `top`: the top_n finalists (`cand_id`, `address_st`, `score`, `verdict`,
  `lon`, `lat`). This is the hand-off to Stage 2.
- `summary`: counts (`n_candidates`, `n_go`, `n_conditional`, `n_nogo`), the
  region, and the resolved filters.

The verdict here (Go / Conditional / No-go) is a preliminary screen. Stage 2
refines it with real measurement and the photo.

## How it works

1. Candidates are the pavement segments inside the region (one row each).
2. Each is enriched with distance to nearest power asset, ADA ramp distance,
   obstruction count in the frontage, disqualifying markings, derived road
   width, pavement condition, and FHWA functional class. All distance math is
   in UTM 19N.
3. Hard gates drop obvious No-gos (no power in range, frontage too small, failed
   pavement, fire-lane / no-parking marking). Survivors get a weighted score
   where the filter sliders are the weights.

## Parameters are grounded in real EV siting, not guesses

- Power distance = make-ready cost. Curbside L2 ideally mounts on an existing
  pole/streetlight; otherwise trenching runs ~$50-150+/ft. So ~50 ft is cheap,
  ~250 ft is ~$25k+, and beyond ~330 ft a curbside connection is uneconomic
  (the hard gate). `est_make_ready_usd` exposes the estimate.
- Fit = an on-street parallel charging space (~20-22 ft; ADA EV space is
  11 x 20 ft). small / medium / large require 20 / 42 / 84 ft for 1 / 2 / 4 ports.
- Demand is residential, not traffic. Curbside L2 serves residents with no
  driveway, so the road-class curve favors local and collector streets and
  penalizes major arterials (where curbside parking is usually restricted). This
  is the opposite of a DC-fast-charge curve. Real demand wants residential /
  multifamily density and off-street-parking share; road class is a proxy and a
  noted data gap to pair in later.

## Data

Source priority: REST API (when `CYVL_API_KEY` + `CYVL_PROJECT_ID` are set),
then the local cache, then the public S3 bucket over HTTPS (no credentials). The
bulk GeoJSON layers cache under `screening/_cache/` (gitignored) and are re-used.

Coverage caveat: in the delivered v2 dataset the pavement and power-asset layers
were captured over only partially overlapping areas. They share a ~900 m strip
around lon [-71.108, -71.098]; the demo region sits inside it. Distances are to
the nearest DETECTED pole, and pole detection is sparse, so treat power distance
as a relative signal.

## Run

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r screening/requirements.txt
.venv/bin/python -m pytest tests/ -q          # 26 tests; integration tests skip if no cache
.venv/bin/python -c "from screening import screen, config; print(screen(region=config.DEMO_BBOX)['summary'])"
```

## Not in this stage (boundaries)

No LLM, no SAM3, no measurement from the 3D scan (that is Stage 2), no frontend.
The REST path is wired but unverified without the team key. Stage-1 CV is left as
a future pluggable signal.
