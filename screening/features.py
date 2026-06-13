"""Candidate generation and spatial enrichment.

Turns the raw layers into one row per candidate curb segment, with the measured
inputs the score needs: distance to power, ADA ramp distance, obstruction count,
disqualifying markings, derived road width, pavement condition, and road class.

All distance math is done in UTM 19N (meters). Output is returned in WGS84.
"""
from __future__ import annotations

import math

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

from . import config


def _cost_estimate(dist_m):
    """Rough make-ready cost and band from the trench distance to power.

    Returns (usd or None, band). Informational only; not used for gating.
    """
    if dist_m is None or math.isinf(dist_m) or math.isnan(dist_m):
        return None, "unknown"
    trench_ft = dist_m * 3.281
    usd = config.MAKE_READY_BASE_USD + trench_ft * config.TRENCH_COST_PER_FT
    if usd <= config.COST_BAND_LOW_USD:
        band = "low"
    elif usd >= config.COST_BAND_HIGH_USD:
        band = "high"
    else:
        band = "moderate"
    return round(usd, -2), band


def normalize_region(region):
    """Accept a bbox [w,s,e,n], a shapely geometry, or a GeoJSON geometry dict.

    Returns (bbox, geom) where bbox is [w,s,e,n] for cheap layer clipping and
    geom is a shapely polygon for precise filtering (None if a plain bbox).
    """
    if region is None:
        return config.DEMO_BBOX, None
    if isinstance(region, (list, tuple)) and len(region) == 4:
        return list(region), None
    if isinstance(region, dict):  # GeoJSON geometry
        geom = shape(region)
        return list(geom.bounds), geom
    if hasattr(region, "bounds"):  # shapely geometry
        return list(region.bounds), region
    raise ValueError("region must be a bbox [w,s,e,n], a GeoJSON geometry dict, or a shapely geometry")


def _nearest_distance_m(left_utm: gpd.GeoDataFrame, right_utm: gpd.GeoDataFrame, col: str) -> pd.Series:
    """Distance in meters from each left geometry to the nearest right geometry.

    Returns a Series aligned to left_utm.index. Infinity where right is empty.
    """
    if len(right_utm) == 0 or len(left_utm) == 0:
        return pd.Series(float("inf"), index=left_utm.index, name=col)
    joined = gpd.sjoin_nearest(left_utm[["geometry"]], right_utm[["geometry"]], distance_col=col)
    # sjoin_nearest can emit ties (multiple rows per left); keep the minimum.
    return joined.groupby(joined.index)[col].min().reindex(left_utm.index).fillna(float("inf"))


def _count_within(left_utm: gpd.GeoDataFrame, points_utm: gpd.GeoDataFrame, buffer_m: float) -> pd.Series:
    """Count point features within buffer_m of each left geometry."""
    if len(points_utm) == 0 or len(left_utm) == 0:
        return pd.Series(0, index=left_utm.index)
    buffered = left_utm[["geometry"]].copy()
    buffered["geometry"] = buffered.geometry.buffer(buffer_m)
    joined = gpd.sjoin(buffered, points_utm[["geometry"]], predicate="intersects")
    counts = joined.groupby(joined.index).size()
    return counts.reindex(left_utm.index).fillna(0).astype(int)


def _any_within(left_utm: gpd.GeoDataFrame, feats_utm: gpd.GeoDataFrame, buffer_m: float) -> pd.Series:
    """True where any feature lies within buffer_m of the left geometry."""
    return _count_within(left_utm, feats_utm, buffer_m) > 0


def build_candidates(layers: dict, region=None, functional_class: pd.DataFrame | None = None) -> gpd.GeoDataFrame:
    """Build the enriched candidate table.

    layers: {"pavements","assets","markings"} as GeoDataFrames (EPSG:4326).
    region: bbox / geometry; pavements are filtered to it.
    functional_class: optional inspect_cell_id -> fhwa_functional_class frame.

    Returns a GeoDataFrame (EPSG:4326), one row per candidate, with feature columns.
    """
    bbox, geom = normalize_region(region)

    pav = layers["pavements"]
    if len(pav):
        w, s, e, n = bbox
        pav = pav.cx[w:e, s:n]
        if geom is not None and len(pav):
            pav = pav[pav.intersects(geom)]
    pav = pav.copy()

    # Stable candidate id. client_seg_id can repeat across segments, so prefer
    # inspect_id and fall back to the row index.
    if "inspect_id" in pav.columns:
        pav["cand_id"] = pav["inspect_id"].astype(str)
    else:
        pav["cand_id"] = pav.index.astype(str)
    pav = pav.reset_index(drop=True)

    # Empty region: return an empty, well-formed frame.
    if len(pav) == 0:
        cols = ["cand_id", "address_st", "score", "label", "length_ft", "area_sqft",
                "road_width_ft", "dist_to_power_m", "dist_to_ramp_m", "obstruction_count",
                "disqualify_marking", "functional_class", "geometry"]
        return gpd.GeoDataFrame(columns=cols, geometry="geometry", crs=config.WGS84)

    assets = layers["assets"]
    markings = layers["markings"]

    # Project everything to meters once.
    pav_utm = pav.to_crs(config.UTM_19N)
    power_utm = assets[assets["asset_type"].isin(config.POWER_TYPES)].to_crs(config.UTM_19N) if len(assets) else assets
    ramp_utm = assets[assets["asset_type"] == config.RAMP_TYPE].to_crs(config.UTM_19N) if len(assets) else assets
    obstr_utm = assets[assets["asset_type"].isin(config.OBSTRUCTION_TYPES)].to_crs(config.UTM_19N) if len(assets) else assets

    if len(markings):
        kw = "|".join(config.DISQUALIFY_MARKING_KEYWORDS)
        disq = markings[markings["type"].str.contains(kw, case=False, na=False)].to_crs(config.UTM_19N)
    else:
        disq = markings

    pav["dist_to_power_m"] = _nearest_distance_m(pav_utm, power_utm, "dist_to_power_m").values
    pav["dist_to_ramp_m"] = _nearest_distance_m(pav_utm, ramp_utm, "dist_to_ramp_m").values
    pav["obstruction_count"] = _count_within(pav_utm, obstr_utm, config.FRONTAGE_BUFFER_M).values
    pav["disqualify_marking"] = _any_within(pav_utm, disq, config.FRONTAGE_BUFFER_M).values

    # Derived road width (cartway, coarse) and tidy condition fields.
    pav["road_width_ft"] = (pav["area_sqft"] / pav["length_ft"]).where(pav["length_ft"] > 0)
    pav["pci"] = pav["score"]

    # Informational make-ready cost estimate from the trench distance to power.
    ests = [_cost_estimate(d) for d in pav["dist_to_power_m"]]
    pav["est_make_ready_usd"] = [e[0] for e in ests]
    pav["connection_cost_band"] = [e[1] for e in ests]

    # Road class (traffic proxy) by joining cells on inspect_cell_id.
    if functional_class is not None and len(functional_class) and "inspect_cell_id" in pav.columns:
        pav = pav.merge(functional_class, on="inspect_cell_id", how="left")
        pav["functional_class"] = pav["fhwa_functional_class"]
    else:
        pav["functional_class"] = pd.NA

    return gpd.GeoDataFrame(pav, geometry="geometry", crs=config.WGS84)
