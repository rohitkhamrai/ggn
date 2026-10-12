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

def run_pipeline(user_text: str, seed: int = 42, out_dir: str = "out/design_001", exit_on_fail: bool = False):
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
    T_shank = np.eye(4)
    s_crown = next(s for s in shank_meta["sockets"] if s["id"] == "crown")
    c_base = next(s for s in collet_meta["sockets"] if s["id"] == "base")
    T_collet = snap_part(s_crown, c_base, T_shank, spin_deg=0.0)

    c_seat = next(s for s in collet_meta["sockets"] if s["id"] == "seat")
    g_girdle = next(s for s in gem_meta["sockets"] if s["id"] == "girdle")
    T_gem = snap_part(c_seat, g_girdle, T_collet, spin_deg=0.0)

    metal_parts_w = [shank_mesh.copy().apply_transform(T_shank), collet_mesh.copy().apply_transform(T_collet)]
    gem_parts_w = [gem_mesh.copy().apply_transform(T_gem)]

    assembly_parts = [
        {"id": "shank", "part_id": shank_meta["part_id"], "transform": T_shank.tolist()},
        {"id": "collet", "part_id": collet_meta["part_id"], "transform": T_collet.tolist()},
        {"id": "gem_0", "part_id": gem_meta["part_id"], "transform": T_gem.tolist()}
    ]

    assembly_def = [
        {"id": "shank", "parent": None},
        {"id": "collet", "parent": "shank"},
        {"id": "gem_0", "parent": "collet"}
    ]
    metas = {"shank": shank_meta, "collet": collet_meta, "gem_0": gem_meta}
    transforms = {"shank": T_shank, "collet": T_collet, "gem_0": T_gem}

    # Handle side stones if present
    side_stones = spec.get("side_stones") or []
    for idx, s in enumerate(side_stones):
        s_diam = float(s.get("diameter_mm", gem_diam * 0.6))
        s_collet_m, s_collet_meta = generate_round_collet(part_id=f"collet_side_{idx}", seat_diameter=s_diam)
        s_gem_m, s_gem_meta = generate_round_gem(part_id=f"gem_{idx+1}", girdle_diameter=s_diam)
        s_collet_m.export(os.path.join(meshes_dir, f"collet_side_{idx}.obj"))
        s_gem_m.export(os.path.join(meshes_dir, f"gem_{idx+1}.obj"))

        c_s_seat = next(sock for sock in s_collet_meta["sockets"] if sock["id"] == "seat")
        g_s_girdle = next(sock for sock in s_gem_meta["sockets"] if sock["id"] == "girdle")

        sign = -1.0 if idx == 0 else 1.0
        dx = sign * (gem_diam/2 + s_diam/2 + 0.8)
        T_side = T_collet.copy()
        T_side[0, 3] += dx
        T_side[2, 3] -= 0.4

        T_gem_s = snap_part(c_s_seat, g_s_girdle, T_side, spin_deg=0.0)

        metal_parts_w.append(s_collet_m.copy().apply_transform(T_side))
        gem_parts_w.append(s_gem_m.copy().apply_transform(T_gem_s))

        collet_id = f"collet_side_{idx}"
        gem_id = f"gem_{idx+1}"
        assembly_parts.append({"id": collet_id, "part_id": s_collet_meta["part_id"], "transform": T_side.tolist()})
        assembly_parts.append({"id": gem_id, "part_id": s_gem_meta["part_id"], "transform": T_gem_s.tolist()})
        assembly_def.append({"id": collet_id, "parent": "shank"})
        assembly_def.append({"id": gem_id, "parent": collet_id})
        metas[collet_id] = s_collet_meta
        metas[gem_id] = s_gem_meta
        transforms[collet_id] = T_side
        transforms[gem_id] = T_gem_s

    assembly_manifest = {
        "schema_version": 1,
        "units": "mm",
        "seed": seed,
        "spec": spec,
        "parts": assembly_parts
    }
    with open(os.path.join(out_dir, "assembly.json"), "w") as f:
        json.dump(assembly_manifest, f, indent=2)

    # Step 4 — Gatekeeper: Iterative robust boolean union of metal parts
    curr_metal_path = os.path.join(out_dir, "temp_part_0.obj")
    metal_parts_w[0].export(curr_metal_path)
    temp_files = [curr_metal_path]

    for i in range(1, len(metal_parts_w)):
        next_part_path = os.path.join(out_dir, f"temp_part_{i}.obj")
        metal_parts_w[i].export(next_part_path)
        temp_files.append(next_part_path)
        out_union_path = os.path.join(out_dir, f"temp_union_{i}.obj")
        temp_files.append(out_union_path)
        union_ok = robust_union(curr_metal_path, next_part_path, out_union_path)
        if not union_ok:
            report = {"pass": False, "error": f"Metal boolean union failed at step {i}"}
            with open(os.path.join(out_dir, "report.json"), "w") as f:
                json.dump(report, f, indent=2)
            for p in temp_files:
                if os.path.exists(p): os.remove(p)
            if exit_on_fail:
                sys.exit(1)
            return report
        curr_metal_path = out_union_path

    metal_mesh = trimesh.load(curr_metal_path, force="mesh")
    for p in temp_files:
        if os.path.exists(p): os.remove(p)

    clearance_ok = all(check_gem_clearance_boolean(g, metal_mesh) for g in gem_parts_w)

    checks = {
        "watertight": check_watertight(metal_mesh),
        "positive_volume": check_positive_volume(metal_mesh),
        "single_component": check_single_component(metal_mesh),
        "gem_clearance": clearance_ok,
        "gem_support": check_gem_support(gem_parts_w[0], metal_mesh, assembly_def, metas, transforms)
    }

    report = generate_report(metal_mesh, checks)
    with open(os.path.join(out_dir, "report.json"), "w") as f:
        json.dump(report, f, indent=2)

    if not report["pass"]:
        print("FAIL — gatekeeper checks failed:", report["checks"])
        if exit_on_fail:
            sys.exit(1)
        return report

    # Step 5 — Export final STLs
    metal_stl_path = os.path.join(out_dir, "metal.stl")
    metal_mesh.export(metal_stl_path)

    for idx, g in enumerate(gem_parts_w):
        gem_stl_path = os.path.join(gems_dir, f"gem_{idx}.stl")
        g.export(gem_stl_path)

    print(f"PASS — wrote metal.stl and {len(gem_parts_w)} gem meshes to {out_dir}/")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jewelry Engine End-to-End Pipeline")
    parser.add_argument("text", type=str, help="Natural language jewelry prompt")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--out", type=str, default="out/design_001", help="Output directory")

    args = parser.parse_args()
    run_pipeline(args.text, seed=args.seed, out_dir=args.out, exit_on_fail=True)
