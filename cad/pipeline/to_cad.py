"""Build a CAD-looking OBJ/MTL scene from detected geometry.

Objects are generic meshes: {name, material, verts: [(x,y,z)], faces: [(i,...)]}
(face indices are 0-based within the object's own verts). write_obj() handles
the global vertex offsets and per-object `usemtl` lines.
"""
import math

MATERIALS = {
    "asphalt":  (0.13, 0.13, 0.15),
    "concrete": (0.80, 0.78, 0.72),
    "grass":    (0.36, 0.50, 0.28),
    "car":      (0.30, 0.38, 0.50),
    "glass":    (0.15, 0.18, 0.22),
    "trunk":    (0.36, 0.26, 0.18),
    "canopy":   (0.20, 0.45, 0.20),
    "pole":     (0.45, 0.45, 0.48),
    "hydrant":  (0.75, 0.15, 0.12),
    "metal":    (0.35, 0.35, 0.38),
    "signal":   (0.12, 0.12, 0.12),
    "misc":     (0.62, 0.58, 0.30),
    "wall":     (0.72, 0.66, 0.58),
    "roof":     (0.45, 0.40, 0.38),
    # Sonder EV charger (ChargePoint CT4000-class curbside pedestal)
    "ev_body":   (0.16, 0.18, 0.21),  # dark charcoal housing
    "ev_accent": (0.05, 0.62, 0.55),  # teal status light bar
    "ev_base":   (0.27, 0.27, 0.30),  # mounting plinth
    "ev_screen": (0.08, 0.10, 0.13),  # display
    "ev_beacon": (0.87, 1.00, 0.00),  # bright locator beacon (so you can spot the charger)
    "ev_marker": (1.00, 0.05, 0.55),  # hot-magenta locator pillar (charger 1)
    # futuristic curbside fast charger (modern monolith, no brand)
    "ev_white":  (0.93, 0.94, 0.96),  # sleek white shell
    "ev_cyan":   (0.00, 0.80, 0.92),  # cyan light strip
    "ev_marker2":(0.10, 0.85, 1.00),  # cyan locator pillar (charger 2)
}


def write_mtl(path):
    lines = []
    for name, (r, g, b) in MATERIALS.items():
        lines += [f"newmtl {name}", f"Kd {r:.3f} {g:.3f} {b:.3f}",
                  "Ka 0 0 0", "Ks 0.05 0.05 0.05", "Ns 10", ""]
    open(path, "w").write("\n".join(lines))


# ---------- primitives (verts 0-indexed, faces reference local verts) ----------

def mesh_box(center, size, yaw=0.0):
    cx, cy, cz = center
    sx, sy, sz = size
    c, s = math.cos(yaw), math.sin(yaw)
    verts = []
    for ox, oy, oz in [(-.5, -.5, -.5), (.5, -.5, -.5), (.5, .5, -.5), (-.5, .5, -.5),
                       (-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5)]:
        x, y, z = ox * sx, oy * sy, oz * sz
        verts.append((cx + x * c - y * s, cy + x * s + y * c, cz + z))
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return verts, faces


def mesh_cylinder(cx, cy, z0, radius, height, n=12):
    verts, faces = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = cx + radius * math.cos(a), cy + radius * math.sin(a)
        verts.append((x, y, z0))
        verts.append((x, y, z0 + height))
    for i in range(n):
        j = (i + 1) % n
        faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    faces.append(tuple(2 * i for i in range(n)))          # bottom cap
    faces.append(tuple(2 * i + 1 for i in range(n)))      # top cap
    return verts, faces


def mesh_cone(cx, cy, z0, radius, height, n=12):
    verts = [(cx + radius * math.cos(2 * math.pi * i / n),
              cy + radius * math.sin(2 * math.pi * i / n), z0) for i in range(n)]
    verts.append((cx, cy, z0 + height))                   # apex
    faces = [(i, (i + 1) % n, n) for i in range(n)]
    faces.append(tuple(range(n)))                         # base cap
    return verts, faces


# ---------- scene generators ----------

