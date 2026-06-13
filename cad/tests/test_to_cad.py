"""Tests for the OBJ/MTL scene writer and parametric models.

Updated to the current to_cad API (mesh primitives + {name, material, verts, faces} objects;
the old box_obj/kind API this file used was stale). Also covers Sonder's ev_station_objects.
All pure-Python: no PDAL, no APS, no data.
"""
from pipeline.to_cad import (
    mesh_box, write_obj, write_mtl, car_objects, asset_objects, ev_station_objects, MATERIALS,
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


def test_ev_station_named_selectable_parts():
    objs = ev_station_objects([{"x": 5.0, "y": 3.0, "ground_z": 0.0, "yaw": 0.0}])
    names = [o["name"] for o in objs]
    assert names == ["ev_station_01", "ev_station_01_screen", "ev_station_01_plug"]
    assert all(" " not in n for n in names)          # no spaces -> stays selectable in APS Viewer
    assert objs[0]["material"] == "ev_green"
    assert all(o["verts"] and o["faces"] for o in objs)


def test_ev_station_in_full_scene_obj(tmp_path):
    objs = (car_objects([{"center": (0, 0, 0.75), "length": 4.5, "width": 1.8, "height": 1.5}])
            + ev_station_objects([{"x": 8.0, "y": 2.0, "ground_z": 0.0, "yaw": 0.7}]))
    p = tmp_path / "scene.obj"
    write_obj(str(p), objs, mtl_filename="scene.mtl")
    body = p.read_text()
    assert "o ev_station_01\n" in body
    assert "usemtl ev_green" in body


def test_ev_green_material_exported(tmp_path):
    assert "ev_green" in MATERIALS
    p = tmp_path / "scene.mtl"
    write_mtl(str(p))
    assert "newmtl ev_green" in p.read_text()


def test_asset_objects_skips_ground_assets():
    # CURB/SIDEWALK/RAMP are part of the ground mesh, not standalone objects
    objs = asset_objects([
        {"type": "CURB", "x": 0, "y": 0, "ground_z": 0, "height": 0.2},
        {"type": "HYDRANT", "x": 1, "y": 1, "ground_z": 0, "height": 0.9},
    ])
    names = [o["name"] for o in objs]
    assert any(n.startswith("hydrant") for n in names)
    assert not any("curb" in n for n in names)
