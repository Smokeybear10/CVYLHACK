import json
import math
import sys
import requests
from shapely.geometry import shape, box
from config import DEFAULT_BBOX, DEFAULT_CAP_GB


def tiles_in_bbox(manifest, bbox):
    region = box(*bbox)
    return [f["properties"] for f in manifest["features"]
            if shape(f["geometry"]).intersects(region)]


def corridor_bbox(a, b, margin_m=50.0):
    minlon, maxlon = sorted([a[0], b[0]])
    minlat, maxlat = sorted([a[1], b[1]])
    midlat = (minlat + maxlat) / 2
    dlat = margin_m / 111_320.0
    dlon = margin_m / (111_320.0 * math.cos(math.radians(midlat)))
    return (minlon - dlon, minlat - dlat, maxlon + dlon, maxlat + dlat)


def head_size(props):
    url = props["baseUrl"] + props["lasPath"]
    r = requests.head(url, allow_redirects=True, timeout=30)
    r.raise_for_status()
    return int(r.headers.get("Content-Length", 0))


def select_under_budget(tiles, cap_bytes):
    picked, total = [], 0
    for t in sorted(tiles, key=lambda x: x["size"]):
        if total + t["size"] <= cap_bytes:
            picked.append(t); total += t["size"]
    return picked


def plan(manifest_path, bbox=DEFAULT_BBOX, cap_gb=DEFAULT_CAP_GB):
    manifest = json.load(open(manifest_path))
    candidates = tiles_in_bbox(manifest, bbox)
    for t in candidates:
        t["size"] = head_size(t)
    picked = select_under_budget(candidates, int(cap_gb * 1024**3))
    total_gb = sum(t["size"] for t in picked) / 1024**3
    print(f"# {len(picked)} tiles, {total_gb:.2f} GB (cap {cap_gb} GB)")
    print("mkdir -p ./laz && cd ./laz")
    for t in picked:
        print(f'curl -O "{t["baseUrl"] + t["lasPath"]}"')
        print(f'#   Potree: {t["baseUrl"] + t["lasPath"]}.potree/metadata.json')
    json.dump(picked, open("selected_tiles.json", "w"), indent=2)


if __name__ == "__main__":
    plan(sys.argv[1] if len(sys.argv) > 1 else "pointclouds_v2.geojson")
