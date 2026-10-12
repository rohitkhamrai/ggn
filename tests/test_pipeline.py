import os
import json
import pytest
import trimesh
import numpy as np
from jobs.pipeline import run_pipeline

def test_pipeline_round_solitaire(tmp_path):
    out_dir = str(tmp_path / "test_run")
    user_text = "round diamond solitaire size 6"
    seed = 0

    report = run_pipeline(user_text=user_text, seed=seed, out_dir=out_dir)

    assert report["pass"] is True
    assert all(report["checks"].values())

    # Check report.json written
    report_file = os.path.join(out_dir, "report.json")
    assert os.path.exists(report_file)
    with open(report_file, "r") as f:
        loaded_report = json.load(f)
    assert loaded_report["pass"] is True

    # Check metal.stl exists and is watertight
    metal_file = os.path.join(out_dir, "metal.stl")
    assert os.path.exists(metal_file)
    metal_mesh = trimesh.load(metal_file)
    assert metal_mesh.is_watertight is True
    assert metal_mesh.volume > 0

    # Check gems
    gems_dir = os.path.join(out_dir, "gems")
    assert os.path.exists(gems_dir)
    gem_files = [os.path.join(gems_dir, f) for f in os.listdir(gems_dir) if f.endswith(".stl")]
    assert len(gem_files) > 0

    # Assert no gem intersects metal mesh
    for gem_f in gem_files:
        gem_mesh = trimesh.load(gem_f)
        from geometry.clearance import check_gem_clearance_boolean
        assert check_gem_clearance_boolean(gem_mesh, metal_mesh) is True
