#!/usr/bin/env python3
"""
Fetch Cyvl hackathon data from the public S3 bucket and print label stats.

No AWS credentials needed. The bucket is public over plain HTTPS for the
duration of the event.

Usage:
    pip install pandas pyarrow geopandas
    python scripts/fetch_data.py            # download core layers + docs, print stats
    python scripts/fetch_data.py --all      # also grab the bigger layers

Verified working on hackathon day. See docs/DATA.md for the full data map.
"""
import argparse
import sys
from pathlib import Path
from urllib.request import urlretrieve

BUCKET = "https://cyvl-hackathon.s3.amazonaws.com"
OUT = Path("data_cache")

DOCS = ["README.md", "index.md", "schemas.md"]

# (key, download by default?)
LAYERS = {
    "rollup": True,
    "pavements": True,
    "signs": True,
    "aboveGroundAssets": True,
    "sam": True,
    "distresses": False,            # 11 MB parquet, 84k rows
    "distressInspectionCells": False,
    "plainImagery": True,
    "panoramicImagery": False,
}


def fetch(key: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BUCKET}/{key}"
    print(f"  GET {url}")
    urlretrieve(url, dest)
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="also fetch the big layers")
    args = ap.parse_args()

    OUT.mkdir(exist_ok=True)
    print("== docs ==")
    for d in DOCS:
        fetch(d, OUT / d)

    print("== parquet layers ==")
    for name, default in LAYERS.items():
        if default or args.all:
            fetch(f"parquet/layers/{name}.parquet", OUT / f"{name}.parquet")

    # stats
    try:
        import geopandas as gpd
    except ImportError:
        print("\n(install geopandas to see label stats: pip install geopandas)")
        return

    print("\n== label stats ==")
    pav = gpd.read_parquet(OUT / "pavements.parquet")
    print(f"pavements: {len(pav)} segments")
    print(pav["label"].value_counts().to_string())

    signs_p = OUT / "signs.parquet"
    if signs_p.exists():
        s = gpd.read_parquet(signs_p)
        print(f"\nsigns: {len(s)} (image_url present: {s['image_url'].notna().sum()})")
        print("top MUTCD:", dict(s["mutcd"].value_counts().head(8)))
        print("category:", dict(s["category"].value_counts()))

    dis_p = OUT / "distresses.parquet"
    if dis_p.exists():
        d = gpd.read_parquet(dis_p)
        print(f"\ndistresses: {len(d)} (image present: {d['image'].notna().sum()})")
        print("types:", dict(d["distress_type"].value_counts()))
        print("severity:", dict(d["severity"].value_counts()))

    print(f"\nDone. Files in ./{OUT}/")


if __name__ == "__main__":
    sys.exit(main())
