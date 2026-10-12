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

def check_gem_support(gem_mesh: trimesh.Trimesh, final_metal: trimesh.Trimesh, assembly_def=None, metas=None, transforms=None) -> bool:
    try:
        import trimesh.proximity
        import numpy as np
        
        if not assembly_def or not metas or not transforms:
            # Fallback distance check when bare meshes provided (e.g. unit tests)
            closest, distance, _ = trimesh.proximity.closest_point(final_metal, gem_mesh.vertices)
            return float(np.min(distance)) <= 0.1
        
        gem_node = next((n for n in assembly_def if "gem" in n["id"]), None)
        if not gem_node: return False
        
        setting_node = next((n for n in assembly_def if n["id"] == gem_node["parent"]), None)
        if not setting_node: return False
        
        setting_meta = metas[setting_node["id"]]
        T_setting = transforms[setting_node["id"]]
        
        setting_type = setting_meta.get("setting_type", "bezel")
        
        if setting_type == "prong":
            prong_pts = []
            for sock in setting_meta["sockets"]:
                if "prong" in sock["id"].lower():
                    pt_world = T_setting[:3, :3] @ sock["origin"] + T_setting[:3, 3]
                    prong_pts.append(pt_world)
            if not prong_pts: return False
            closest, distance, _ = trimesh.proximity.closest_point(gem_mesh, prong_pts)
            
            # Crush guard: prong tip cannot be exactly 0 (or inside, if we used signed distance)
            if np.min(distance) <= 1e-4:
                return False
                
            return np.max(distance) <= 0.05
            
        elif setting_type == "bezel":
            gem_meta = metas[gem_node["id"]]
            T_gem = transforms[gem_node["id"]]
            s_gem = gem_node.get("scale", 1.0)
            girdle_r = (gem_meta["dims"]["girdle_diameter"] * s_gem) / 2.0
            
            angles = np.linspace(0, 2*np.pi, 36, endpoint=False)
            girdle_pts_local = np.column_stack((np.cos(angles)*girdle_r, np.sin(angles)*girdle_r, np.zeros_like(angles)))
            
            girdle_pts_world = np.hstack((girdle_pts_local, np.ones((len(angles), 1))))
            girdle_pts_world = (T_gem @ girdle_pts_world.T).T[:, :3]
            
            closest, distance, _ = trimesh.proximity.closest_point(final_metal, girdle_pts_world)
            return np.max(distance) <= 0.1
            
        else:
            centroid = gem_mesh.centroid
            bounds = final_metal.bounds
            if not (bounds[0][0] <= centroid[0] <= bounds[1][0] and bounds[0][1] <= centroid[1] <= bounds[1][1]):
                return False
            return True
    except Exception as e:
        print("Support check failed:", e)
        return False
