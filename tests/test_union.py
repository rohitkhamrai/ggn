import pytest
import trimesh
import os
from geometry.union_wrapper import robust_union

def test_robust_union(tmp_path):
    a = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    b = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    b.apply_translation([0.5, 0, 0])
    
    path_a = tmp_path / "a.obj"
    path_b = tmp_path / "b.obj"
    out_path = tmp_path / "out.obj"
    
    a.export(path_a)
    b.export(path_b)
    
    success = robust_union(str(path_a), str(path_b), str(out_path))
    assert success
    
    res = trimesh.load(out_path, force='mesh')
    assert abs(res.volume - 1.5) < 1e-4
