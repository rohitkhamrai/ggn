import trimesh
import numpy as np

def generate_round_gem(part_id="gem_round_01", girdle_diameter=6.5, table_diameter=3.5, crown_height=1.0, pavilion_depth=1.5):
    # Create points for a convex hull brilliant approximation
    points = []
    # Culet
    points.append([0, 0, -pavilion_depth])
    # Girdle (16 points)
    r_girdle = girdle_diameter / 2.0
    for i in range(16):
        theta = i * (2 * np.pi / 16)
        points.append([r_girdle * np.cos(theta), r_girdle * np.sin(theta), 0])
    # Table (8 points)
    r_table = table_diameter / 2.0
    for i in range(8):
        theta = i * (2 * np.pi / 8) + (np.pi / 8)
        points.append([r_table * np.cos(theta), r_table * np.sin(theta), crown_height])
        
    mesh = trimesh.convex.convex_hull(points)
    
    meta = {
        "schema_version": 1,
        "part_id": part_id,
        "category": "gem",
        "mesh": f"meshes/{part_id}.obj",
        "units": "mm",
        "body": "gem",
        "symmetry": {"axis": [0, 0, 1], "order": 16},
        "dims": {
            "girdle_diameter": girdle_diameter,
            "table_diameter": table_diameter,
            "crown_height": crown_height,
            "pavilion_depth": pavilion_depth
        },
        "sockets": [
            {
                "id": "girdle",
                "origin": [0, 0, 0],
                "axis": [0, 0, -1],
                "ref": [1, 0, 0],
                "class": "gem_seat_round",
                "role": "child"
            }
        ]
    }
    return mesh, meta
