"""Config for the perception stage (Stage 1.5, the obstruction filter).

Real measurement from Cyvl's 3D scan. SAM3 obstruction discovery runs when FAL_KEY
is set; the LiDAR measurement path is always real and needs no key.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SCENE_NAME = os.getenv("CYVL_SCENE", "somerville")
FAL_KEY = os.getenv("FAL_KEY", "")

# UTM zone the Somerville scan uses (UTM 19N). Frames expose .utm_epsg too.
UTM_EPSG = "EPSG:32619"
WGS84 = "EPSG:4326"

# Required usable frontage (ft) by station size. Matches screening: 1 / 2 / 4 ports
# at a ~20-22 ft on-street parallel space (ADA EV space is 11 x 20 ft).
STATION_FRONTAGE_FT = {"small": 20.0, "medium": 42.0, "large": 84.0}
DEFAULT_STATION = "small"

# Beyond this a curbside connection is uneconomic (mirrors screening's hard gate).
POWER_MAX_M = 100.0

# SAM3 text prompts. These are blockers the Cyvl point-asset layer does NOT fully
# carry (driveways, bus stops, loading zones, active construction). Hydrants/trees
# already come from the asset layer; we keep a couple as a cross-check.
OBSTRUCTION_PROMPTS = [
    "driveway curb cut",
    "bus stop",
    "loading zone",
    "construction barrier",
    "fire hydrant",
]
POWER_PROMPT = "utility pole"

# Rough on-curb footprint each blocker eats from usable frontage (ft).
FOOTPRINT_FT = {
    "driveway curb cut": 12.0,
    "bus stop": 40.0,
    "loading zone": 30.0,
    "construction barrier": 20.0,
    "fire hydrant": 5.0,
    "_default": 10.0,
}

# An obstruction counts against a segment if it sits within this distance of it.
ON_SEGMENT_M = 4.0

_HERE = Path(__file__).resolve().parent
CACHE_DIR = Path(os.getenv("PERCEPTION_CACHE", _HERE / "_cache"))
EVIDENCE_DIR = Path(os.getenv("PERCEPTION_EVIDENCE", _HERE / "_evidence"))


def sam_available() -> bool:
    """SAM3 obstruction discovery needs the fal.ai key and the cyvl[sam] extra."""
    if not FAL_KEY:
        return False
    try:
        import cyvl.segment  # noqa: F401
        return True
    except Exception:
        return False


def required_frontage_ft(station_size: str) -> float:
    return STATION_FRONTAGE_FT.get(station_size, STATION_FRONTAGE_FT[DEFAULT_STATION])


def footprint_ft(label: str) -> float:
    return FOOTPRINT_FT.get(label, FOOTPRINT_FT["_default"])
