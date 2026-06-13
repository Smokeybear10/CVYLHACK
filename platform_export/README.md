# platform_export

Somerville layers exported from the Cyvl platform (the "City of Somerville, MA Marketing Demo" project) and shared over Google Drive. Same underlying data as the public S3 bucket (see [../docs/DATA.md](../docs/DATA.md)), in shapefile / GeoJSON form, plus a routable street centerline the bucket doesn't have.

All layers are WGS84 (EPSG:4326). Read with geopandas: `gpd.read_file("path/to/layer.shp")`.

| Folder / file | Features | Geom | Notes |
|---|---|---|---|
| `centerline/somerville_ma_streets_final_2.shp` | 2,167 | LineString | **Routable street graph** (OSM-style: `u`,`v` nodes, `oneway`, `length`, `ref`, `bridge`, `junction`). New vs the S3 bucket. Good for routing/network ideas. |
| `pavement_scores_30ft/layer_zip.shp` | 5,080 | LineString | 30 ft pavement segments: `score` (0-100), `label`, `address_st`, `length_ft`, `area_sqft`, `client_seg`. Render color in `stroke`. Same as S3 `pavements_v2`. |
| `pavement_scores_segment/layer_zip.shp` | 894 | LineString | Segment-to-segment rollup: one `score`/`label` per street segment. Same as S3 `rollup_v2`. |
| `signs/tmpvw1yibth.shp` | 3,782 | Point | Signs with `mutcd`, `category`, `condition`, `image_url`. South/SE coverage. |
| `plainImagery/layer_zip.shp` | 22,830 | Point | Forward-facing photo points: `image_url` (CDN), `lat/lon`, `bearing`, `prev_id`/`next_id`. |
| `panoramicImagery/layer_zip.shp` | 38,469 | Point | 360 panorama points + viewer links. |
| `aboveGroundAssets.geojson` | 8,254 | Point | Manholes, hydrants, ramps, poles, etc. `asset_type`, `image_url`. |
| `sam.geojson` | 7,116 | LineString | Pavement markings / striping: `type`, `color`, `condition`, `image_url`. |

## Join keys

`client_seg` links pavement_30ft ↔ pavement_segment ↔ (S3) distresses. `id`/`prev_id`/`next_id` walk the imagery capture sequence.

## vs the S3 bucket

The S3 bucket (`scripts/fetch_data.py`) additionally has `distresses_v2` (84,612 labeled defects with per-row images) and the SDK pose/calibration parquet for 3D↔2D projection. Use the bucket for CV training data; these exports are convenient for QGIS and quick local GIS work. The `centerline` here is the one layer not in the bucket.
