#!/usr/bin/env python
"""SAM3 obstruction survey for a curbside EV site — Sonder Stage 1.5/2.

Takes a site (--site <id> or --lonlat <lon> <lat>), finds the nearest posed
Cyvl frame, runs SAM3 (fal.ai) for each EV-relevant obstruction, lifts every
mask to 3D through the frame's LiDAR, and writes an evidence overlay + JSON.
Real measurement from the scan, no mock data.

    python perception/sam_survey.py --site IA17248
    python perception/sam_survey.py --lonlat -71.0996 42.3855 --prompts "fire hydrant,driveway"

Needs FAL_KEY (read from the repo .env or the environment).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
# prompts whose SAM hits are kept as measured points but shown without a type name
GENERIC = {"manhole"}
DEFAULT_PROMPTS = ["fire hydrant", "driveway", "utility pole", "tree", "parked car", "traffic sign"]
COLORS = [(255, 90, 57), (139, 245, 61), (46, 176, 255), (82, 90, 255), (255, 120, 180), (255, 200, 120)]  # BGR


def _load_env() -> None:
    """Populate FAL_KEY (and friends) from the repo .env if not already set."""
    import os

    if os.environ.get("FAL_KEY"):
        return
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _site_lonlat(site_id: str) -> tuple[float, float]:
    """Look up a site's lon/lat from the frontend's data.js."""
    data = REPO / "demo" / "mockups" / "data.js"
    txt = data.read_text()
    m = re.search(r'"id":\s*"' + re.escape(site_id) + r'"(.{0,300})', txt, re.S)
    if not m:
        raise SystemExit(f"Site {site_id!r} not found in {data}")
    chunk = m.group(1)
    lat = re.search(r'"lat":\s*(-?[\d.]+)', chunk)
    lng = re.search(r'"lng":\s*(-?[\d.]+)', chunk)
    if not (lat and lng):
        raise SystemExit(f"Could not parse lat/lng for {site_id!r}")
    return float(lng.group(1)), float(lat.group(1))


def survey(lon, lat, prompts=DEFAULT_PROMPTS, *, scene="somerville", out=None,
           label="", frame_id=None, radius_m=30.0, max_masks=3):
    """Segment + 3D-locate obstructions for one curbside site."""
    _load_env()
    import cyvl
    from cyvl.geometry import lonlat_to_utm, utm_to_lonlat
    from cyvl.segment import locate

    out = Path(out) if out else REPO / "exports" / "sam"
    sc = cyvl.load_scene(scene)
    frame = sc.frame(frame_id) if frame_id else sc.nearest_frame(lon, lat)

    q = lonlat_to_utm(lon, lat, 0.0, frame.utm_epsg)[0]
    frame_dist = float(np.hypot(q[0] - frame.position[0], q[1] - frame.position[1]))
    flon, flat, _ = utm_to_lonlat(frame.position[None, :], frame.utm_epsg)[0]

    canvas = cv2.cvtColor(frame.image(), cv2.COLOR_RGB2BGR)
    findings = []
    for ci, prompt in enumerate(prompts):
        try:
            hits = locate(frame, prompt, radius_m=radius_m, max_masks=max_masks)
        except Exception as exc:  # one bad prompt shouldn't kill the survey
            print(f"  ! {prompt}: {exc}")
            continue
        color = COLORS[ci % len(COLORS)]
        for h in hits:
            reg = h.mask.astype(bool)
            canvas[reg] = (canvas[reg] * 0.45 + np.array(color) * 0.55).astype(np.uint8)
            ys, xs = np.where(reg)
            if len(xs):
                cv2.putText(canvas, (f"{h.distance_m:.1f}m" if prompt in GENERIC else f"{prompt} {h.distance_m:.1f}m"), (int(xs.min()), max(16, int(ys.min()) - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
            findings.append({
                "prompt": ("" if prompt in GENERIC else prompt),
                "lonlat": [round(h.lonlat[0], 6), round(h.lonlat[1], 6)],
                "distance_m": round(h.distance_m, 1),
                "score": round(h.score, 2),
                "lidar_points": h.n_points,
            })
        print(f"  {prompt}: {len(hits)} located")

    out.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", label or frame.id)
    img_path = out / f"{stem}.jpg"
    cv2.imwrite(str(img_path), canvas)
    result = {
        "site": label,
        "query": [round(lon, 6), round(lat, 6)],
        "frame": frame.id,
        "frame_lonlat": [round(float(flon), 6), round(float(flat), 6)],
        "frame_distance_m": round(frame_dist, 1),
        "n_obstructions": len(findings),
        "obstructions": sorted(findings, key=lambda f: f["distance_m"]),
        "overlay": str(img_path),
    }
    (out / f"{stem}.json").write_text(json.dumps(result, indent=2))
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--site", help="site id from data.js (e.g. IA17248)")
    g.add_argument("--lonlat", nargs=2, type=float, metavar=("LON", "LAT"))
    ap.add_argument("--frame-id", help="force a specific frame instead of nearest")
    ap.add_argument("--prompts", help="comma-separated; defaults to the EV obstruction set")
    ap.add_argument("--scene", default="somerville")
    ap.add_argument("--out")
    ap.add_argument("--radius", type=float, default=30.0, help="LiDAR fetch radius, meters")
    ap.add_argument("--max-masks", type=int, default=3, help="max objects per prompt (1-32)")
    a = ap.parse_args()

    if a.site:
        lon, lat = _site_lonlat(a.site)
        label = a.site
    else:
        lon, lat = a.lonlat
        label = f"{lat:.5f}_{lon:.5f}"
    prompts = [s.strip() for s in a.prompts.split(",")] if a.prompts else DEFAULT_PROMPTS

    print(f"Surveying {label}  ({lat:.5f}, {lon:.5f})")
    r = survey(lon, lat, prompts, scene=a.scene, out=a.out, label=label, frame_id=a.frame_id, radius_m=a.radius, max_masks=a.max_masks)
    print(f"\nframe {r['frame']}  ({r['frame_distance_m']} m from site)")
    print(f"{r['n_obstructions']} obstruction(s) located in 3D:")
    for f in r["obstructions"]:
        lon_, lat_ = f["lonlat"]
        print(f"  - {f['prompt']:<14}{f['distance_m']:>6} m   score {f['score']}   "
              f"{f['lidar_points']:,} pts   @ {lat_:.6f},{lon_:.6f}")
    print(f"\noverlay -> {r['overlay']}")
    print(f"json    -> {r['overlay'].replace('.jpg', '.json')}")


if __name__ == "__main__":
    main()
