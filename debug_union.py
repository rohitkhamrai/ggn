import trimesh
import manifold3d as m3d
import numpy as np

m1 = trimesh.load("jobs/output/temp_collet.obj", force='mesh')
m2 = trimesh.load("jobs/output/temp_shank.obj", force='mesh')

print("Collet bounds:", m1.bounds)
print("Shank bounds:", m2.bounds)

man1 = m3d.Manifold(m3d.Mesh(vert_properties=np.array(m1.vertices, dtype=np.float32), tri_verts=np.array(m1.faces, dtype=np.uint32)))
man2 = m3d.Manifold(m3d.Mesh(vert_properties=np.array(m2.vertices, dtype=np.float32), tri_verts=np.array(m2.faces, dtype=np.uint32)))

print("Man1 status:", man1.status())
print("Man2 status:", man2.status())

res = man1 + man2
print("Res status:", res.status())
print("Res genus:", res.genus())
print("Res num_prop:", res.num_prop())
print("Res components (manifold):", res.num_vert(), "verts")

m3 = res.to_mesh()
v = np.array(m3.vert_properties).reshape(-1, 3)
f = np.array(m3.tri_verts).reshape(-1, 3)
tm = trimesh.Trimesh(vertices=v, faces=f, process=True)
print("Trimesh body count (processed):", tm.body_count)
comps = tm.split()
for i, c in enumerate(comps):
    print(f"Comp {i}: volume {c.volume}, bounds {c.bounds}")
