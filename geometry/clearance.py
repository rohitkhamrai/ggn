import manifold3d as m3d
import trimesh
import numpy as np

def check_gem_clearance_boolean(gem_mesh: trimesh.Trimesh, metal_mesh: trimesh.Trimesh) -> bool:
    """
    Returns True if gem is CLEAR of the metal (no intersection).
    Uses manifold3d for boolean intersection volume.
    """
    m_gem = m3d.Mesh(vert_properties=np.array(gem_mesh.vertices, dtype=np.float32), tri_verts=np.array(gem_mesh.faces, dtype=np.uint32))
    m_metal = m3d.Mesh(vert_properties=np.array(metal_mesh.vertices, dtype=np.float32), tri_verts=np.array(metal_mesh.faces, dtype=np.uint32))
    
    try:
        man_gem = m3d.Manifold(m_gem)
        man_metal = m3d.Manifold(m_metal)
        
        intersection = man_gem ^ man_metal
        return intersection.volume() < 1e-5
    except Exception as e:
        print(f"Clearance check failed: {e}")
        return False

def check_gem_support(gem_mesh: trimesh.Trimesh, metal_mesh: trimesh.Trimesh, max_dist=0.05) -> bool:
    """
    Checks if gem is touching the metal or close enough to be supported.
    Uses surface sampling to approximate true surface-to-surface distance,
    meaning we can reliably measure from prong tips to the gem girdle.
    """
    try:
        import trimesh.proximity
        import trimesh.sample
        # Sample points on the gem surface (which includes the girdle)
        gem_pts, _ = trimesh.sample.sample_surface(gem_mesh, 5000)
        closest, distance, triangle_id = trimesh.proximity.closest_point(metal_mesh, gem_pts)
        min_dist = np.min(distance)
        return min_dist <= max_dist
    except Exception as e:
        print("Support check failed:", e)
        return False
