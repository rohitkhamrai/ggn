import build123d as bd
from core.mesh_utils import b3d_to_trimesh

def generate_round_collet(part_id="collet_round_04", seat_diameter=6.5, seat_depth=1.8, min_wall=0.6):
    outer_r = (seat_diameter / 2.0) + min_wall
    inner_r = (seat_diameter / 2.0)
    height = seat_depth + 1.0 # arbitrary total height
    
    # A simple conical collet
    with bd.BuildPart() as collet:
        with bd.BuildSketch() as sk_bottom:
            bd.Circle(outer_r * 0.9)
        with bd.BuildSketch(bd.Location((0, 0, height))) as sk_top:
            bd.Circle(outer_r)
        bd.loft()
        
        # cut the inside
        with bd.BuildSketch(bd.Location((0, 0, height))) as cut_sk:
            bd.Circle(inner_r)
        bd.extrude(amount=-seat_depth, mode=bd.Mode.SUBTRACT)
        
    mesh = b3d_to_trimesh(collet.part)
    
    meta = {
        "schema_version": 1,
        "part_id": part_id,
        "category": "setting",
        "mesh": f"meshes/{part_id}.obj",
        "units": "mm",
        "body": "metal",
        "setting_type": "bezel",
        "symmetry": {"axis": [0, 0, 1], "order": 1},
        "params": {"scale": {"min": 0.8, "max": 1.4, "uniform": True}},
        "dims": {"seat_diameter": seat_diameter, "seat_depth": seat_depth, "min_wall": min_wall},
        "sockets": [
            {
                "id": "base",
                "origin": [0, 0, 0],
                "axis": [0, 0, -1],
                "ref": [1, 0, 0],
                "class": "shank_crown",
                "role": "child",
                "spin": {"free": True, "step_deg": 90},
                "embed_mm": 0.3
            },
            {
                "id": "seat",
                "origin": [0, 0, height],
                "axis": [0, 0, 1],
                "ref": [1, 0, 0],
                "class": "gem_seat_round",
                "role": "parent",
                "size_key": "seat_diameter"
            },
            {
                "id": "hanger",
                "origin": [0, outer_r, height/2],
                "axis": [0, 1, 0], # pointing out radially
                "ref": [0, 0, 1], # pointing up
                "class": "pendant_drop",
                "role": "child"
            }
        ]
    }
    return mesh, meta
