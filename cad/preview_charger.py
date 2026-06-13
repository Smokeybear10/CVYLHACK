"""Render both charger styles to a PNG to eyeball them. No PDAL/APS. Run from cad/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from pipeline.to_cad import ev_charger_objects, MATERIALS

fig = plt.figure(figsize=(10, 7))
for col, style in enumerate(("pedestal", "futuristic")):
    objs = ev_charger_objects([{"x": 0, "y": 0, "ground_z": 0, "yaw": 0.0}], style=style, beacon=False)
    ax = fig.add_subplot(1, 2, col + 1, projection="3d")
    for o in objs:
        V = o["verts"]; c = MATERIALS.get(o["material"], (0.5, 0.5, 0.5))
        ax.add_collection3d(Poly3DCollection([[V[i] for i in f] for f in o["faces"]],
                                             facecolor=c, edgecolor=(0, 0, 0, 0.25), linewidths=0.3))
    ax.set_xlim(-0.7, 0.7); ax.set_ylim(-0.7, 0.7); ax.set_zlim(0, 2.7)
    ax.set_box_aspect((1, 1, 2.0)); ax.view_init(elev=10, azim=40); ax.set_title(style)
plt.savefig("charger_preview.png", dpi=120, bbox_inches="tight")
print("wrote charger_preview.png")
