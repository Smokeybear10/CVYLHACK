"""Data access layer.

Source priority, in order:
  1. Cyvl REST API, if CYVL_API_KEY (and CYVL_PROJECT_ID) are set. Live, per bbox.
  2. Local cache files under CACHE_DIR.
  3. The public S3 bucket over plain HTTPS, downloaded once into the cache.

Every layer comes back as a GeoDataFrame in EPSG:4326. The rest of the package and
any frontend depend only on screen(); this module is the single place that knows
where bytes come from, so swapping to the team REST key at kickoff changes nothing
downstream.
"""
from __future__ import annotations

import logging
import os

import geopandas as gpd
import pandas as pd
import requests

from . import config

log = logging.getLogger("screening.data")


class DataUnavailable(RuntimeError):
    """Raised when no source could supply a layer. Mentions the offline fallback."""


# --- low level ---------------------------------------------------------------

def _cache_file(key: str):
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return config.CACHE_DIR / os.path.basename(key)


def _download_to_cache(key: str):
    """Download one object from the public bucket into the cache, return its path."""
    url = f"{config.S3_BASE}/{key}"
    dest = _cache_file(key)
    log.info("downloading %s -> %s", url, dest)
    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
        tmp.replace(dest)
    return dest


def _read_geojson(path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(config.WGS84)
    elif gdf.crs.to_epsg() != config.WGS84:
        gdf = gdf.to_crs(config.WGS84)
    return gdf


# --- REST path (used only when a key is present) -----------------------------

def _rest_available() -> bool:
    return bool(os.environ.get("CYVL_API_KEY") and os.environ.get("CYVL_PROJECT_ID"))


def _load_from_rest(name: str, bbox) -> gpd.GeoDataFrame:
    """Fetch one layer from the REST API, paginating to the end.

    Only reached when CYVL_API_KEY and CYVL_PROJECT_ID are set. Not exercised
    without the team key; if anything goes wrong we raise and the caller falls
    back to the cache/S3 path.
    """
    endpoint = config.REST_ENDPOINTS[name]
    headers = {"Authorization": f"Bearer {os.environ['CYVL_API_KEY']}"}
    params = {
        "project_id": os.environ["CYVL_PROJECT_ID"],
        "bbox": ",".join(str(x) for x in bbox),
        "limit": 200,
        "include_geometry": "true",
    }
    feats: list = []
    cursor = None
    while True:
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(config.REST_BASE + endpoint, headers=headers, params=params, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        feats.extend(body.get("features", []))
        page = body.get("pagination", {})
        cursor = page.get("cursor")
        if not page.get("has_more") or not cursor:
            break
    gdf = gpd.GeoDataFrame.from_features(feats, crs=config.WGS84) if feats else gpd.GeoDataFrame(geometry=[], crs=config.WGS84)
    return gdf


# --- public ------------------------------------------------------------------

def load_layer(name: str, bbox=None) -> gpd.GeoDataFrame:
    """Load a single layer (pavements, assets, markings) as a GeoDataFrame.

    Tries REST first when a key is present, then the local cache, then S3. If
    bbox is given the layer is clipped to it (west, south, east, north).
    """
    if name not in config.LAYER_KEYS:
        raise KeyError(f"unknown layer {name!r}; known: {sorted(config.LAYER_KEYS)}")

    gdf = None
    if _rest_available():
        try:
            gdf = _load_from_rest(name, bbox or config.DATA_BOUNDS)
            log.info("loaded %s from REST (%d features)", name, len(gdf))
        except Exception as exc:  # fall through to cache/S3
            log.warning("REST load of %s failed (%s); falling back to cache/S3", name, exc)
            gdf = None

    if gdf is None:
        key = config.LAYER_KEYS[name]
        path = _cache_file(key)
        try:
            if not path.exists():
                _download_to_cache(key)
            gdf = _read_geojson(path)
        except Exception as exc:
            raise DataUnavailable(
                f"could not load layer {name!r} from REST, cache, or S3 ({exc}). "
                f"If the Cyvl API is down, download {key} from the hackathon "
                f"Google Drive / S3 bucket into {config.CACHE_DIR} and retry."
            ) from exc

    if bbox is not None and len(gdf):
        w, s, e, n = bbox
        gdf = gdf.cx[w:e, s:n].copy()
    return gdf


def load_functional_class() -> pd.DataFrame:
    """Return a small frame of inspect_cell_id -> fhwa_functional_class.

    Used to attach a Cyvl-native road-class (traffic proxy) to each candidate.
    Best effort: returns an empty frame if the cells file is unavailable.
    """
    path = _cache_file(config.CELLS_KEY)
    try:
        if not path.exists():
            _download_to_cache(config.CELLS_KEY)
        cells = pd.read_parquet(path, columns=["id", "fhwa_functional_class"])
        return cells.rename(columns={"id": "inspect_cell_id"})
    except Exception as exc:
        log.warning("functional class unavailable (%s); traffic will use default", exc)
        return pd.DataFrame(columns=["inspect_cell_id", "fhwa_functional_class"])


def load_layers(names=("pavements", "assets", "markings"), bbox=None) -> dict:
    """Load several layers at once. Returns {name: GeoDataFrame}."""
    return {name: load_layer(name, bbox=bbox) for name in names}
