"""Public interface for the screening stage.

    from screening import screen
    result = screen(region=[-71.108, 42.388, -71.099, 42.397],
                    filters={"station_size": "small", "weights": {"power": 0.5}},
                    top_n=25)

`result` is a plain dict, JSON serializable, with three keys:
  - candidates: a GeoJSON FeatureCollection, one feature per segment, each with
    score, verdict, gate info, the component breakdown, and the raw measured
    features. Sorted best first.
  - top: the top_n candidate ids and centroids, the hand-off to Stage 2.
  - summary: counts and the echoed region and filters.

This is the only thing other sections or a frontend need to import. Everything
under it (data source, geometry, scoring) can change without breaking callers.
"""
from __future__ import annotations

import json

from . import config, data
from .features import build_candidates, normalize_region
from .scoring import Filters, score_candidates

_FEATURE_PROPS = [
    "cand_id", "address_st", "score", "verdict", "gated", "gate_reasons", "components",
    "pci", "label", "length_ft", "road_width_ft", "dist_to_power_m", "dist_to_ramp_m",
    "obstruction_count", "disqualify_marking", "functional_class",
    "residential_suit", "traffic_suit", "est_make_ready_usd", "connection_cost_band",
]


def _coerce_filters(filters) -> Filters:
    if filters is None:
        return Filters()
    if isinstance(filters, Filters):
        return filters
    if isinstance(filters, dict):
        return Filters(
            station_size=filters.get("station_size", config.DEFAULT_SIZE),
            weights=filters.get("weights", {}) or {},
            required_frontage_ft=filters.get("required_frontage_ft"),
            demand_mix=filters.get("demand_mix", config.DEFAULT_DEMAND_MIX),
        )
    raise TypeError("filters must be a Filters, a dict, or None")


def _clean(value):
    """Make a value JSON safe (handle NaN, inf, numpy scalars)."""
    try:
        import math
        if isinstance(value, float):
            if math.isnan(value):
                return None
            if math.isinf(value):
                return None
    except Exception:
        pass
    if hasattr(value, "item"):  # numpy scalar
        return value.item()
    return value


def _to_feature_collection(gdf):
    features = []
    for _, row in gdf.iterrows():
        geom = row.geometry
        props = {k: _clean(row.get(k)) for k in _FEATURE_PROPS if k in gdf.columns}
        features.append({
            "type": "Feature",
            "geometry": geom.__geo_interface__ if geom is not None else None,
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


def screen(region=None, filters=None, top_n: int = 25, layers: dict | None = None) -> dict:
    """Screen a region and return ranked candidate curb segments.

    region: bbox [w,s,e,n], a GeoJSON geometry dict, or a shapely geometry. None
            uses the demo region.
    filters: a Filters, a dict, or None.
    top_n: how many finalists to surface for Stage 2.
    layers: pre-loaded {name: GeoDataFrame} (skips data loading; handy for tests).
    """
    bbox, _ = normalize_region(region)
    flt = _coerce_filters(filters)

    if layers is None:
        layers = data.load_layers(("pavements", "assets", "markings"), bbox=bbox)
        fclass = data.load_functional_class()
    else:
        fclass = layers.get("_functional_class")

    candidates = build_candidates(layers, region=region, functional_class=fclass)
    scored = score_candidates(candidates, flt)

    fc = _to_feature_collection(scored)

    top = []
    for _, row in scored.head(top_n).iterrows():
        c = row.geometry.centroid if row.geometry is not None else None
        top.append({
            "cand_id": row.get("cand_id"),
            "address_st": _clean(row.get("address_st")),
            "score": _clean(row.get("score")),
            "verdict": row.get("verdict"),
            "lon": round(c.x, 6) if c is not None else None,
            "lat": round(c.y, 6) if c is not None else None,
        })

    verdicts = list(scored["verdict"]) if len(scored) else []
    summary = {
        "n_candidates": int(len(scored)),
        "n_go": verdicts.count("Go"),
        "n_conditional": verdicts.count("Conditional"),
        "n_nogo": verdicts.count("No-go"),
        "region_bbox": bbox,
        "filters": {
            "station_size": flt.station_size,
            "required_frontage_ft": flt.required_frontage(),
            "demand_mix": flt.demand_mix,
            "weights": flt.resolved_weights(),
        },
    }

    return {"candidates": fc, "top": top, "summary": summary}


def to_geojson_str(result: dict) -> str:
    """Serialize just the candidates FeatureCollection (for QGIS, etc.)."""
    return json.dumps(result["candidates"])
