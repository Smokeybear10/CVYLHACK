"""Unit tests for region handling and spatial enrichment. Synthetic, no network."""
import geopandas as gpd
import pytest
from shapely.geometry import LineString, Point, box

from screening import config
from screening.features import build_candidates, normalize_region


def test_normalize_region_forms():
    assert normalize_region([1, 2, 3, 4]) == ([1, 2, 3, 4], None)
    bbox, geom = normalize_region({"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]})
    assert geom is not None and len(bbox) == 4
    bbox, geom = normalize_region(box(0, 0, 1, 1))
    assert geom is not None
    assert normalize_region(None)[0] == config.DEMO_BBOX


def test_normalize_region_rejects_garbage():
    with pytest.raises(ValueError):
        normalize_region("not a region")
    with pytest.raises(ValueError):
        normalize_region([1, 2, 3])  # wrong length


def _scene():
    """A tiny hand-built scene near Somerville with known relationships."""
    # two ~30 ft segments along Medford-ish coordinates
    seg_a = LineString([(-71.1000, 42.3900), (-71.0999, 42.3900)])
    seg_b = LineString([(-71.1050, 42.3920), (-71.1049, 42.3920)])
    pav = gpd.GeoDataFrame(
        {
            "inspect_id": ["A1", "A2"],
            "inspect_cell_id": ["c1", "c2"],
            "client_seg_id": ["s1", "s2"],
            "address_st": ["Medford Street", "Summer Street"],
            "length_ft": [30.0, 30.0],
            "area_sqft": [900.0, 600.0],
            "label": ["Good", "Failed"],
            "score": [85.0, 5.0],
        },
        geometry=[seg_a, seg_b],
        crs=config.WGS84,
    )
    # a pole right next to seg_a, far from seg_b
    assets = gpd.GeoDataFrame(
        {"asset_type": ["UTILITY_POLE", "RAMP", "HYDRANT"]},
        geometry=[Point(-71.10005, 42.39001), Point(-71.10003, 42.39002), Point(-71.09997, 42.39001)],
        crs=config.WGS84,
    )
    # a fire-lane marking on seg_b
    markings = gpd.GeoDataFrame(
        {"type": ["FIRE LANE"]},
        geometry=[LineString([(-71.1050, 42.39201), (-71.1049, 42.39201)])],
        crs=config.WGS84,
    )
    return {"pavements": pav, "assets": assets, "markings": markings}


def test_build_candidates_features():
    cand = build_candidates(_scene(), region=[-71.11, 42.388, -71.094, 42.394])
    assert len(cand) == 2
    a = cand[cand.cand_id == "A1"].iloc[0]
    b = cand[cand.cand_id == "A2"].iloc[0]
    # seg_a is next to the pole, seg_b is far
    assert a.dist_to_power_m < b.dist_to_power_m
    assert a.dist_to_power_m < 10
    # seg_a has the hydrant in its frontage; seg_b does not
    assert a.obstruction_count >= 1
    # seg_b carries a fire-lane marking
    assert bool(b.disqualify_marking) is True
    assert bool(a.disqualify_marking) is False
    # derived width = area / length
    assert a.road_width_ft == pytest.approx(30.0)


def test_empty_region_is_clean():
    cand = build_candidates(_scene(), region=[10, 10, 11, 11])  # nowhere near the data
    assert len(cand) == 0
    assert cand.crs is not None  # still a well-formed GeoDataFrame
    assert "dist_to_power_m" in cand.columns


def test_polygon_region_filters():
    # a polygon covering only seg_a's location
    poly = box(-71.1005, 42.3895, -71.0995, 42.3905).__geo_interface__
    cand = build_candidates(_scene(), region=poly)
    ids = set(cand.cand_id)
    assert "A1" in ids and "A2" not in ids
