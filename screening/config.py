"""Configuration for the screening stage.

All tunables live here: data sources, asset classification, scoring bands, and the
demo region. Other sections and any frontend should not need to read this; they call
screen() and get a result back.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- data sources -----------------------------------------------------------
S3_BASE = "https://cyvl-hackathon.s3.amazonaws.com"
REST_BASE = "https://i3.cyvl.app"

# Local cache for the bulk GeoJSON layers. Override with CYVL_DATA_DIR.
CACHE_DIR = Path(os.environ.get("CYVL_DATA_DIR", Path(__file__).resolve().parent / "_cache"))

# logical layer name -> object key in the public bucket
LAYER_KEYS = {
    "pavements": "data/pavements_v2.geojson",
    "assets": "data/aboveGroundAssets_v2.geojson",
    "markings": "data/sam_v2.geojson",
}
CELLS_KEY = "parquet/layers/distressInspectionCells.parquet"

# REST endpoints, used only when CYVL_API_KEY is set (live, per-bbox). Untested
# without the team key; the cache/S3 path is the verified one.
REST_ENDPOINTS = {
    "pavements": "/api/v1/pavement/scores",
    "assets": "/api/v1/assets",
    "markings": "/api/v1/markings",
}

# --- coordinate systems ------------------------------------------------------
WGS84 = 4326
UTM_19N = 32619  # meters, correct zone for Somerville; used for all distance math

# --- asset classification ----------------------------------------------------
# Interconnection proxies. For a curbside charger the nearest of these is the
# real connection point, so the minimum distance to any of them is the signal.
POWER_TYPES = {"UTILITY_POLE", "LUMINARIES", "TRAFFIC_SIGNAL_POLE"}
RAMP_TYPE = "RAMP"
# Physical things that eat into usable curb frontage.
OBSTRUCTION_TYPES = {"HYDRANT", "TREE", "CATCH_BASIN", "FLASHING_BEACONS", "BIKE_RACK"}

# Marking types whose presence on a segment constrains curbside use. Matched as
# case-insensitive substrings against the marking `type` field.
DISQUALIFY_MARKING_KEYWORDS = ["FIRE", "NO PARKING"]

# --- scoring bands -----------------------------------------------------------
# Power distance maps directly to make-ready cost. A curbside L2 charger ideally
# mounts on an existing pole/streetlight (run ~0); otherwise you trench at roughly
# $50-150+/ft with surface restoration. So ~15 m (~50 ft) is a cheap run (~$5-7k),
# ~75 m (~250 ft) is ~$25k+ and uneconomic for L2, and beyond ~100 m a curbside
# connection generally does not pencil out. Distances are to the nearest DETECTED
# pole/luminaire, and detection is sparse (see DATA notes), so treat as a relative
# signal. Sources: trenching cost guides; curbside programs mount on existing poles.
POWER_GATE_M = 100.0  # ~330 ft; beyond this a curbside L2 connection is uneconomic -> No-go
POWER_FULL_M = 15.0   # ~50 ft, mountable or a short cheap run -> full score
POWER_ZERO_M = 75.0   # ~250 ft, make-ready ~$25k+ -> zero score
FRONTAGE_BUFFER_M = 4.5   # ~15 ft, the hydrant/clearance zone around a charging space
FAILED_LABEL = "Failed"   # pavement label that hard-fails (trench/restoration risk)
OBSTRUCTION_FULL_PENALTY_AT = 4  # this many blockers in the frontage -> full penalty

# Make-ready cost estimate from trench distance (informational, shown in the report).
TRENCH_COST_PER_FT = 120.0     # mid of the $50-150+/ft street-trenching range
MAKE_READY_BASE_USD = 6000.0   # rough equipment + permit + connection baseline
COST_BAND_LOW_USD = 12000.0    # <= this -> "low"
COST_BAND_HIGH_USD = 30000.0   # >= this -> "high"; between -> "moderate"

# Curbside demand suitability by FHWA functional class. NOTE: curbside L2 serves
# residents who park on-street with no driveway, so demand is RESIDENTIAL, not
# vehicle volume. Local and collector residential streets are the target; major
# arterials and freeways are poor (curbside parking is usually restricted there).
# This curve is the OPPOSITE of a DC-fast-charge curve. True demand would use
# residential / multifamily density and off-street-parking share (a data gap to
# pair in later); road class is the available proxy. 1 interstate ... 7 local.
FCLASS_TRAFFIC = {1: 0.10, 2: 0.15, 3: 0.30, 4: 0.55, 5: 0.90, 6: 1.0, 7: 0.85}
DEFAULT_TRAFFIC_SCORE = 0.6  # used when functional class is missing

# Component weights, reflecting what curbside siting actually prioritizes:
# electrical feasibility first, then residential demand, then physical fit, then
# accessibility and clearances; pavement is minor (trench-restoration cost only).
# The filter sliders override these; values are normalized to sum to 1.
DEFAULT_WEIGHTS = {
    "power": 0.30,
    "traffic": 0.25,   # curbside (residential) demand suitability
    "fit": 0.20,
    "ada": 0.10,
    "obstruction": 0.10,
    "pavement": 0.05,
}

# Station size -> required usable curb frontage in feet. Grounded in an on-street
# parallel charging space of ~20-22 ft (ADA EV space is 11 x 20 ft). 1 / 2 / 4 ports.
# Stage 1 fit is coarse (segment length stands in for curb frontage); Stage 2
# measures the true frontage from the scan.
SIZE_FRONTAGE_FT = {"small": 20.0, "medium": 42.0, "large": 84.0}
DEFAULT_SIZE = "small"

# Preliminary screening verdict thresholds. Stage 2 produces the final verdict.
GO_THRESHOLD = 70.0
CONDITIONAL_THRESHOLD = 45.0

# --- region ------------------------------------------------------------------
# DATA coverage notes (verified against the delivered v2 dataset):
#   pavements span lon [-71.121, -71.098]  (central / west, not Davis Square)
#   power assets span lon [-71.109, -71.077]  (east)
# The two layers were captured over only partially overlapping areas. They share
# a ~900 m strip around lon [-71.108, -71.098]; west of it there are roads but
# almost no detected poles. The demo region must sit in that overlap.
DATA_BOUNDS = [-71.1209, 42.3816, -71.0976, 42.4021]
# Default demo box inside the overlap strip (verified: ~411 candidates with a
# healthy Go / Conditional / No-go spread).
DEMO_BBOX = [-71.1015, 42.3840, -71.0976, 42.3960]
