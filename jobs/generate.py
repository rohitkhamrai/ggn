import os
import sys
import argparse
import random
import hashlib
import sqlite3
import shutil
import json
from datetime import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from jobs.pipeline import run_pipeline

def init_db(db_path: str = "out/designs.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS designs (
            hash TEXT PRIMARY KEY,
            seed INTEGER,
            out_dir TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn

def load_catalog_index(index_path: str = "catalog/index.json") -> dict:
    with open(index_path, "r") as f:
        return json.load(f)

def generate_component_batch(
    jewelry_type: str = "ring",
    components_str: str = "shank,setting,gem",
    count: int = 20,
    out_dir: str = "out/batch/"
):
    os.makedirs(out_dir, exist_ok=True)
    conn = init_db("out/designs.db")
    cursor = conn.cursor()
    catalog = load_catalog_index()

    component_slots = [c.strip() for c in components_str.split(",") if c.strip()]

    attempted = 0
    passed = 0
    unique_kept = 0

    metals = ["yellow_gold", "white_gold", "rose_gold", "platinum"]
    stone_types = ["diamond", "sapphire", "emerald"]

    for i in range(count):
        attempted += 1
        seed = random.randint(0, 999999)
        rng = random.Random(seed)

        picked_parts = {}
        gems_picked = []
        settings_picked = []
        shanks_picked = []

        for slot in component_slots:
            if slot not in catalog:
                slot_key = "setting" if slot == "collet" else slot
            else:
                slot_key = slot
            
            entry = rng.choice(catalog[slot_key])
            if slot_key == "shank":
                shanks_picked.append(entry)
            elif slot_key == "setting":
                settings_picked.append(entry)
            elif slot_key == "gem":
                d_min, d_max = entry["diameter_range"]
                sampled_diam = round(rng.uniform(d_min, d_max), 1)
                gem_info = {
                    "entry": entry,
                    "diameter_mm": sampled_diam,
                    "type": rng.choice(stone_types)
                }
                gems_picked.append(gem_info)

        # Default fallback if slots were empty
        shank_entry = shanks_picked[0] if shanks_picked else catalog["shank"][0]
        setting_entry = settings_picked[0] if settings_picked else catalog["setting"][0]
        center_gem = gems_picked[0] if gems_picked else {"diameter_mm": 6.5, "type": "diamond"}

        shank_style = shank_entry.get("style", "simple")
        setting_style = setting_entry.get("style", "prong")
        prongs = setting_entry.get("prongs", 4)
        center_diam = center_gem["diameter_mm"]
        gem_type = center_gem["type"]
        metal = rng.choice(metals)
        metal_text = metal.replace("_", " ")

        # Build prompt string from picked parts and slots
        gem_count = len(gems_picked)
        setting_count = len(settings_picked)

        if gem_count == 1:
            prompt = f"{shank_style} {setting_style} ring with {center_diam}mm {gem_type}, {prongs} prongs, {metal_text}, size 7"
        elif gem_count == 2 and setting_count < 2:
            side_diam = gems_picked[1]["diameter_mm"]
            side_type = gems_picked[1]["type"]
            prompt = f"{shank_style} two stone ring with {center_diam}mm {gem_type} and {side_diam}mm {side_type}, {metal_text}, size 7"
        elif (gem_count == 2 and setting_count >= 2) or gem_count >= 3:
            # Trilogy ring
            prompt = f"{shank_style} trilogy ring with {center_diam}mm {gem_type} and side stones, {setting_style} setting, {metal_text}, size 7"
        else:
            prompt = f"{shank_style} ring with {center_diam}mm {gem_type}, {setting_style} setting, {metal_text}, size 7"

        dir_idx = attempted
        while os.path.exists(os.path.join(out_dir, f"design_{dir_idx:03d}")):
            dir_idx += 1
        candidate_dir = os.path.join(out_dir, f"design_{dir_idx:03d}")

        try:
            report = run_pipeline(prompt, seed=seed, out_dir=candidate_dir, exit_on_fail=False)
            if not report.get("pass", False):
                failed_checks = [k for k, v in report.get("checks", {}).items() if not v]
                print(f"[{attempted}/{count}] GATEKEEPER FAIL: {failed_checks}")
                shutil.rmtree(candidate_dir, ignore_errors=True)
                continue
        except Exception as e:
            print(f"[{attempted}/{count}] ERROR running pipeline: {e}")
            shutil.rmtree(candidate_dir, ignore_errors=True)
            continue

        passed += 1

        # Compute param hash
        hash_input = f"{jewelry_type}_{components_str}_{round(center_diam, 1)}_{prongs}_{metal}_{shank_style}_{setting_style}"
        key = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        # Check SQLite deduplication
        cursor.execute("SELECT hash FROM designs WHERE hash = ?", (key,))
        row = cursor.fetchone()
        if row:
            print(f"[{attempted}/{count}] DUPLICATE hash={key} — skipping")
            shutil.rmtree(candidate_dir, ignore_errors=True)
            continue

        now_ts = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO designs (hash, seed, out_dir, timestamp) VALUES (?, ?, ?, ?)",
            (key, seed, candidate_dir, now_ts)
        )
        conn.commit()
        unique_kept += 1
        print(f"[{attempted}/{count}] KEPT: hash={key} seed={seed} dir={candidate_dir}")

    conn.close()

    summary_line = f"{attempted} attempted, {passed} passed gatekeeper, {unique_kept} unique kept"
    print("\n" + "=" * 50)
    print(summary_line)
    print("=" * 50)
    return summary_line

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Component-driven jewelry batch generator")
    parser.add_argument("--type", type=str, default="ring", help="Jewelry type")
    parser.add_argument("--components", type=str, default="shank,setting,gem", help="Comma-separated component slots")
    parser.add_argument("--count", type=int, default=20, help="Number of designs to attempt")
    parser.add_argument("--out", type=str, default="out/batch/", help="Output folder")

    args = parser.parse_args()
    generate_component_batch(
        jewelry_type=args.type,
        components_str=args.components,
        count=args.count,
        out_dir=args.out
    )
