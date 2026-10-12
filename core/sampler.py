import random

def sample_assembly(seed=42):
    rng = random.Random(seed)
    
    assembly_def = [
        {"id": "node_gem", "part_id": "gem_round_01", "scale": rng.uniform(0.8, 1.2), "parent": "node_collet", "socket_pair": ("girdle", "seat"), "spin_deg": 0.0},
        {"id": "node_collet", "part_id": "collet_round_04", "scale": 1.0, "parent": "node_shank", "socket_pair": ("base", "crown"), "spin_deg": float(rng.choice([0, 90, 180, 270]))},
        {"id": "node_shank", "part_id": "shank_01", "scale": rng.uniform(0.8, 1.5), "parent": None, "socket_pair": None, "spin_deg": 0.0}
    ]
    
    mirror = rng.choice([True, False])
    return assembly_def, mirror
