import trimesh

def b3d_to_trimesh(part, tolerance=0.01):
    vertices, triangles = part.tessellate(tolerance)
    
    # Handle Vector objects if present, else assume tuple/list
    v_arr = []
    for v in vertices:
        if hasattr(v, 'X'):
            v_arr.append([v.X, v.Y, v.Z])
        else:
            v_arr.append(list(v))
            
    mesh = trimesh.Trimesh(vertices=v_arr, faces=triangles)
    
    if not mesh.is_watertight:
        # OCCT can leave seams. 
        mesh.merge_vertices()
        if not mesh.is_watertight:
            raise ValueError("Tessellated mesh is not watertight even after merge_vertices.")
            
    return mesh
