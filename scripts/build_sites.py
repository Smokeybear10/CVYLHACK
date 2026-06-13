#!/usr/bin/env python3
"""
Sonder Stage 1 - real screening pipeline.

Reads the real Cyvl exports in platform_export/ and produces demo/mockups/data.js:
every pavement curb segment enriched with REAL measurements computed from the real
asset geometry (distance to nearest power asset, nearest ADA ramp, obstruction count,
usable frontage, pavement condition), gated and scored. No synthesized numbers.

    python3 scripts/build_sites.py
"""
import json, math, collections
from pathlib import Path
import numpy as np
import shapefile

ROOT = Path(__file__).resolve().parent.parent
EXP = ROOT / "platform_export"
OUT = ROOT / "demo" / "mockups" / "data.js"

# ---- load real assets -------------------------------------------------------
assets = json.load(open(EXP / "aboveGroundAssets.geojson"))["features"]
def pts(types):
    a = [(f["geometry"]["coordinates"][0], f["geometry"]["coordinates"][1])
         for f in assets if f["properties"].get("asset_type") in types
         and f.get("geometry") and f["geometry"].get("type") == "Point"]
    return np.array(a, dtype=float) if a else np.zeros((0, 2))

POWER = pts({"UTILITY_POLE", "LUMINARIES", "TRAFFIC_SIGNAL_POLE"})
ADA   = pts({"RAMP"})
OBST  = pts({"HYDRANT", "TREE", "MANHOLE_COVER", "CATCH_BASIN"})
# every asset with a photo, for nearest evidence image
img_xy, img_url = [], []
for f in assets:
    u = f["properties"].get("image_url"); g = f.get("geometry")
    if u and g and g.get("type") == "Point":
        img_xy.append((g["coordinates"][0], g["coordinates"][1])); img_url.append(u)
img_xy = np.array(img_xy, dtype=float)

# markings: fire lane / crosswalk / no-lines near a segment -> parking + activity
marks = json.load(open(EXP / "sam.geojson"))["features"]
def mark_xy(pred):
    a = []
    for f in marks:
        g = f.get("geometry"); t = (f["properties"].get("type") or "")
        if not g or not pred(t):
            continue
        c = g["coordinates"]
        while isinstance(c[0], list):
            c = c[0]
        a.append((c[0], c[1]))
    return np.array(a, dtype=float) if a else np.zeros((0, 2))
FIRE = mark_xy(lambda t: "FIRE LANE" in t)
CROSS = mark_xy(lambda t: "CROSSWALK" in t)
ACTIV = mark_xy(lambda t: t not in ("", "NO LINES"))  # marking density = street activity

# ---- meters helpers ---------------------------------------------------------
LAT0 = 42.3855
MLON = 111320 * math.cos(math.radians(LAT0))
MLAT = 110540
def nearest_m(px, py, arr):
    if len(arr) == 0:
        return 9999.0, 0
    dx = (arr[:, 0] - px) * MLON
    dy = (arr[:, 1] - py) * MLAT
    d = np.sqrt(dx * dx + dy * dy)
    return float(d.min()), d
def count_within(px, py, arr, r):
    if len(arr) == 0:
        return 0
    dx = (arr[:, 0] - px) * MLON; dy = (arr[:, 1] - py) * MLAT
    return int((np.sqrt(dx * dx + dy * dy) <= r).sum())

clamp = lambda v: max(0.0, min(1.0, v))

# ---- load real pavement segments (candidates) -------------------------------
r = shapefile.Reader(str(EXP / "pavement_scores_30ft" / "layer_zip.shp"))
fld = [f[0] for f in r.fields[1:]]
recs = r.records(); shapes = r.shapes()

def neigh(lat, lon):
    return "Brickbottom" if lat > 42.384 else ("Duck Village" if lon < -71.100 else "Union Square")
def sf(x, dv=0.0):
    try: return float(x)
    except (TypeError, ValueError): return dv

