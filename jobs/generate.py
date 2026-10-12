import os
import sys
import argparse
import random
import hashlib
import sqlite3
import shutil
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

def map_template(jewelry_type: str, n_components: int) -> str:
    if jewelry_type.lower() == "bracelet":
        return "bracelet"
    if n_components == 1:
        return "solitaire"
    elif 3 <= n_components <= 5:
        return "halo"
    elif 6 <= n_components <= 10:
        return "halo + pave shoulder"
    elif 11 <= n_components <= 20:
        return "full pave eternity band"
    else:
        return "halo"

def generate_batch(jewelry_type: str = "ring", n_components: int = 7, count: int = 20, out_dir: str = "out/batch/"):
    os.makedirs(out_dir, exist_ok=True)
    conn = init_db("out/designs.db")
    cursor = conn.cursor()

    template = map_template(jewelry_type, n_components)

    attempted = 0
    passed = 0
    unique_kept = 0

    stone_types = ["diamond", "sapphire", "emerald"]
    metals = ["yellow_gold", "white_gold", "rose_gold", "platinum"]
    prong_counts = [4, 6]
    shank_styles = ["simple", "cathedral", "pave"]

    diameters = [5.0, 5.5, 6.0, 6.5, 7.0, 7.5]

    for i in range(count):
        attempted += 1
        seed = random.randint(0, 999999)

        stone_type = random.choice(stone_types)
        metal = random.choice(metals)
        diam = random.choice(diameters)
        prong = random.choice(prong_counts)
        style = random.choice(shank_styles)

        metal_text = metal.replace("_", " ")
        prompt = f"{template} ring, {diam}mm {stone_type}, {prong} prongs, {metal_text}, {style} shank, size 7"

        candidate_dir = os.path.join(out_dir, f"design_{attempted:03d}")

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
        hash_input = f"{jewelry_type}_{n_components}_{round(diam, 1)}_{prong}_{metal}_{style}"
        key = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        # Check SQLite deduplication
        cursor.execute("SELECT hash FROM designs WHERE hash = ?", (key,))
        row = cursor.fetchone()
        if row:
            print(f"[{attempted}/{count}] DUPLICATE hash={key} — skipping")
            shutil.rmtree(candidate_dir, ignore_errors=True)
            continue

        # Insert and keep
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
    parser = argparse.ArgumentParser(description="Generative jewelry batch loop")
    parser.add_argument("--type", type=str, default="ring", help="Jewelry type")
    parser.add_argument("--n-components", type=int, default=7, help="Component count")
    parser.add_argument("--count", type=int, default=20, help="Number of designs to attempt")
    parser.add_argument("--out", type=str, default="out/batch/", help="Output folder")

    args = parser.parse_args()
    generate_batch(jewelry_type=args.type, n_components=args.n_components, count=args.count, out_dir=args.out)
