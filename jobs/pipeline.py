import os
import json
import trimesh
import numpy as np
from core.sampler import sample_assembly
from core.solver import solve_assembly_scales
from core.snap import snap_part
from geometry.union_wrapper import robust_union
from geometry.clearance import check_gem_clearance_boolean
from geometry.casting_checks import check_watertight, check_positive_volume, check_single_component
from geometry.report import generate_report

def run_pipeline(seed=42):
    os.makedirs("jobs/output", exist_ok=True)
    
    assembly_def, mirror = sample_assembly(seed)
    solve_assembly_scales(assembly_def)
    
    # Load metas and compute transforms
    metas = {}
    meshes = {}
    for node in assembly_def:
        pid = node["part_id"]
        with open(f"catalog/meta/{pid}.json", 'r') as f:
            metas[node["id"]] = json.load(f)
        meshes[node["id"]] = trimesh.load(f"catalog/meshes/{pid}.obj", force='mesh')
        
    transforms = {}
    # Base part (shank)
    shank = next(n for n in assembly_def if n["parent"] is None)
    transforms[shank["id"]] = np.eye(4)
    
    # Note: scale whole part record before snapping. 
    # For now, trimesh apply_transform handles mesh scaling, and origin scaling must be done in sockets
    # Let's simplify by assuming snap_part handles it or we pre-scale sockets.
    
    # Wait, spec: "Scale the whole part record (mesh and sockets) before snapping"
    for node in assembly_def:
        s = node.get("scale", 1.0)
        if s != 1.0:
            m = metas[node["id"]]
            for sock in m["sockets"]:
                sock["origin"] = [c * s for c in sock["origin"]]
            meshes[node["id"]].apply_scale(s)
            
    # Collet
    collet = next(n for n in assembly_def if n["id"] == "node_collet")
    transforms[collet["id"]] = snap_part(
        parent_socket=next(s for s in metas[shank["id"]]["sockets"] if s["id"] == collet["socket_pair"][1]),
        child_socket=next(s for s in metas[collet["id"]]["sockets"] if s["id"] == collet["socket_pair"][0]),
        parent_transform=transforms[shank["id"]],
        spin_deg=collet["spin_deg"]
    )
    
    # Gem
    gem = next(n for n in assembly_def if n["id"] == "node_gem")
    transforms[gem["id"]] = snap_part(
        parent_socket=next(s for s in metas[collet["id"]]["sockets"] if s["id"] == gem["socket_pair"][1]),
        child_socket=next(s for s in metas[gem["id"]]["sockets"] if s["id"] == gem["socket_pair"][0]),
        parent_transform=transforms[collet["id"]],
        spin_deg=gem["spin_deg"]
    )
    
    # Apply transforms
    for node in assembly_def:
        meshes[node["id"]].apply_transform(transforms[node["id"]])
        
    if mirror:
        M_mirror = np.eye(4)
        M_mirror[0, 0] = -1.0
        for node in assembly_def:
            mesh = meshes[node["id"]]
            mesh.apply_transform(M_mirror)
            mesh.fix_normals()
            assert mesh.volume > 1e-5, f"Mirrored volume of {node['id']} must be positive"
            assert mesh.is_winding_consistent, f"Mirrored mesh of {node['id']} has inconsistent winding"
            transforms[node["id"]] = M_mirror @ transforms[node["id"]]
        
    # Metal boolean union
    meshes["node_collet"].export("jobs/output/temp_collet.obj")
    meshes["node_shank"].export("jobs/output/temp_shank.obj")
    
    union_success = robust_union("jobs/output/temp_shank.obj", "jobs/output/temp_collet.obj", "jobs/output/metal.obj")
    if not union_success:
        print("Union failed")
        return False
        
    final_metal = trimesh.load("jobs/output/metal.obj", force='mesh')
    gem_mesh = meshes["node_gem"]
    gem_mesh.export("jobs/output/gem.obj")
    
    # Export seed-named copies for batch rendering
    final_metal.export(f"jobs/output/seed_{seed}_metal.obj")
    gem_mesh.export(f"jobs/output/seed_{seed}_gem.obj")
    
    # Checks
    from geometry.clearance import check_gem_support
    checks = {
        "watertight": check_watertight(final_metal),
        "positive_volume": check_positive_volume(final_metal),
        "single_component": check_single_component(final_metal),
        "gem_clearance": check_gem_clearance_boolean(gem_mesh, final_metal),
        "gem_support": check_gem_support(gem_mesh, final_metal, assembly_def, metas, transforms)
    }
    
    report = generate_report(final_metal, checks)
    
    manifest = {
        "schema_version": 1,
        "units": "mm",
        "seed": seed,
        "mirror": mirror,
        "parts": [
            {
                "part_id": n["part_id"],
                "instance": n["id"],
                "scale": n["scale"],
                "spin_deg": n["spin_deg"],
                "transform": transforms[n["id"]].tolist()
            } for n in assembly_def
        ],
        "report": report
    }
    
    with open("jobs/output/assembly.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    return report

if __name__ == "__main__":
    passes = 0
    total = 400
    failures = {"union_crashed": 0, "watertight": 0, "positive_volume": 0, "single_component": 0, "gem_clearance": 0, "gem_support": 0}
    for i in range(total):
        report = run_pipeline(i)
        if report is False:
            failures["union_crashed"] += 1
        elif report["pass"]:
            passes += 1
        else:
            for k, v in report["checks"].items():
                if not v:
                    failures[k] = failures.get(k, 0) + 1
    print(f"Pass rate: {passes}/{total}")
    print("Failures breakdown:", failures)