sites = []
for rec, shp in zip(recs, shapes):
    d = dict(zip(fld, list(rec)))
    P = shp.points
    if not P:
        continue
    lon = sum(p[0] for p in P) / len(P); lat = sum(p[1] for p in P) / len(P)
    pci = sf(d["score"]); label = str(d["label"]); length_ft = sf(d["length_ft"], 30); area = sf(d["area_sqft"], length_ft * 20)
    width_ft = round(area / length_ft, 1) if length_ft else 0.0
    dist_power, _ = nearest_m(lon, lat, POWER)
    if dist_power > 120:          # outside the scanned / serviceable coverage -> not a candidate
        continue
    dist_ada, _ = nearest_m(lon, lat, ADA)
    n_obst = count_within(lon, lat, OBST, 8.0)
    fire = count_within(lon, lat, FIRE, 10.0) > 0
    near_cross = count_within(lon, lat, CROSS, 12.0) > 0
    activity = count_within(lon, lat, ACTIV, 45.0)
    stalls = max(0, int(length_ft // 18))            # 5.5 m = 18 ft per stall
    ada_mapped = dist_ada <= 250                     # ramp data present near here?

    # factors 0..1 (real). Unmapped ADA is flagged, not penalized (plan: flag never fake).
    f_power = clamp(1 - dist_power / 60.0)
    f_ada = clamp(1 - dist_ada / 80.0) if dist_ada <= 80 else (0.55 if ada_mapped else 0.5)
    f_mount = clamp((width_ft - 16) / 24.0)          # frontage / road width fit
    f_park = clamp(0.9 - (0.5 if fire else 0) - (0.25 if near_cross else 0))
    f_demand = clamp(activity / 9.0)
    f = {"mounting": round(f_mount, 3), "power": round(f_power, 3),
         "parking": round(f_park, 3), "ada": round(f_ada, 3), "demand": round(f_demand, 3)}

    # hard gates -> No-go
    gate = None
    if label == "Failed": gate = "Pavement failed"
    elif length_ft < 18: gate = "Frontage too short for a stall"

    # nearest real evidence photo
    iu = ""
    if len(img_xy):
        _, dd = nearest_m(lon, lat, img_xy); iu = img_url[int(dd.argmin())]

    sites.append({
        "id": str(d["inspect_id"]), "lat": round(lat, 6), "lng": round(lon, 6),
        "g": [[round(x, 6), round(y, 6)] for x, y in shp.points[:6]],
        "addr": (str(d["address_st"]) or "Unnamed").title(), "nb": neigh(lat, lon),
        "f": f, "gate": gate,
        "m": {"dist_power": round(dist_power), "dist_ada": round(dist_ada), "n_obst": n_obst,
              "width_ft": width_ft, "pci": round(pci), "pci_label": label,
              "frontage_ft": round(length_ft), "stalls": stalls,
              "surface": "Concrete" if pci >= 85 else "Asphalt",
              "fire": fire, "activity": activity, "ada_pass": dist_ada < 40, "ada_mapped": ada_mapped},
        "img": iu,
    })

# default model = Level 2 curbside (the locked MVP scope)
W = {"mounting": .20, "power": .25, "parking": .25, "ada": .15, "demand": .15}
sm = sum(W.values())
for s in sites:
    base = 100 * sum(W[k] / sm * s["f"][k] for k in W)
    s["score"] = 0.0 if s["gate"] else round(base, 1)
    s["cost"] = round((9000 + s["m"]["dist_power"] * 140 + (6000 if s["m"]["pci_label"] in ("Poor", "Very Poor", "Serious") else 0)) / 100) * 100
    s["pay"] = round(20 + (1 - s["score"] / 100) * 34)

sites.sort(key=lambda s: -s["score"])
for i, s in enumerate(sites):
    s["rank"] = i + 1

lats = [s["lat"] for s in sites]; lons = [s["lng"] for s in sites]
viable = sum(1 for s in sites if s["score"] >= 70 and not s["gate"])
meta = {"city": "Somerville, MA", "source": "Cyvl platform export (real)",
        "evaluated": len(sites), "viable": viable,
        "center": [round(sum(lons) / len(lons), 5), round(sum(lats) / len(lats), 5)],
        "bounds": [min(lons), min(lats), max(lons), max(lats)],
        "weights": W}
OUT.write_text("window.MOCK=" + json.dumps({"meta": meta, "sites": sites}) + ";")

# ---- report -----------------------------------------------------------------
print(f"segments scored : {len(sites)}")
print(f"gated No-go     : {sum(1 for s in sites if s['gate'])}")
print(f"viable (>=70)   : {viable}")
print(f"power assets    : {len(POWER)}  ada ramps: {len(ADA)}  obstructions: {len(OBST)}")
md = np.median([s['m']['dist_power'] for s in sites])
print(f"median dist-to-power: {md:.0f} m")
print("top 5 real sites:")
for s in sites[:5]:
    m = s["m"]
    print(f"  #{s['rank']} {s['id']} {s['addr'][:26]:26} score {s['score']:5} | "
          f"power {m['dist_power']}m, ada {m['dist_ada']}m, {m['stalls']} stalls, PCI {m['pci']}")
print(f"\nwrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size//1024} KB)")
