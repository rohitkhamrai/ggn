import numpy as np
import build123d as bd
from core.mesh_utils import b3d_to_trimesh

def generate_bead(part_id="bead_round_01", radius=2.0, hole_radius=0.6, style="sphere"):
    """
    Jewelry bead with a central through-hole along X axis.
    Sockets:
      - entry: [-radius, 0, 0], axis: [-1, 0, 0], ref: [0, 1, 0], class: chain_link
      - exit:  [radius, 0, 0],  axis: [1, 0, 0],  ref: [0, 1, 0], class: chain_link
    """
    hole_cyl = bd.Cylinder(hole_radius, radius * 3.0)
    
    if style == "barrel":
        base = bd.Cylinder(radius, radius * 1.5)
    elif style == "faceted":
        base = bd.Cone(radius, 0.0, radius) + bd.Cone(radius, 0.0, radius, rotation=(180, 0, 0))
    else: # sphere
        base = bd.Sphere(radius)

    part = base - hole_cyl
    mesh = b3d_to_trimesh(part)
    
    # Rotate mesh from Z-alignment to X-alignment (preserves watertight connectivity)
    # Mapping Z -> X, Y -> Y, X -> -Z
    R_align = np.array([
        [ 0.0, 0.0, 1.0, 0.0],
        [ 0.0, 1.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0],
        [ 0.0, 0.0, 0.0, 1.0]
    ], dtype=float)
    mesh.apply_transform(R_align)

    meta = {
        "schema_version": 1,
        "part_id": part_id,
        "category": "bead",
        "mesh": f"meshes/{part_id}.obj",
        "units": "mm",
        "body": "metal",
        "sockets": [
            {
                "id": "entry",
                "origin": [-radius, 0.0, 0.0],
                "axis": [-1.0, 0.0, 0.0],
                "ref": [0.0, 1.0, 0.0],
                "class": "chain_link",
                "role": "child"
            },
            {
                "id": "exit",
                "origin": [radius, 0.0, 0.0],
                "axis": [1.0, 0.0, 0.0],
                "ref": [0.0, 1.0, 0.0],
                "class": "chain_link",
                "role": "parent"
            }
        ]
    }
    return mesh, meta
