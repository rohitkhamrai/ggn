import pytest
import trimesh
from geometry.casting_checks import check_single_component, check_min_wall, check_prong_diameter
from geometry.clearance import check_gem_clearance_boolean, check_gem_support

def test_two_disconnected_parts():
    mesh1 = trimesh.creation.box(extents=[1,1,1])
    mesh2 = trimesh.creation.box(extents=[1,1,1])
    mesh2.apply_translation([5,0,0])
    combined = mesh1 + mesh2
    assert not check_single_component(combined)

def test_crushed_prongs():
    gem = trimesh.creation.box(extents=[2,2,2])
    metal = trimesh.creation.box(extents=[1.5,1.5,1.5])
    # Overlap heavily
    assert not check_gem_clearance_boolean(gem, metal)

def test_floating_gem():
    gem = trimesh.creation.box(extents=[1,1,1])
    metal = trimesh.creation.box(extents=[1,1,1])
    gem.apply_translation([0, 0, 5])
    # Distance is 4
    assert not check_gem_support(gem, metal)

def test_min_wall_and_prong():
    # Thick ring: diameter 18-20, height 2 -> walls are 2.0 thick
    ring = trimesh.creation.box(extents=[10, 10, 2])
    # Thin prong: radius 0.1 -> diameter 0.2
    prong = trimesh.creation.cylinder(radius=0.1, height=2)
    prong.apply_translation([5, 0, 1])
    mesh = ring + prong
    
    # Must fail because prong thickness 0.2 < 0.3
    assert not check_min_wall(mesh, 0.3)
    assert not check_prong_diameter(mesh, 0.5)
