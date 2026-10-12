import pytest
from core.solver import solve_assembly_scales

def test_solve_assembly_scales():
    assembly_def = [
        {"id": "node_gem", "part_id": "gem_round_01", "scale": 1.0, "parent": "node_collet", "socket_pair": ("girdle", "seat")},
        {"id": "node_collet", "part_id": "collet_round_04", "scale": 1.0, "parent": None, "socket_pair": None},
    ]
    
    res = solve_assembly_scales(assembly_def, compat_path="catalog/compat.json", catalog_meta_dir="catalog/meta")
    collet = next(n for n in res if n["id"] == "node_collet")
    assert collet["scale"] == 1.0
