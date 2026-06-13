"""Default obstruction source: Cyvl's detected above-ground assets.

Real, reliable, no fal.ai. Loads the asset layer once (the same one screening
uses), keeps the blocker types (hydrant, tree, catch basin, ...), and for a curb
segment returns the ones sitting on or near its frontage, with footprints so the
usable-frontage subtraction is honest. SAM3 (segment.py) is the optional upgrade
for blockers the asset layer cannot see (driveways, bus stops).
"""
from __future__ import annotations

import functools

import numpy as np

from . import config, scene


@functools.lru_cache(maxsize=1)
def _blocker_points():
    """All obstruction-type assets as (labels, utm_x, utm_y). Loaded once."""
    from screening import data

    gdf = data.load_layer("assets")  # whole city; ~8k points, small
    labels: list[str] = []
    lons: list[float] = []
    lats: list[float] = []
    for _, row in gdf.iterrows():
        at = row.get("asset_type")
        geom = row.geometry
        if at in config.OBSTRUCTION_ASSET_TYPES and geom is not None and geom.geom_type == "Point":
            labels.append(at)
            lons.append(geom.x)
            lats.append(geom.y)
    if not labels:
        return [], np.empty(0), np.empty(0), np.empty(0), np.empty(0)
    ux, uy = scene._to_utm.transform(np.array(lons), np.array(lats))
    return labels, np.array(lons), np.array(lats), np.asarray(ux), np.asarray(uy)


def _seg_distances(ux, uy, a, b):
    """Vectorized distance (m) from points to segment a-b (UTM)."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom == 0:
        return np.hypot(ux - ax, uy - ay)
    t = ((ux - ax) * dx + (uy - ay) * dy) / denom
    t = np.clip(t, 0.0, 1.0)
    cx, cy = ax + t * dx, ay + t * dy
    return np.hypot(ux - cx, uy - cy)


def find_obstructions(endpoints) -> list[dict]:
    """Obstruction-type assets within NEARBY_M of the curb segment, tagged.

    Each: {label, lon, lat, offset_m, on_segment, source}.
    """
    if endpoints is None:
        return []
    labels, lons, lats, ux, uy = _blocker_points()
    if len(labels) == 0:
        return []
    (alon, alat), (blon, blat) = endpoints
    a = scene.lonlat_to_utm(alon, alat)
    b = scene.lonlat_to_utm(blon, blat)
    dist = _seg_distances(ux, uy, a, b)
    near = np.where(dist <= config.NEARBY_M)[0]
    out = []
    for i in near:
        out.append({
            "label": labels[i],
            "lon": float(lons[i]),
            "lat": float(lats[i]),
            "offset_m": round(float(dist[i]), 2),
            "on_segment": bool(dist[i] <= config.ON_SEGMENT_M),
            "source": "cyvl-asset",
        })
    out.sort(key=lambda o: o["offset_m"])
    return out
