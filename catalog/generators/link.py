import math
import build123d as bd
from core.mesh_utils import b3d_to_trimesh

def generate_round_link(part_id="link_round_01", major_radius=2.5, minor_radius=0.5, gap=0.1, bend_deg=0.0):
    """
    Round torus chain link with entry, exit, and drop sockets.
    """
    with bd.BuildPart() as link:
        bd.Torus(major_radius, minor_radius)
        
    mesh = b3d_to_trimesh(link.part)
    
    # Centers must be (2R - 2r + gap) apart to loop through each other's holes.
    socket_x = major_radius - minor_radius + (gap / 2.0)
    
    bend_rad = math.radians(bend_deg)
    c, s = math.cos(bend_rad), math.sin(bend_rad)
    exit_axis = [c, s, 0.0]
    exit_ref = [0.0, 0.0, 1.0] # 90 deg twist
    
    meta = {
        "schema_version": 1,
        "part_id": part_id,
        "category": "link",
        "mesh": f"meshes/{part_id}.obj",
        "units": "mm",
        "body": "metal",
        "sockets": [
            {
                "id": "entry",
                "origin": [-socket_x, 0.0, 0.0],
                "axis": [-1.0, 0.0, 0.0],
                "ref": [0.0, 1.0, 0.0],
                "class": "chain_link",
                "role": "child"
            },
            {
                "id": "exit",
                "origin": [socket_x, 0.0, 0.0],
                "axis": exit_axis,
                "ref": exit_ref,
                "class": "chain_link",
                "role": "parent",
                "spin": {"free": True, "step_deg": 90}
            },
            {
                "id": "drop",
                "origin": [0.0, 0.0, -major_radius],
                "axis": [0.0, 0.0, -1.0],
                "ref": [1.0, 0.0, 0.0],
                "class": "pendant_drop",
                "role": "parent"
            }
        ]
    }
    return mesh, meta

def generate_oval_link(part_id="link_oval_01", length=6.0, width=3.5, wire_width=0.8, thickness=1.0, bend_deg=0.0):
    """
    Oval cable chain link with entry, exit, and drop sockets.
    """
    inner_len = length - 2.0 * wire_width
    inner_width = width - 2.0 * wire_width
    
    with bd.BuildPart() as link:
        with bd.BuildSketch(bd.Plane.XY):
            bd.SlotOverall(length, width)
            bd.SlotOverall(inner_len, inner_width, mode=bd.Mode.SUBTRACT)
        bd.extrude(amount=thickness / 2.0, both=True)
        
    mesh = b3d_to_trimesh(link.part)
    
    socket_x = (inner_len / 2.0) - (wire_width / 2.0)
    bend_rad = math.radians(bend_deg)
    c, s = math.cos(bend_rad), math.sin(bend_rad)
    exit_axis = [c, s, 0.0]
    exit_ref = [0.0, 0.0, 1.0] # 90 deg twist
    
    meta = {
        "schema_version": 1,
        "part_id": part_id,
        "category": "link",
        "mesh": f"meshes/{part_id}.obj",
        "units": "mm",
        "body": "metal",
        "sockets": [
            {
                "id": "entry",
                "origin": [-socket_x, 0.0, 0.0],
                "axis": [-1.0, 0.0, 0.0],
                "ref": [0.0, 1.0, 0.0],
                "class": "chain_link",
                "role": "child"
            },
            {
                "id": "exit",
                "origin": [socket_x, 0.0, 0.0],
                "axis": exit_axis,
                "ref": exit_ref,
                "class": "chain_link",
                "role": "parent",
                "spin": {"free": True, "step_deg": 90}
            },
            {
                "id": "drop",
                "origin": [0.0, 0.0, -width / 2.0],
                "axis": [0.0, 0.0, -1.0],
                "ref": [1.0, 0.0, 0.0],
                "class": "pendant_drop",
                "role": "parent"
            }
        ]
    }
    return mesh, meta

def generate_link(part_id="link_01", shape="round", **kwargs):
    if shape == "oval":
        return generate_oval_link(part_id=part_id, **kwargs)
    return generate_round_link(part_id=part_id, **kwargs)
