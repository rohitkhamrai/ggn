import build123d as bd
from core.mesh_utils import b3d_to_trimesh

def generate_ball_charm(part_id="charm_ball_01", radius=2.0, thickness=0.6):
    """
    Flat disc jewelry charm normalized to 4mm diameter.
    Hangs down gracefully from link drop socket.
    """
    hole_y = radius - 0.7
    with bd.BuildPart() as charm:
        bd.Cylinder(radius, thickness)
        with bd.BuildSketch(bd.Location((0, hole_y, 0))):
            bd.Circle(0.4)
        bd.extrude(amount=thickness * 2.0, both=True, mode=bd.Mode.SUBTRACT)
            
    mesh = b3d_to_trimesh(charm.part)
    
    meta = {
        "schema_version": 1,
        "part_id": part_id,
        "category": "charm",
        "mesh": f"meshes/{part_id}.obj",
        "units": "mm",
        "body": "metal",
        "sockets": [
            {
                "id": "hanger",
                "origin": [0.0, float(hole_y), 0.0],
                "axis": [0.0, 1.0, 0.0], # Points towards the chain link
                "ref": [1.0, 0.0, 0.0],
                "class": "pendant_drop",
                "role": "child"
            }
        ]
    }
    return mesh, meta
