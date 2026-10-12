import os
import json
from catalog.generators.gem import generate_round_gem
from catalog.generators.collet import generate_round_collet
from catalog.generators.shank import generate_simple_shank

def build_all():
    os.makedirs("catalog/meshes", exist_ok=True)
    os.makedirs("catalog/meta", exist_ok=True)
    
    generators = [
        generate_round_gem,
        generate_round_collet,
        generate_simple_shank
    ]
    
    for gen in generators:
        mesh, meta = gen()
        part_id = meta["part_id"]
        
        # Validate generated part
        if not mesh.is_watertight:
            raise ValueError(f"Validation failed: {part_id} is not watertight")
        if mesh.body_count != 1:
            raise ValueError(f"Validation failed: {part_id} has {mesh.body_count} components, expected 1")
            
        # Save mesh
        mesh.export(f"catalog/{meta['mesh']}")
        
        # Save meta
        with open(f"catalog/meta/{part_id}.json", "w") as f:
            json.dump(meta, f, indent=2)
            
        print(f"Built {part_id}")

if __name__ == "__main__":
    build_all()
