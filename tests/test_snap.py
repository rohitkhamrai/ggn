import pytest
import numpy as np
from core.snap import snap_part

def test_snap_part_basic():
    parent_socket = {'origin': [0, 0, 1], 'axis': [0, 0, 1], 'ref': [1, 0, 0]}
    child_socket = {'origin': [0, 0, 0], 'axis': [0, 0, 1], 'ref': [1, 0, 0]}
    parent_transform = np.eye(4)
    
    T_W_B = snap_part(parent_socket, child_socket, parent_transform, spin_deg=0)
    
    assert np.allclose(T_W_B[0:3, 3], [0, 0, 1], atol=1e-5)
    assert np.isclose(np.linalg.det(T_W_B[:3, :3]), 1.0, atol=1e-5)

def test_snap_part_spin_step_fails():
    parent_socket = {'origin': [0, 0, 1], 'axis': [0, 0, 1], 'ref': [1, 0, 0], 'spin': {'step_deg': 90}}
    child_socket = {'origin': [0, 0, 0], 'axis': [0, 0, 1], 'ref': [1, 0, 0]}
    parent_transform = np.eye(4)
    
    with pytest.raises(ValueError, match="multiple of step_deg"):
        snap_part(parent_socket, child_socket, parent_transform, spin_deg=45)

def test_snap_part_spin_step_passes():
    parent_socket = {'origin': [0, 0, 1], 'axis': [0, 0, 1], 'ref': [1, 0, 0], 'spin': {'step_deg': 90}}
    child_socket = {'origin': [0, 0, 0], 'axis': [0, 0, 1], 'ref': [1, 0, 0]}
    parent_transform = np.eye(4)
    
    T_W_B = snap_part(parent_socket, child_socket, parent_transform, spin_deg=90)
    assert np.isclose(np.linalg.det(T_W_B[:3, :3]), 1.0, atol=1e-5)

def test_snap_part_spin_step_negative():
    parent_socket = {'origin': [0, 0, 1], 'axis': [0, 0, 1], 'ref': [1, 0, 0], 'spin': {'step_deg': 90}}
    child_socket = {'origin': [0, 0, 0], 'axis': [0, 0, 1], 'ref': [1, 0, 0]}
    parent_transform = np.eye(4)
    
    T_W_B = snap_part(parent_socket, child_socket, parent_transform, spin_deg=-90)
    assert np.isclose(np.linalg.det(T_W_B[:3, :3]), 1.0, atol=1e-5)
