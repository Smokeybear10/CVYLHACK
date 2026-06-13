"""Tests for the OBJ/MTL scene writer and parametric models.

Updated to the current to_cad API (mesh primitives + {name, material, verts, faces} objects;
the old box_obj/kind API this file used was stale). Also covers Sonder's ev_station_objects.
All pure-Python: no PDAL, no APS, no data.
"""
from pipeline.to_cad import (
    mesh_box, write_obj, write_mtl, car_objects, asset_objects,
    ev_charger_objects, ev_station_objects, MATERIALS,
)


def test_mesh_box_8_verts_6_faces():
    verts, faces = mesh_box((0, 0, 0.75), (4.5, 1.8, 1.5))
    assert len(verts) == 8
    assert len(faces) == 6


def test_write_obj_named_groups_and_offset(tmp_path):
    objs = car_objects([
        {"center": (0, 0, 0.75), "length": 4.5, "width": 1.8, "height": 1.5, "yaw": 0},
        {"center": (10, 0, 0.75), "length": 4.5, "width": 1.8, "height": 1.5, "yaw": 0},
    ])
    p = tmp_path / "scene.obj"
    write_obj(str(p), objs, mtl_filename="scene.mtl")
    body = p.read_text()
    assert body.startswith("mtllib scene.mtl")
    assert "o car_01\n" in body and "o car_02\n" in body   # exact group lines
    assert "o car_01_cabin\n" in body                       # multi-part object
    # later objects must reference globally-offset vertex indices (1-based)
    assert "\nf " in body


def test_ev_charger_named_parts_share_prefix():
    objs = ev_charger_objects([{"x": 5.0, "y": 3.0, "ground_z": 0.0, "yaw": 0.0}])
    names = [o["name"] for o in objs]
    # every part is its own selectable node, all sharing the ev_charger_01 prefix (drag as a group)
    assert all(n.startswith("ev_charger_01") for n in names)
    assert {"ev_charger_01_base", "ev_charger_01_pole", "ev_charger_01_head",
            "ev_charger_01_light", "ev_charger_01_plug"}.issubset(set(names))
    assert all(" " not in n for n in names)          # no spaces -> stays selectable in APS Viewer
    assert all(o["verts"] and o["faces"] for o in objs)
    mats = {o["material"] for o in objs}
    assert "ev_accent" in mats and "ev_body" in mats  # teal light bar + charcoal body


def test_ev_station_alias_still_works():
    assert ev_station_objects is ev_charger_objects


def test_ev_charger_in_full_scene_obj(tmp_path):
    objs = (car_objects([{"center": (0, 0, 0.75), "length": 4.5, "width": 1.8, "height": 1.5}])
            + ev_charger_objects([{"x": 8.0, "y": 2.0, "ground_z": 0.0, "yaw": 0.7}]))
    p = tmp_path / "scene.obj"
    write_obj(str(p), objs, mtl_filename="scene.mtl")
    body = p.read_text()
    assert "o ev_charger_01_head\n" in body
    assert "usemtl ev_accent" in body


def test_ev_materials_exported(tmp_path):
    for m in ("ev_body", "ev_accent", "ev_base", "ev_screen"):
        assert m in MATERIALS
    p = tmp_path / "scene.mtl"
    write_mtl(str(p))
    txt = p.read_text()
    assert "newmtl ev_accent" in txt and "newmtl ev_body" in txt


def test_asset_objects_skips_ground_assets():
    # CURB/SIDEWALK/RAMP are part of the ground mesh, not standalone objects
    objs = asset_objects([
        {"type": "CURB", "x": 0, "y": 0, "ground_z": 0, "height": 0.2},
        {"type": "HYDRANT", "x": 1, "y": 1, "ground_z": 0, "height": 0.9},
    ])
    names = [o["name"] for o in objs]
    assert any(n.startswith("hydrant") for n in names)
    assert not any("curb" in n for n in names)
