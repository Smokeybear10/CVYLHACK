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
# Live SAM3 (fal.ai) is opt-in. Default obstruction source is Cyvl's detected asset
# layer (real, reliable, no fal). Set USE_FAL_SAM=1 only when the fal key actually works.
USE_FAL_SAM = os.getenv("USE_FAL_SAM", "0") == "1"

# UTM zone the Somerville scan uses (UTM 19N). Frames expose .utm_epsg too.
UTM_EPSG = "EPSG:32619"
WGS84 = "EPSG:4326"

# Required usable frontage (ft) by station size. Matches screening: 1 / 2 / 4 ports
# at a ~20-22 ft on-street parallel space (ADA EV space is 11 x 20 ft).
STATION_FRONTAGE_FT = {"small": 20.0, "medium": 42.0, "large": 84.0}
DEFAULT_STATION = "small"

# Beyond this a curbside connection is uneconomic (mirrors screening's hard gate).
POWER_MAX_M = 100.0

# Default obstruction source: Cyvl's detected above-ground assets (real, no fal).
# These mirror screening's OBSTRUCTION_TYPES: things on the curb that block a bay.
OBSTRUCTION_ASSET_TYPES = {"HYDRANT", "TREE", "CATCH_BASIN", "FLASHING_BEACONS", "BIKE_RACK"}

# Optional SAM3 (fal.ai) prompts: blockers the asset layer does NOT carry
# (driveways, bus stops, loading zones, construction). Used only when FAL_KEY works.
OBSTRUCTION_PROMPTS = [
    "driveway curb cut",
    "bus stop",
    "loading zone",
    "construction barrier",
]
POWER_PROMPT = "utility pole"

# Rough on-curb footprint each blocker eats from usable frontage (ft).
FOOTPRINT_FT = {
    # Cyvl asset-type labels
    "HYDRANT": 5.0,
    "TREE": 6.0,
    "CATCH_BASIN": 4.0,
    "FLASHING_BEACONS": 3.0,
    "BIKE_RACK": 8.0,
    # SAM3 prompt labels
    "driveway curb cut": 12.0,
    "bus stop": 40.0,
    "loading zone": 30.0,
    "construction barrier": 20.0,
    "_default": 6.0,
}

# An obstruction counts against frontage if within ON_SEGMENT_M of the segment;
# we surface ones within NEARBY_M as context.
ON_SEGMENT_M = 4.0
NEARBY_M = 8.0

_HERE = Path(__file__).resolve().parent
CACHE_DIR = Path(os.getenv("PERCEPTION_CACHE", _HERE / "_cache"))
EVIDENCE_DIR = Path(os.getenv("PERCEPTION_EVIDENCE", _HERE / "_evidence"))


def sam_available() -> bool:
    """Live SAM3 needs the opt-in flag, the fal.ai key, and the cyvl[sam] extra."""
    if not USE_FAL_SAM or not FAL_KEY:
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
