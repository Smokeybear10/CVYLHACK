"""Stage 1.5 orchestrator: measure a screened finalist from the 3D scan.

Public surface (what a frontend or the agent swarm imports):

    from perception import perceive, perceive_finalists

    site = perceive(candidate_feature)          # one screened candidate -> measurement
    sites = perceive_finalists(screen_result)   # whole screen() result -> measurements

`screen_result` is exactly what `screening.screen()` returns. `candidate_feature`
is a GeoJSON Feature from `screen_result["candidates"]` (it carries the geometry we
measure). Output is a plain JSON-serializable dict; see README for the schema.
"""
from __future__ import annotations

import json

from . import config, measure, scene, segment

VERIFY_ON_SITE = ["grid capacity", "zoning", "host willingness", "final permit"]


def _centroid(geometry, props) -> tuple[float, float] | None:
    if props.get("lon") is not None and props.get("lat") is not None:
        return float(props["lon"]), float(props["lat"])
    ends = measure.segment_endpoints(geometry or {})
    if ends:
        (alon, alat), (blon, blat) = ends
        return (alon + blon) / 2.0, (alat + blat) / 2.0
    return None


def _cache_path(cand_id):
    return config.CACHE_DIR / f"{cand_id}.json"


def _load_cache(cand_id):
    p = _cache_path(cand_id)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return None


def _save_cache(cand_id, result):
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(cand_id).write_text(json.dumps(result))


def perceive(candidate, station_size: str = config.DEFAULT_STATION,
             use_cache: bool = True, render: bool = True) -> dict:
    """Measure one screened candidate. `candidate` is a GeoJSON Feature (preferred,
    has geometry) or a dict with at least cand_id + lon/lat."""
    geometry = candidate.get("geometry")
    props = candidate.get("properties", candidate)
    cand_id = props.get("cand_id") or props.get("id")

    if use_cache and cand_id is not None:
        cached = _load_cache(cand_id)
        if cached is not None:
            return cached

    centroid = _centroid(geometry, props)
    endpoints = measure.segment_endpoints(geometry or {})
    notes: list[str] = []

    result = {
        "cand_id": cand_id,
        "station_size": station_size,
        "required_frontage_ft": config.required_frontage_ft(station_size),
        "screening_verdict": props.get("verdict"),
        "screening_score": props.get("score"),
    }

    if centroid is None:
        result.update({"measured": False, "method": "none",
                       "error": "no geometry or lon/lat on candidate"})
        if use_cache and cand_id is not None:
            _save_cache(cand_id, result)
        return result

    frame = scene.nearest_frame(centroid[0], centroid[1])

    # SAM3 obstruction discovery + power location (real CV; runs only with FAL_KEY)
    obstructions, sam_used, note = segment.locate_obstructions(frame)
    if note:
        notes.append(note)
    sam_power_m, _ = segment.locate_power(frame)

    # frontage measured off the scan when we have the segment geometry
    if endpoints:
        segment_ft, frontage_source = measure.measure_frontage_scan(frame, endpoints)
        tagged = measure.on_segment_obstructions(obstructions, endpoints)
    else:
        segment_ft = float(props.get("length_ft") or 0.0)
        frontage_source = "screening"
        tagged = [dict(o, on_segment=False, offset_m=None) for o in obstructions]
        notes.append("no segment geometry; frontage from screening length_ft")

    usable_ft = measure.usable_frontage_ft(segment_ft, tagged)

    # distance to power: prefer the SAM3 measurement, else screening's detected-pole value
    if sam_power_m is not None:
        dist_to_power_m, power_source = float(sam_power_m), "sam3"
    elif props.get("dist_to_power_m") is not None:
        dist_to_power_m, power_source = float(props["dist_to_power_m"]), "screening"
    else:
        dist_to_power_m, power_source = None, None

    fits = measure.fits_station(usable_ft, station_size)
    has_blocker = any(o.get("on_segment") for o in tagged)
    verdict = measure.refined_verdict(
        fits=fits, dist_to_power_m=dist_to_power_m, has_blocker=has_blocker, sam_used=sam_used)

    evidence_path = None
    if render and endpoints:
        evidence_path = measure.render_evidence(
            frame, endpoints, tagged, config.EVIDENCE_DIR / f"{cand_id}.png")

    result.update({
        "measured": True,
        "method": "sam3" if sam_used else ("lidar" if frontage_source == "scan" else "geometry"),
        "frame_id": getattr(frame, "id", None),
        "image_url": getattr(frame, "image_url", None),
        "segment_frontage_ft": round(segment_ft, 1),
        "frontage_source": frontage_source,
        "usable_frontage_ft": round(usable_ft, 1),
        "fits_station": fits,
        "dist_to_power_m": round(dist_to_power_m, 1) if dist_to_power_m is not None else None,
        "power_source": power_source,
        "obstructions": tagged,
        "obstruction_count": sum(1 for o in tagged if o.get("on_segment")),
        "sam_used": sam_used,
        "refined_verdict": verdict,
        "flags": [f"verify on site: {f}" for f in VERIFY_ON_SITE],
        "evidence_image_path": evidence_path,
        "notes": notes,
    })

    if use_cache and cand_id is not None:
        _save_cache(cand_id, result)
    return result


def perceive_finalists(screen_result: dict, limit: int | None = None,
                       station_size: str | None = None, use_cache: bool = True,
                       render: bool = True) -> list[dict]:
    """Measure the screening finalists. Uses screen_result['top'] to pick which and
    screen_result['candidates'] for the geometry. Returns a list of measurements."""
    station_size = station_size or (
        screen_result.get("summary", {}).get("filters", {}).get("station_size")
        or config.DEFAULT_STATION)

    by_id = {}
    for feat in screen_result.get("candidates", {}).get("features", []):
        cid = feat.get("properties", {}).get("cand_id")
        if cid is not None:
            by_id[cid] = feat

    top = screen_result.get("top", [])
    if limit is not None:
        top = top[:limit]

    out = []
    for item in top:
        cid = item.get("cand_id")
        feat = by_id.get(cid)
        if feat is None:  # only the centroid is known
            feat = {"geometry": None, "properties": item}
        out.append(perceive(feat, station_size=station_size,
                             use_cache=use_cache, render=render))
    return out
