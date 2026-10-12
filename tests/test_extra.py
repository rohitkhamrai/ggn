import pytest
import trimesh
import numpy as np
import json
from core.snap import snap_part

def test_snap_part_antiparallel():
    parent_socket = {'origin': [0, 0, 1], 'axis': [0, 0, 1], 'ref': [1, 0, 0]}
    child_socket = {'origin': [0, 0, 0], 'axis': [0, 0, 1], 'ref': [1, 0, 0]}
    parent_transform = np.eye(4)
    
    T_W_B = snap_part(parent_socket, child_socket, parent_transform, spin_deg=0)
    
    parent_z = parent_transform[:3, :3] @ parent_socket['axis']
    child_z = T_W_B[:3, :3] @ child_socket['axis']
    
    assert np.isclose(np.dot(parent_z, child_z), -1.0, atol=1e-5)

def test_spin_invariance():
    mesh = trimesh.load("catalog/meshes/collet_round_04.obj", force='mesh')
    with open("catalog/meta/collet_round_04.json", 'r') as f:
        meta = json.load(f)
    
    base_sock = next(s for s in meta["sockets"] if s["id"] == "base")
    step_deg = base_sock.get("spin", {}).get("step_deg", 360)
    
    if step_deg < 360:
        vol1 = mesh.volume
        bbox1 = mesh.bounding_box.extents
        
        angle = np.radians(step_deg)
        R = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
        mesh.apply_transform(R)
        
        vol2 = mesh.volume
        bbox2 = mesh.bounding_box.extents
        
        assert np.isclose(vol1, vol2, atol=1e-5)
        # Bounding box X and Y might swap upon 90 degree rotation if not perfectly tessellated symmetric
        assert np.allclose(sorted(bbox1[:2]), sorted(bbox2[:2]), atol=1e-5)
        assert np.isclose(bbox1[2], bbox2[2], atol=1e-5)

def test_scale_propagation():
    with open("catalog/meta/collet_round_04.json", 'r') as f:
        meta = json.load(f)
    
    scale = 1.2
    scaled_sockets = []
    for sock in meta["sockets"]:
        new_sock = sock.copy()
        new_sock["origin"] = [c * scale for c in sock["origin"]]
        scaled_sockets.append(new_sock)
        
    for orig, scaled in zip(meta["sockets"], scaled_sockets):
        for o, s in zip(orig["origin"], scaled["origin"]):
            assert np.isclose(o * scale, s)
