import pytest
from catalog.compiler import compile_spec

def test_compiler_sapphire_halo_ring():
    spec = compile_spec("sapphire halo ring size 7")
    assert spec["type"] == "ring"
    assert spec["inner_diameter_mm"] == 17.3
    assert 5.5 <= spec["center_stone"]["diameter_mm"] <= 7.5
    assert spec["center_stone"]["type"] == "sapphire"
    assert spec["setting"] == "halo"

def test_compiler_cathedral_pave():
    spec = compile_spec("cathedral pave ring with 6.5mm diamond center size 6")
    assert spec["inner_diameter_mm"] == 16.5
    assert spec["center_stone"]["diameter_mm"] == 6.5
    assert spec["shank"] == "cathedral_pave"
