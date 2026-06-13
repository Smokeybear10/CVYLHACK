"""Export candidate charger spots, chunked by street, for the frontend (Thomas).

Output: spots_by_street.json
  { "Summer Street": { "count": N, "spots": [ {seg_id, lon, lat, score, label, verdict}, ... ] }, ... }

Each street is one chunk; each spot is a curb location with coordinates. The frontend renders the
spots per street and, for any spot, can open its CAD scene (run.py with that lon/lat).

Two sources:
  - default: derive spots from data/pavements_v2.geojson (every scored curb segment = a spot)
  - --verdicts path.json : a list of swarm verdicts [{lon,lat,address_st,verdict,score}, ...]
    (the end goal: only the swarm-verified streets/spots)

    cd cad && python export_spots.py
    cd cad && python export_spots.py --verdicts verdicts.json
"""
import argparse
import json
from collections import defaultdict

import geopandas as gpd


def from_pavements(path="data/pavements_v2.geojson"):
    g = gpd.read_file(path)
    spots = []
    for _, r in g.iterrows():
        c = r.geometry.centroid if r.geometry is not None else None
        if c is None:
            continue
        spots.append({
            "seg_id": r.get("client_seg_id"),
            "address_st": r.get("address_st") or "Unknown",
            "lon": round(c.x, 6), "lat": round(c.y, 6),
            "score": r.get("score"), "label": r.get("label"),
            "verdict": None,                        # filled by the swarm later
        })
    return spots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdicts", help="JSON list of swarm verdicts with lon/lat/address_st")
    ap.add_argument("--out", default="spots_by_street.json")
    args = ap.parse_args()

    if args.verdicts:
        spots = json.load(open(args.verdicts))
    else:
        spots = from_pavements()

    # add a Google-Maps-ready "latlon" string (LAT first) so no one swaps the order
    for s in spots:
        if s.get("lat") is not None and s.get("lon") is not None:
            s["latlon"] = f"{s['lat']}, {s['lon']}"     # paste straight into Google Maps
            s["maps_url"] = f"https://www.google.com/maps?q={s['lat']},{s['lon']}"

    by_street = defaultdict(list)
    for s in spots:
        by_street[s.get("address_st") or "Unknown"].append(s)

    out = {st: {"count": len(v), "spots": v} for st, v in sorted(by_street.items())}
    json.dump(out, open(args.out, "w"), indent=2, default=str)
    print(f"wrote {args.out}: {len(out)} streets, {sum(c['count'] for c in out.values())} spots")
    # show the biggest few streets
    for st, c in sorted(out.items(), key=lambda kv: -kv[1]["count"])[:6]:
        print(f"  {c['count']:4d}  {st}")


if __name__ == "__main__":
    main()
