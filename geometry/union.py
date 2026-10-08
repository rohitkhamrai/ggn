import sys
import manifold3d as m3d
import trimesh
import argparse
import numpy as np

def union_meshes(path_a, path_b, out_path):
    mesh_a = trimesh.load(path_a, force='mesh')
    mesh_b = trimesh.load(path_b, force='mesh')
    
    m_a = m3d.Mesh(vert_properties=np.array(mesh_a.vertices, dtype=np.float32), tri_verts=np.array(mesh_a.faces, dtype=np.uint32))
    m_b = m3d.Mesh(vert_properties=np.array(mesh_b.vertices, dtype=np.float32), tri_verts=np.array(mesh_b.faces, dtype=np.uint32))
    man_a = m3d.Manifold(m_a)
    man_b = m3d.Manifold(m_b)
    
    res = man_a + man_b
    
    out_mesh = res.to_mesh()
    # manifold3d to_mesh returns object with vert_properties (flat array usually)
    # Let's extract safely
    vertices = np.array(out_mesh.vert_properties).reshape(-1, 3)
    faces = np.array(out_mesh.tri_verts).reshape(-1, 3)
    trimesh.Trimesh(vertices=vertices, faces=faces).export(out_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("a")
    parser.add_argument("b")
    parser.add_argument("out")
    args = parser.parse_args()
    union_meshes(args.a, args.b, args.out)
