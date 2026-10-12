import json
import trimesh
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os

mesh = trimesh.load("jobs/output/metal.obj")
gem = trimesh.load("catalog/meshes/gem_round_01.obj")

with open("jobs/output/assembly.json", "r") as f:
    manifest = json.load(f)

for part in manifest["parts"]:
    if part["instance"] == "node_gem":
        gem.apply_transform(np.array(part["transform"]).reshape(4,4))

fig = plt.figure(figsize=(15, 5))

# Front view
ax1 = fig.add_subplot(131, projection='3d')
ax1.view_init(elev=0, azim=90)
ax1.add_collection3d(Poly3DCollection(mesh.vertices[mesh.faces], alpha=0.5, facecolor='gold', edgecolor='k', linewidth=0.1))
ax1.add_collection3d(Poly3DCollection(gem.vertices[gem.faces], alpha=0.8, facecolor='cyan', edgecolor='k', linewidth=0.1))
ax1.set_xlim([-10, 10]); ax1.set_ylim([-10, 10]); ax1.set_zlim([-10, 15])
ax1.set_title("Front View")

# Side view
ax2 = fig.add_subplot(132, projection='3d')
ax2.view_init(elev=0, azim=0)
ax2.add_collection3d(Poly3DCollection(mesh.vertices[mesh.faces], alpha=0.5, facecolor='gold', edgecolor='k', linewidth=0.1))
ax2.add_collection3d(Poly3DCollection(gem.vertices[gem.faces], alpha=0.8, facecolor='cyan', edgecolor='k', linewidth=0.1))
ax2.set_xlim([-10, 10]); ax2.set_ylim([-10, 10]); ax2.set_zlim([-10, 15])
ax2.set_title("Side View")

# Cross section (Y=0)
slice = mesh.section(plane_origin=[0,0,0], plane_normal=[0,1,0])
gem_slice = gem.section(plane_origin=[0,0,0], plane_normal=[0,1,0])
ax3 = fig.add_subplot(133)
if slice:
    for entity in slice.entities:
        pts = slice.vertices[entity.points]
        ax3.plot(pts[:, 0], pts[:, 2], color='goldenrod', linewidth=2)
if gem_slice:
    for entity in gem_slice.entities:
        pts = gem_slice.vertices[entity.points]
        ax3.plot(pts[:, 0], pts[:, 2], color='c', linewidth=2)
ax3.set_xlim([-10, 10]); ax3.set_ylim([-10, 15])
ax3.set_title("Cross Section (Y=0)")
ax3.set_aspect('equal')

plt.tight_layout()
plt.savefig("jobs/output/assembly_views.png", dpi=150)
print("Saved jobs/output/assembly_views.png")
