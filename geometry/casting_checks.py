import numpy as np

def check_watertight(mesh):
    return mesh.is_watertight

def check_positive_volume(mesh):
    return mesh.volume > 1e-5

def check_single_component(mesh):
    return mesh.body_count == 1

def check_min_wall(mesh, min_thickness=0.3):
    if mesh.is_empty:
        return False
    origins = mesh.triangles_center - mesh.face_normals * 1e-4
    directions = -mesh.face_normals
    locations, index_ray, index_tri = mesh.ray.intersects_location(
        ray_origins=origins,
        ray_directions=directions,
        multiple_hits=False
    )
    if len(locations) > 0:
        dists = np.linalg.norm(locations - origins[index_ray], axis=1)
        valid = dists > 1e-3
        dists = dists[valid]
        if len(dists) > 0 and np.min(dists) < min_thickness:
            return False
    return True

def check_prong_diameter(mesh, min_dia=0.5):
    # A prong diameter check is a stricter local thickness check for protruding features.
    return check_min_wall(mesh, min_thickness=min_dia)
