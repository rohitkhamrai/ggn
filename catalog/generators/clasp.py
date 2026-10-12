import build123d as bd
from core.mesh_utils import b3d_to_trimesh

def generate_clasp(part_id="clasp_lobster_01", length=8.0, width=3.2, thickness=1.4):
    """
    Lobster claw jewelry clasp normalized to 8mm max dimension.
    Sockets:
      - entry: eyelet center [eye_x, 0, 0], axis: [-1, 0, 0]
      - exit:  claw center   [claw_x, 0, 0], axis: [1, 0, 0]
    """
    half_l = length / 2.0
    eye_x = -half_l + (width / 2.0)
    claw_x = half_l - (width / 2.0)
    
    with bd.BuildPart() as clasp:
        with bd.BuildSketch(bd.Plane.XY):
            bd.SlotOverall(length, width)
            with bd.Locations((eye_x, 0)):
                bd.Circle(width * 0.28, mode=bd.Mode.SUBTRACT)
            with bd.Locations((claw_x, 0)):
                bd.Circle(width * 0.32, mode=bd.Mode.SUBTRACT)
        bd.extrude(amount=thickness / 2.0, both=True)

    mesh = b3d_to_trimesh(clasp.part)

    meta = {
        "schema_version": 1,
        "part_id": part_id,
        "category": "clasp",
        "mesh": f"meshes/{part_id}.obj",
        "units": "mm",
        "body": "metal",
        "sockets": [
            {
                "id": "entry",
                "origin": [float(eye_x), 0.0, 0.0],
                "axis": [-1.0, 0.0, 0.0],
                "ref": [0.0, 1.0, 0.0],
                "class": "chain_link",
                "role": "child"
            },
            {
                "id": "exit",
                "origin": [float(claw_x), 0.0, 0.0],
                "axis": [1.0, 0.0, 0.0],
                "ref": [0.0, 0.0, 1.0],
                "class": "chain_link",
                "role": "parent"
            }
        ]
    }
    return mesh, meta
