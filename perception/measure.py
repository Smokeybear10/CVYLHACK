"""Measurement math and evidence rendering.

The pure functions (geometry, footprint subtraction, fit, verdict) have no SDK or
network dependency and are unit tested directly. The scan functions use the frame.
"""
from __future__ import annotations

import math

import numpy as np

from . import config, scene

FT_PER_M = 3.280839895
M_PER_FT = 0.3048


# --- pure geometry / scoring (unit tested, no SDK) ---

def segment_endpoints(geometry: dict) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """First and last lon/lat vertex of a (Multi)LineString GeoJSON geometry."""
    if not geometry:
        return None
    coords = geometry.get("coordinates")
    gtype = geometry.get("type")
    if gtype == "MultiLineString":
        flat = [pt for line in coords for pt in line]
    elif gtype == "LineString":
        flat = coords
    else:
        return None
    if not flat or len(flat) < 2:
        return None
    a, b = flat[0], flat[-1]
    return (float(a[0]), float(a[1])), (float(b[0]), float(b[1]))


def geom_length_ft(endpoints) -> float:
    """Planar UTM length between two lon/lat endpoints, in feet."""
    (alon, alat), (blon, blat) = endpoints
    ax, ay = scene.lonlat_to_utm(alon, alat)
    bx, by = scene.lonlat_to_utm(blon, blat)
    return math.hypot(bx - ax, by - ay) * FT_PER_M


def dist_point_to_segment_m(p, a, b) -> float:
    """Distance (m) from UTM point p to segment a-b (all (x, y) in meters)."""
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def on_segment_obstructions(obstructions, endpoints) -> list[dict]:
    """Tag obstructions that sit on the curb segment (within ON_SEGMENT_M)."""
    (alon, alat), (blon, blat) = endpoints
    a = scene.lonlat_to_utm(alon, alat)
    b = scene.lonlat_to_utm(blon, blat)
    tagged = []
    for o in obstructions:
        if o.get("lon") is None or o.get("lat") is None:
            tagged.append({**o, "on_segment": False, "offset_m": None})
            continue
        ox, oy = scene.lonlat_to_utm(o["lon"], o["lat"])
        d = dist_point_to_segment_m((ox, oy), a, b)
        oo = dict(o)
        oo["on_segment"] = d <= config.ON_SEGMENT_M
        oo["offset_m"] = round(d, 2)
        tagged.append(oo)
    return tagged


def usable_frontage_ft(segment_ft: float, tagged_obstructions) -> float:
    """Segment length minus the footprint of each on-segment blocker, clamped >= 0."""
    eaten = sum(
        config.footprint_ft(o["label"]) for o in tagged_obstructions if o.get("on_segment")
    )
    return max(0.0, segment_ft - eaten)


def fits_station(usable_ft: float, station_size: str) -> bool:
    return usable_ft >= config.required_frontage_ft(station_size)


def refined_verdict(*, fits: bool, dist_to_power_m, has_blocker: bool,
                    obstructions_checked: bool) -> str:
    """Narrow the screening verdict with the measured reality."""
    if not fits:
        return "No-go"
    if dist_to_power_m is not None and dist_to_power_m > config.POWER_MAX_M:
        return "No-go"
    if has_blocker:
        return "Conditional"
    if not obstructions_checked:
        return "Conditional"
    return "Go"


# --- scan measurement (uses the frame) ---

def measure_frontage_scan(frame, endpoints) -> tuple[float, str]:
    """Measure the segment length off the LiDAR when both endpoints are in view,
    else fall back to the planar geometry length. Returns (feet, source)."""
    geom_ft = geom_length_ft(endpoints)
    try:
        import cyvl
        (alon, alat), (blon, blat) = endpoints
        pa = scene.project_point(frame, alon, alat)
        pb = scene.project_point(frame, blon, blat)
        if pa and pb and pa[2] and pb[2]:
            m = cyvl.measure(frame, (pa[0], pa[1]), (pb[0], pb[1]))
            if m.feet and m.feet > 0:
                return float(m.feet), "scan"
    except Exception:
        pass
    return geom_ft, "geometry"


def render_evidence(frame, endpoints, obstructions, out_path) -> str | None:
    """Save the street photo with the measured frontage line and obstruction pins."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        img = np.asarray(frame.image())
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.imshow(img)
        ax.axis("off")

        (alon, alat), (blon, blat) = endpoints
        pa = scene.project_point(frame, alon, alat)
        pb = scene.project_point(frame, blon, blat)
        if pa and pb:
            ax.plot([pa[0], pb[0]], [pa[1], pb[1]], "-", color="#00e0ff", linewidth=3)
            ax.text(pa[0], pa[1], " usable frontage", color="#00e0ff", fontsize=11)
        for o in obstructions:
            pp = scene.project_point(frame, o["lon"], o["lat"])
            if pp and pp[2]:
                ax.plot(pp[0], pp[1], "o", color="#ff3b30", markersize=10)
                ax.text(pp[0], pp[1], " " + o["label"], color="#ff3b30", fontsize=10)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, bbox_inches="tight", dpi=90)
        plt.close(fig)
        return str(out_path)
    except Exception:
        return None
