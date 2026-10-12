import os
import sys
import json
import sqlite3

def export_gallery(db_path="out/designs.db", out_json="out/gallery.json"):
    if not os.path.exists(db_path):
        print(f"Error: {db_path} does not exist.")
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT hash, seed, out_dir, timestamp FROM designs")
    rows = cursor.fetchall()
    conn.close()

    designs = []
    for h, seed, out_dir, ts in rows:
        norm_dir = out_dir.replace("\\", "/")
        design_id = os.path.basename(norm_dir)
        
        spec_path = os.path.join(norm_dir, "spec.json")
        report_path = os.path.join(norm_dir, "report.json")

        spec = {}
        if os.path.exists(spec_path):
            with open(spec_path, "r") as f:
                spec = json.load(f)

        report = {}
        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                report = json.load(f)

        # Compute cheap_score: stone_coverage = center_stone_dia / inner_diam
        center_stone = spec.get("center_stone") or {}
        stone_diam = float(center_stone.get("diameter_mm", 6.5))
        inner_diam = float(spec.get("inner_diameter_mm", 17.3))
        score = stone_diam / inner_diam if inner_diam > 0 else 0.0

        item = {
            "id": design_id,
            "hash": h,
            "seed": seed,
            "out_dir": norm_dir,
            "metal_stl": f"{norm_dir}/metal.stl",
            "gem_stl": f"{norm_dir}/gems/gem_0.stl",
            "spec": spec,
            "report": report,
            "score": round(score, 4),
            "timestamp": ts
        }
        designs.append(item)

    # Sort descending by score
    designs.sort(key=lambda d: d["score"], reverse=True)

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(designs, f, indent=2)

    msg = f"Exported {len(designs)} designs to {out_json}"
    print(msg)
    return len(designs)

if __name__ == "__main__":
    export_gallery()
