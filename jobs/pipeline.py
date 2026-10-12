import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import argparse
import numpy as np
import trimesh

from catalog.compiler import compile_spec
from catalog.generators.gem import generate_round_gem
from catalog.generators.collet import generate_round_collet
from catalog.generators.shank import generate_simple_shank
from core.snap import snap_part
from geometry.union_wrapper import robust_union
from geometry.clearance import check_gem_clearance_boolean, check_gem_support
from geometry.casting_checks import check_watertight, check_positive_volume, check_single_component
from geometry.report import generate_report

def run_pipeline(user_text: str, seed: int = 42, out_dir: str = "out/design_001"):
    os.makedirs(out_dir, exist_ok=True)
    meshes_dir = os.path.join(out_dir, "meshes")
    gems_dir = os.path.join(out_dir, "gems")
    os.makedirs(meshes_dir, exist_ok=True)
    os.makedirs(gems_dir, exist_ok=True)

    # Step 1 — Compile text to JewelrySpec
    spec = compile_spec(user_text)
    with open(os.path.join(out_dir, "spec.json"), "w") as f:
        json.dump(spec, f, indent=2)

    # Step 2 — Generate geometry from spec
    center = spec.get("center_stone") or {"diameter_mm": 6.5}
    gem_diam = float(center.get("diameter_mm", 6.5))
    inner_diam = float(spec.get("inner_diameter_mm", 17.3))

    # Shank
    shank_mesh, shank_meta = generate_simple_shank(part_id="shank", inner_diameter=inner_diam)
    # Collet (matched to gem diameter)
    collet_mesh, collet_meta = generate_round_collet(part_id="collet", seat_diameter=gem_diam)
    # Gem
    gem_mesh, gem_meta = generate_round_gem(part_id="gem_0", girdle_diameter=gem_diam)

    shank_mesh.export(os.path.join(meshes_dir, "shank.obj"))
    collet_mesh.export(os.path.join(meshes_dir, "collet.obj"))
    gem_mesh.export(os.path.join(meshes_dir, "gem_0.obj"))

    # Step 3 — Snap assembly
    # 1. Shank is at world origin
    T_shank = np.eye(4)

    # 2. Collet base snaps to shank crown
    s_crown = next(s for s in shank_meta["sockets"] if s["id"] == "crown")
    c_base = next(s for s in collet_meta["sockets"] if s["id"] == "base")
    T_collet = snap_part(s_crown, c_base, T_shank, spin_deg=0.0)

    # 3. Gem girdle snaps to collet seat
    c_seat = next(s for s in collet_meta["sockets"] if s["id"] == "seat")
    g_girdle = next(s for s in gem_meta["sockets"] if s["id"] == "girdle")
    T_gem = snap_part(c_seat, g_girdle, T_collet, spin_deg=0.0)

    # Transform meshes
    shank_w = shank_mesh.copy()
    shank_w.apply_transform(T_shank)

    collet_w = collet_mesh.copy()
    collet_w.apply_transform(T_collet)

    gem_w = gem_mesh.copy()
    gem_w.apply_transform(T_gem)

    # Manifest
    assembly_manifest = {
        "schema_version": 1,
        "units": "mm",
        "seed": seed,
        "spec": spec,
        "parts": [
            {"id": "shank", "part_id": shank_meta["part_id"], "transform": T_shank.tolist()},
            {"id": "collet", "part_id": collet_meta["part_id"], "transform": T_collet.tolist()},
            {"id": "gem_0", "part_id": gem_meta["part_id"], "transform": T_gem.tolist()}
        ]
    }
    with open(os.path.join(out_dir, "assembly.json"), "w") as f:
        json.dump(assembly_manifest, f, indent=2)

    # Step 4 — Gatekeeper
    temp_shank = os.path.join(out_dir, "temp_shank.obj")
    temp_collet = os.path.join(out_dir, "temp_collet.obj")
    temp_metal = os.path.join(out_dir, "temp_metal.obj")
    shank_w.export(temp_shank)
    collet_w.export(temp_collet)

    union_ok = robust_union(temp_shank, temp_collet, temp_metal)
    if not union_ok:
        report = {"pass": False, "error": "Metal boolean union failed"}
        with open(os.path.join(out_dir, "report.json"), "w") as f:
            json.dump(report, f, indent=2)
        print("Union failed")
        sys.exit(1)

    metal_mesh = trimesh.load(temp_metal, force="mesh")
    # Clean temp files
    for p in [temp_shank, temp_collet, temp_metal]:
        if os.path.exists(p): os.remove(p)

    assembly_def = [
        {"id": "shank", "parent": None},
        {"id": "collet", "parent": "shank"},
        {"id": "gem_0", "parent": "collet"}
    ]
    metas = {"shank": shank_meta, "collet": collet_meta, "gem_0": gem_meta}
    transforms = {"shank": T_shank, "collet": T_collet, "gem_0": T_gem}

    checks = {
        "watertight": check_watertight(metal_mesh),
        "positive_volume": check_positive_volume(metal_mesh),
        "single_component": check_single_component(metal_mesh),
        "gem_clearance": check_gem_clearance_boolean(gem_w, metal_mesh),
        "gem_support": check_gem_support(gem_w, metal_mesh, assembly_def, metas, transforms)
    }

    report = generate_report(metal_mesh, checks)
    with open(os.path.join(out_dir, "report.json"), "w") as f:
        json.dump(report, f, indent=2)

    if not report["pass"]:
        print("FAIL — gatekeeper checks failed:", report["checks"])
        sys.exit(1)

    # Step 5 — Export final STLs
    metal_stl_path = os.path.join(out_dir, "metal.stl")
    metal_mesh.export(metal_stl_path)

    gem_stl_path = os.path.join(gems_dir, "gem_0.stl")
    gem_w.export(gem_stl_path)

    print(f"PASS — wrote metal.stl and 1 gem meshes to {out_dir}/")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jewelry Engine End-to-End Pipeline")
    parser.add_argument("text", type=str, help="Natural language jewelry prompt")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--out", type=str, default="out/design_001", help="Output directory")

    args = parser.parse_args()
    run_pipeline(args.text, seed=args.seed, out_dir=args.out)
