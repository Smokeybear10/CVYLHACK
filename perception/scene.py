"""Scene access and geometry helpers around the cyvl spatial SDK.

The scene is loaded once and reused. All world coordinates are UTM 19N meters
(the scan's native frame); we convert lon/lat at the boundary only.
"""
from __future__ import annotations

import functools

import numpy as np
from pyproj import Transformer

from . import config

_to_utm = Transformer.from_crs(config.WGS84, config.UTM_EPSG, always_xy=True)
_to_wgs = Transformer.from_crs(config.UTM_EPSG, config.WGS84, always_xy=True)


def lonlat_to_utm(lon: float, lat: float) -> tuple[float, float]:
    x, y = _to_utm.transform(lon, lat)
    return float(x), float(y)


def utm_to_lonlat(x: float, y: float) -> tuple[float, float]:
    lon, lat = _to_wgs.transform(x, y)
    return float(lon), float(lat)


@functools.lru_cache(maxsize=1)
def get_scene():
    """Load the Somerville scene once (downloads + caches frame/LiDAR index)."""
    import cyvl
    return cyvl.load_scene(config.SCENE_NAME)


def nearest_frame(lon: float, lat: float):
    """Closest posed camera frame to a coordinate."""
    return get_scene().nearest_frame(lon, lat)


def sample_ground_z(frame, x: float, y: float, search_m: float = 3.0) -> float | None:
    """Altitude (UTM z) of the LiDAR ground near (x, y), for projecting a point."""
    p = frame.points_in_view()
    utm = p.points_utm
    near = (np.abs(utm[:, 0] - x) < search_m) & (np.abs(utm[:, 1] - y) < search_m)
    if not near.any():
        return None
    cand = utm[near]
    d2 = (cand[:, 0] - x) ** 2 + (cand[:, 1] - y) ** 2
    return float(cand[int(np.argmin(d2)), 2])


def project_point(frame, lon: float, lat: float):
    """Project a lon/lat (snapped to LiDAR ground) into the frame.

    Returns (px_x, px_y, in_view: bool) or None if the point has no LiDAR nearby.
    """
    x, y = lonlat_to_utm(lon, lat)
    z = sample_ground_z(frame, x, y)
    if z is None:
        return None
    proj = frame.project(xyz=np.array([[x, y, z]]))
    px = proj.pixels[0]
    in_view = bool(proj.in_view[0])
    return float(px[0]), float(px[1]), in_view
