from pipeline.select_tiles import tiles_in_bbox, corridor_bbox, select_under_budget


def test_tiles_in_bbox_keeps_only_intersecting(synthetic_manifest):
    bbox = (-71.1235, 42.3955, -71.1200, 42.3980)
    names = [t["filename"] for t in tiles_in_bbox(synthetic_manifest, bbox)]
    assert "a.laz" in names and "b.laz" in names
    assert "far.laz" not in names


def test_corridor_bbox_spans_two_points_with_margin():
    minlon, minlat, maxlon, maxlat = corridor_bbox((-71.123, 42.395), (-71.120, 42.398), 50)
    assert minlon < -71.123 and maxlon > -71.120
    assert minlat < 42.395 and maxlat > 42.398


def test_select_under_budget_stops_before_cap():
    tiles = [{"filename": f"{i}.laz", "size": 3_000_000_000} for i in range(10)]
    picked = select_under_budget(tiles, cap_bytes=10_000_000_000)
    assert len(picked) == 3
    assert sum(t["size"] for t in picked) <= 10_000_000_000
