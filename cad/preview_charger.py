"""Render the EV charger model to a PNG so we can eyeball it before touching Autodesk.
No PDAL / APS / creds.  Run from cad/:  python preview_charger.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from pipeline.to_cad import ev_charger_objects, MATERIALS

objs = ev_charger_objects([{"x": 0, "y": 0, "ground_z": 0, "yaw": 0.0}])

fig = plt.figure(figsize=(5, 7))
ax = fig.add_subplot(111, projection="3d")
for o in objs:
    V = o["verts"]
    col = MATERIALS.get(o["material"], (0.5, 0.5, 0.5))
    polys = [[V[i] for i in f] for f in o["faces"]]
    ax.add_collection3d(Poly3DCollection(polys, facecolor=col, edgecolor=(0, 0, 0, 0.25), linewidths=0.3))

ax.set_xlim(-0.6, 0.6); ax.set_ylim(-0.6, 0.6); ax.set_zlim(0, 1.7)
ax.set_box_aspect((1, 1, 1.6))
ax.view_init(elev=10, azim=40)
ax.set_title("Sonder EV charger (CT4000-class)")
plt.savefig("charger_preview.png", dpi=130, bbox_inches="tight")
print("wrote charger_preview.png  parts:", [o["name"] for o in objs])
