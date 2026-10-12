import pytest
import trimesh
import numpy as np
from geometry.clearance import check_gem_clearance_boolean
from geometry.casting_checks import check_watertight, check_positive_volume, check_single_component

def test_check_gem_clearance():
    gem = trimesh.creation.box(extents=[1, 1, 1])
    metal = trimesh.creation.box(extents=[1, 1, 1])
    
    # Overlapping
    assert not check_gem_clearance_boolean(gem, metal)
    
    # Not overlapping
    metal.apply_translation([2, 0, 0])
    assert check_gem_clearance_boolean(gem, metal)

def test_casting_checks():
    metal = trimesh.creation.box(extents=[1, 1, 1])
    assert check_watertight(metal)
    assert check_positive_volume(metal)
    assert check_single_component(metal)