def car_objects(cars):
    """cars: list of {center, length, width, height, yaw}. Body box + cabin box."""
    objs = []
    for i, b in enumerate(cars, 1):
        cx, cy, cz = b["center"]
        L, W, H = b["length"], b["width"], b["height"]
        yaw = b.get("yaw", 0.0)
        z0 = cz - H / 2
        bv, bf = mesh_box((cx, cy, z0 + 0.35 * H), (L, W, 0.7 * H), yaw)
        objs.append({"name": f"car_{i:02d}", "material": "car", "verts": bv, "faces": bf})
        # cabin sits on the body, slightly rearward along the car axis
        off = -0.08 * L
        ox, oy = off * math.cos(yaw), off * math.sin(yaw)
        cv, cf = mesh_box((cx + ox, cy + oy, z0 + 0.78 * H), (0.55 * L, 0.85 * W, 0.44 * H), yaw)
        objs.append({"name": f"car_{i:02d}_cabin", "material": "glass", "verts": cv, "faces": cf})
    return objs


def asset_objects(assets):
    """assets: list of {type, x, y, ground_z, height}. Typed parametric models."""
    SKIP = {"CURB", "SIDEWALK", "RAMP", "GUARDRAILS"}   # covered by the ground mesh
    objs = []
    for i, a in enumerate(assets, 1):
        t = (a["type"] or "OTHER").upper()
        if t in SKIP:
            continue
        x, y, z0 = a["x"], a["y"], a["ground_z"]
        H = max(a["height"], 0.3)
        nm = f"{t.lower()}_{i:02d}"
        if t == "TREE":
            tv, tf = mesh_cylinder(x, y, z0, 0.15, 0.40 * H)
            objs.append({"name": nm, "material": "trunk", "verts": tv, "faces": tf})
            cv, cf = mesh_cone(x, y, z0 + 0.35 * H, min(1.8, 0.3 * H + 0.8), 0.65 * H)
            objs.append({"name": nm + "_canopy", "material": "canopy", "verts": cv, "faces": cf})
        elif t in ("UTILITY_POLE", "TRAFFIC_SIGNAL_POLE", "LUMINARIES"):
            pv, pf = mesh_cylinder(x, y, z0, 0.22, H)
            objs.append({"name": nm, "material": "pole", "verts": pv, "faces": pf})
        elif t == "HYDRANT":
            hv, hf = mesh_cylinder(x, y, z0, 0.25, min(H, 1.1), n=10)
            objs.append({"name": nm, "material": "hydrant", "verts": hv, "faces": hf})
        elif t in ("MANHOLE_COVER", "CATCH_BASIN"):
            dv, df = mesh_cylinder(x, y, z0, 0.45, 0.06, n=12)
            objs.append({"name": nm, "material": "metal", "verts": dv, "faces": df})
        elif t in ("TRAFFIC_SIGNAL", "STAND_ALONE_PEDESTRIAN_HEAD", "FLASHING_BEACONS"):
            pv, pf = mesh_cylinder(x, y, z0, 0.10, H)
            objs.append({"name": nm, "material": "pole", "verts": pv, "faces": pf})
            hv, hf = mesh_box((x, y, z0 + H), (0.4, 0.4, 0.9))
            objs.append({"name": nm + "_head", "material": "signal", "verts": hv, "faces": hf})
        else:
            bv, bf = mesh_box((x, y, z0 + H / 2), (0.5, 0.5, H))
            objs.append({"name": nm, "material": "misc", "verts": bv, "faces": bf})
    return objs


# ---------- Sonder: EV charging station ----------

