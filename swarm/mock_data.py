"""Stub finalists + measurements standing in for Saim's Stage 1 and Max's CV.

Realistic Somerville coordinates and a spread of outcomes (clear go, conditional via a curbside
conflict, no-go via fit/power) so the swarm demo is coherent before the other layers land.
Photo URLs are real Cyvl CDN frames so the real-model path has an image to look at.
"""
from __future__ import annotations

from .schema import SiteInput, Measurements, UserPriorities

_PHOTO_A = "https://dcygqrjfsypox.cloudfront.net/delivery/delivery/GX040766_MP4_1763491887081105_front_3000__ann_19.jpg"
_PHOTO_B = "https://dcygqrjfsypox.cloudfront.net/0e9ad4538ce0a1b7876a5bcfd6275a942b2f92472dfa4b85e93f424eb4a62eda/pavements_masks_001/GX050766_MP4_1763497396974040_front_3000.jpg"


def priorities() -> UserPriorities:
    return UserPriorities(station_size="curbside_l2", required_frontage_ft=18.0,
                          weights={"power": 1.0, "traffic": 0.8, "fit": 1.2})


def finalists() -> list[SiteInput]:
    return [
        SiteInput("seg_001", "Elm St near Davis Sq", -71.1221, 42.3966, 0.88,
                  {"fit": 0.9, "power": 0.95, "traffic": 0.8, "pavement": 0.85},
                  "Good", 84, "collector", 9800, 12.0, 8.0, "Good", 0,
                  {"fire_lane": False, "no_parking": False, "bus_stop": False}, 26.0),
        SiteInput("seg_002", "Highland Ave @ bus stop", -71.1015, 42.3884, 0.81,
                  {"fit": 0.85, "power": 0.8, "traffic": 0.9, "pavement": 0.7},
                  "Satisfactory", 74, "arterial", 14200, 16.0, 12.0, "Fair", 1,
                  {"fire_lane": False, "no_parking": False, "bus_stop": True}, 30.0),
        SiteInput("seg_003", "Summer St narrow frontage", -71.0995, 42.3878, 0.62,
                  {"fit": 0.4, "power": 0.8, "traffic": 0.6, "pavement": 0.7},
                  "Satisfactory", 72, "local", 3100, 14.0, 20.0, "Fair", 0,
                  {"fire_lane": False, "no_parking": True, "bus_stop": False}, 18.0),
        SiteInput("seg_004", "Beacon St near Union Sq", -71.0966, 42.3795, 0.79,
                  {"fit": 0.8, "power": 0.7, "traffic": 0.85, "pavement": 0.75},
                  "Satisfactory", 76, "arterial", 16800, 22.0, 10.0, "Good", 1,
                  {"fire_lane": False, "no_parking": False, "bus_stop": False}, 28.0),
        SiteInput("seg_005", "Washington St far from power", -71.0939, 42.3811, 0.58,
                  {"fit": 0.8, "power": 0.2, "traffic": 0.8, "pavement": 0.6},
                  "Fair", 63, "collector", 8800, 41.0, 15.0, "Fair", 0,
                  {"fire_lane": False, "no_parking": False, "bus_stop": False}, 24.0),
        SiteInput("seg_006", "Broadway failed pavement", -71.0980, 42.3990, 0.45,
                  {"fit": 0.7, "power": 0.7, "traffic": 0.7, "pavement": 0.1},
                  "Serious", 18, "arterial", 19500, 13.0, 18.0, "Poor", 2,
                  {"fire_lane": False, "no_parking": False, "bus_stop": False}, 27.0),
    ]


def measurements() -> dict[str, Measurements]:
    m = {
        "seg_001": Measurements("seg_001", 22.5, 12.0, [], 5.5, _PHOTO_A, _PHOTO_A, 0.92),
        "seg_002": Measurements("seg_002", 20.0, 16.0, [{"type": "bus shelter", "offset_ft": 2.0}],
                                5.0, _PHOTO_A, _PHOTO_A, 0.88),
        "seg_003": Measurements("seg_003", 11.0, 14.0, [], 3.0, _PHOTO_B, _PHOTO_B, 0.8),
        "seg_004": Measurements("seg_004", 19.5, 22.0, [{"type": "hydrant", "offset_ft": 4.0}],
                                5.2, _PHOTO_A, _PHOTO_A, 0.85),
        "seg_005": Measurements("seg_005", 21.0, 41.0, [], 5.0, _PHOTO_B, _PHOTO_B, 0.83),
        "seg_006": Measurements("seg_006", 20.0, 13.0, [{"type": "pothole", "offset_ft": 1.0}],
                                4.8, _PHOTO_B, _PHOTO_B, 0.79),
    }
    return m
