import build123d as bd
from core.mesh_utils import b3d_to_trimesh

def generate_simple_shank(part_id="shank_01", inner_diameter=16.0, thickness=1.5, width=2.0):
    outer_r = (inner_diameter / 2.0) + thickness
    inner_r = inner_diameter / 2.0
    
    with bd.BuildPart() as shank:
        with bd.BuildSketch(bd.Plane.XZ):
            bd.Circle(outer_r)
            bd.Circle(inner_r, mode=bd.Mode.SUBTRACT)
        bd.extrude(amount=width/2, both=True)
        
        # Cut the top flat for the collet to sit
        with bd.BuildSketch(bd.Location((0, 0, outer_r))):
            bd.Rectangle(width*2, width*2)
        bd.extrude(amount=-1.0, mode=bd.Mode.SUBTRACT)
        
    mesh = b3d_to_trimesh(shank.part)
    
    meta = {
        "schema_version": 1,
        "part_id": part_id,
        "category": "shank",
        "mesh": f"meshes/{part_id}.obj",
        "units": "mm",
        "body": "metal",
        "symmetry": {"axis": [1, 0, 0], "order": 2},
        "dims": {"inner_diameter": inner_diameter, "thickness": thickness, "width": width},
        "sockets": [
            {
                "id": "crown",
                "origin": [0, 0, outer_r - 1.0],
                "axis": [0, 0, 1],
                "ref": [1, 0, 0],
                "class": "shank_crown",
                "role": "parent"
            }
        ]
    }
    return mesh, meta
