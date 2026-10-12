import os
import json
import numpy as np
import trimesh
from catalog.generators.link import generate_round_link
from catalog.generators.charm import generate_ball_charm

def run_chain(num_links=24):
    os.makedirs("jobs/output", exist_ok=True)
    os.makedirs("meshes", exist_ok=True)
    
    assembly_def = []
    transforms = {}
    combined_mesh = trimesh.Trimesh()
    
    # Generate the link (ponytail: just one base mesh used multiple times)
    mesh, meta = generate_round_link("link_round_01", major_radius=3.0, minor_radius=0.6, gap=0.2)
    mesh.export(meta["mesh"])
    
    # Build sequence
    for i in range(num_links):
        node_id = f"link_{i}"
        
        if i == 0:
            # First link is at origin
            transform = np.eye(4)
        else:
            # Snap this link's 'entry' to previous link's 'exit'
            prev_id = f"link_{i-1}"
            prev_exit = next(s for s in meta["sockets"] if s["id"] == "exit")
            this_entry = next(s for s in meta["sockets"] if s["id"] == "entry")
            
            from core.snap import snap_part
            transform = snap_part(prev_exit, this_entry, transforms[prev_id])
            
        transforms[node_id] = transform
        
        # Add to assembly manifest
        assembly_def.append({
            "id": node_id,
            "part_id": meta["part_id"],
            "scale": 1.0,
            "spin_deg": 0.0,
            "transform": transform.tolist()
        })
        
        # Add to combined mesh
        inst_mesh = mesh.copy()
        inst_mesh.apply_transform(transform)
        combined_mesh = combined_mesh + inst_mesh
        
        # Branching logic for meaningful composite design
        if i == 6 or i == 18:
            # Add flat disc charm
            charm_id = f"charm_{i}"
            this_drop = next(s for s in meta["sockets"] if s["id"] == "drop")
            
            charm_mesh_inst, charm_meta = generate_ball_charm(f"charm_ball_{i}", radius=3.0)
            charm_hanger = next(s for s in charm_meta["sockets"] if s["id"] == "hanger")
            
            charm_tf = snap_part(this_drop, charm_hanger, transform)
            transforms[charm_id] = charm_tf
            
            assembly_def.append({
                "id": charm_id,
                "part_id": charm_meta["part_id"],
                "scale": 1.0,
                "spin_deg": 0.0,
                "transform": charm_tf.tolist()
            })
            
            charm_mesh_inst.apply_transform(charm_tf)
            combined_mesh = combined_mesh + charm_mesh_inst
            
        elif i == 12:
            # Add center pendant (collet + gem)
            from catalog.generators.collet import generate_round_collet
            from catalog.generators.gem import generate_round_gem
            
            collet_id = "center_collet"
            gem_id = "center_gem"
            
            this_drop = next(s for s in meta["sockets"] if s["id"] == "drop")
            
            # Generate collet and gem meshes (large center pieces)
            collet_mesh_inst, collet_meta = generate_round_collet(part_id="pendant_collet", seat_diameter=8.0)
            gem_mesh_inst, gem_meta = generate_round_gem(part_id="pendant_gem", girdle_diameter=8.0)
            
            # Snap collet to link
            collet_hanger = next(s for s in collet_meta["sockets"] if s["id"] == "hanger")
            collet_tf = snap_part(this_drop, collet_hanger, transform)
            transforms[collet_id] = collet_tf
            
            assembly_def.append({
                "id": collet_id,
                "part_id": collet_meta["part_id"],
                "scale": 1.0,
                "spin_deg": 0.0,
                "transform": collet_tf.tolist()
            })
            collet_mesh_inst.apply_transform(collet_tf)
            combined_mesh = combined_mesh + collet_mesh_inst
            
            # Snap gem to collet
            collet_seat = next(s for s in collet_meta["sockets"] if s["id"] == "seat")
            gem_pavilion = next(s for s in gem_meta["sockets"] if s["id"] == "pavilion")
            gem_tf = snap_part(collet_seat, gem_pavilion, collet_tf)
            transforms[gem_id] = gem_tf
            
            assembly_def.append({
                "id": gem_id,
                "part_id": gem_meta["part_id"],
                "scale": 1.0,
                "spin_deg": 0.0,
                "transform": gem_tf.tolist()
            })
            gem_mesh_inst.apply_transform(gem_tf)
            
            # Export gem separately because it uses a different material!
            gem_mesh_inst.export("jobs/output/chain_gem.obj")
            
    combined_mesh.export("jobs/output/chain_metal.obj")
    
    with open("jobs/output/chain_assembly.json", "w") as f:
        json.dump({"assembly": assembly_def}, f, indent=2)
        
    print(f"Built chain with {num_links} links.")
    
if __name__ == "__main__":
    run_chain(24)
