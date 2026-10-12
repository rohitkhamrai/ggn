import math
import numpy as np
import build123d as bd
from core.mesh_utils import b3d_to_trimesh

def generate_connector(part_id="connector_y_01", radius=5.0, hole_radius=0.8, thickness=1.2):
    """
    Y-split jewelry connector for necklace drops and chandelier branches.
    Sockets:
      - entry:      top hole [0, 4.0, 0],       axis: [0, 1, 0] (child)
      - exit_left:  bottom-left hole [-3.5, -2.0, 0], axis: [-0.866, -0.5, 0] (parent)
      - exit_right: bottom-right hole [3.5, -2.0, 0], axis: [0.866, -0.5, 0] (parent)
    """
    top_pos = (0.0, radius * 0.8)
    left_x = -radius * 0.7
    right_x = radius * 0.7
    bottom_y = -radius * 0.4
    
    with bd.BuildPart() as conn:
        with bd.BuildSketch(bd.Plane.XY):
            bd.RegularPolygon(radius=radius, side_count=3)
            with bd.Locations([top_pos, (left_x, bottom_y), (right_x, bottom_y)]):
                bd.Circle(hole_radius, mode=bd.Mode.SUBTRACT)
        bd.extrude(amount=thickness / 2.0, both=True)

    mesh = b3d_to_trimesh(conn.part)

    # Direction vectors for exit sockets (pointing outward along triangle symmetry)
    cos30 = math.cos(math.radians(30))
    sin30 = math.sin(math.radians(30))

    meta = {
        "schema_version": 1,
        "part_id": part_id,
        "category": "connector",
        "mesh": f"meshes/{part_id}.obj",
        "units": "mm",
        "body": "metal",
        "sockets": [
            {
                "id": "entry",
                "origin": [float(top_pos[0]), float(top_pos[1]), 0.0],
                "axis": [0.0, 1.0, 0.0],
                "ref": [1.0, 0.0, 0.0],
                "class": "chain_link",
                "role": "child"
            },
            {
                "id": "exit_left",
                "origin": [float(left_x), float(bottom_y), 0.0],
                "axis": [-cos30, -sin30, 0.0],
                "ref": [0.0, 0.0, 1.0],
                "class": "chain_link",
                "role": "parent"
            },
            {
                "id": "exit_right",
                "origin": [float(right_x), float(bottom_y), 0.0],
                "axis": [cos30, -sin30, 0.0],
                "ref": [0.0, 0.0, 1.0],
                "class": "chain_link",
                "role": "parent"
            }
        ]
    }
    return mesh, meta