def ev_charger_objects(chargers, style="pedestal", start=1, beacon=True):
    """Sonder: a curbside EV charger placed in the scene's local-shifted UTM frame.

    chargers: list of {x, y, ground_z, yaw}.
    style="pedestal"   -> ChargePoint CT4000-class: slim body on a plinth, head with a dark screen
                          and teal status bar, DUAL ports (holster + J1772 each side). Magenta locator.
    style="futuristic" -> modern curbside fast charger (Tesla-curbside-inspired, no brand): a sleek
                          curved WHITE monolith (rounded cylinder body + tapered cap) with a cyan
                          light strip and a connector. Cyan locator.
    start: index for the name prefix (ev_charger_01, ev_charger_02, ...) so multiple chargers are
           uniquely named. beacon=True adds a giant locator pillar so it is easy to find in a big block.
    """
    def world(x, y, yaw, lx, ly):
        c, s = math.cos(yaw), math.sin(yaw)
        return (x + lx * c - ly * s, y + lx * s + ly * c)

    objs = []
    for i, ch in enumerate(chargers, start):
        x, y, z0 = ch["x"], ch["y"], ch["ground_z"]
        yaw = ch.get("yaw", 0.0)
        nm = f"ev_charger_{i:02d}"

        def box(suffix, material, center, size):
            v, f = mesh_box(center, size, yaw)
            objs.append({"name": nm + suffix, "material": material, "verts": v, "faces": f})

        def cyl(suffix, material, cx, cy, z, r, h):
            v, f = mesh_cylinder(cx, cy, z, r, h)
            objs.append({"name": nm + suffix, "material": material, "verts": v, "faces": f})

        if style == "futuristic":
            cyl("_base", "ev_base", x, y, z0, 0.32, 0.10)                          # round plinth
            cyl("_body", "ev_white", x, y, z0 + 0.10, 0.28, 2.05)                  # curved white monolith
            cv, cf = mesh_cone(x, y, z0 + 2.15, 0.28, 0.45)                        # tapered futuristic cap
            objs.append({"name": nm + "_cap", "material": "ev_white", "verts": cv, "faces": cf})
            sx, sy = world(x, y, yaw, 0.27, 0.0)                                   # cyan light strip (front)
            box("_strip", "ev_cyan", (sx, sy, z0 + 1.25), (0.04, 0.10, 1.70))
            hx, hy = world(x, y, yaw, 0.26, 0.0)                                   # connector
            cyl("_plug", "metal", hx, hy, z0 + 1.00, 0.05, 0.20)
            mk = "ev_marker2"
        else:  # pedestal (CT4000-class)
            box("_base", "ev_base", (x, y, z0 + 0.08), (0.42, 0.38, 0.16))
            box("_pole", "ev_body", (x, y, z0 + 0.85), (0.20, 0.20, 1.40))
            box("_head", "ev_body", (x, y, z0 + 1.78), (0.44, 0.32, 0.52))
            sx, sy = world(x, y, yaw, 0.17, 0.0)
            box("_screen", "ev_screen", (sx, sy, z0 + 1.80), (0.04, 0.26, 0.22))
            lx, ly = world(x, y, yaw, 0.18, 0.0)
            box("_light", "ev_accent", (lx, ly, z0 + 2.00), (0.06, 0.34, 0.06))
            for side, sfx in ((0.20, "a"), (-0.20, "b")):                          # dual ports
                hx, hy = world(x, y, yaw, 0.0, side)
                box("_holster_" + sfx, "ev_body", (hx, hy, z0 + 1.20), (0.12, 0.08, 0.20))
                gx, gy = world(x, y, yaw, 0.04, side * 1.35)
                cyl("_plug_" + sfx, "metal", gx, gy, z0 + 1.00, 0.045, 0.18)
            mk = "ev_marker"

        if beacon:                                                                 # giant locator pillar
            box("_beacon", mk, (x, y, z0 + 6.5), (0.5, 0.5, 12.0))
            box("_beacontop", mk, (x, y, z0 + 13.0), (1.6, 1.6, 1.6))
    return objs


# back-compat alias (run.py / older callers used ev_station_objects)
ev_station_objects = ev_charger_objects


# ---------- writer ----------

def write_obj(path, objects, mtl_filename=None):
    lines = []
    if mtl_filename:
        lines.append(f"mtllib {mtl_filename}")
    voffset = 0
    for o in objects:
        lines.append(f"o {o['name']}")
        if o.get("material"):
            lines.append(f"usemtl {o['material']}")
        for x, y, z in o["verts"]:
            lines.append(f"v {x:.4f} {y:.4f} {z:.4f}")
        for f in o["faces"]:
            lines.append("f " + " ".join(str(i + 1 + voffset) for i in f))
        voffset += len(o["verts"])
    open(path, "w").write("\n".join(lines) + "\n")


def write_dummy_scene(path="out/scene.obj"):
    """Two car shapes so the APS round-trip can be tested before segmentation exists."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cars = [{"center": (0, 0, 0.75), "length": 4.5, "width": 1.8, "height": 1.5, "yaw": 0},
            {"center": (8, 0, 0.75), "length": 4.5, "width": 1.8, "height": 1.5, "yaw": 0}]
    write_obj(path, car_objects(cars))
