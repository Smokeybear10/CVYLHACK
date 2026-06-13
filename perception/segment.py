"""SAM3 obstruction discovery via the cyvl spatial SDK (text-to-3D `locate`).

This is the real-CV step: it finds blockers the Cyvl point-asset layer does not
fully carry (driveways, bus stops, loading zones, construction) and locates the
power asset, each lifted to 3D coordinates with a distance. Runs only when FAL_KEY
is set; otherwise the pipeline measures with LiDAR alone and flags it.
"""
from __future__ import annotations

from . import config


def _hit_lonlat(hit):
    ll = getattr(hit, "lonlat", None)
    if ll is None:
        return None
    try:
        return float(ll[0]), float(ll[1])
    except Exception:
        return None


def locate_obstructions(frame) -> tuple[list[dict], bool, str]:
    """Return (obstructions, sam_used, note).

    Each obstruction: {label, lon, lat, distance_m, source}.
    """
    if not config.sam_available():
        reason = "FAL_KEY not set" if not config.FAL_KEY else "cyvl[sam] not installed"
        return [], False, f"SAM3 skipped ({reason}); measured with LiDAR only"

    from cyvl.segment import locate

    out: list[dict] = []
    for prompt in config.OBSTRUCTION_PROMPTS:
        try:
            hits = locate(frame, prompt, api_key=config.FAL_KEY)
        except Exception as e:  # one bad prompt should not kill the rest
            out.append({"label": prompt, "lon": None, "lat": None,
                        "distance_m": None, "source": "sam3", "error": str(e)[:120]})
            continue
        for h in hits or []:
            ll = _hit_lonlat(h)
            if ll is None:
                continue
            out.append({
                "label": prompt,
                "lon": ll[0],
                "lat": ll[1],
                "distance_m": float(getattr(h, "distance_m", float("nan"))),
                "source": "sam3",
            })
    return out, True, ""


def locate_power(frame):
    """Nearest power asset via SAM3. Returns (distance_m, (lon,lat)) or (None, None)."""
    if not config.sam_available():
        return None, None
    from cyvl.segment import locate
    try:
        hits = locate(frame, config.POWER_PROMPT, api_key=config.FAL_KEY)
    except Exception:
        return None, None
    best = None
    for h in hits or []:
        d = getattr(h, "distance_m", None)
        ll = _hit_lonlat(h)
        if d is None or ll is None:
            continue
        if best is None or d < best[0]:
            best = (float(d), ll)
    return best if best else (None, None)
