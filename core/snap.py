import numpy as np
from core.frames import build_socket_frame

def snap_part(parent_socket, child_socket, parent_transform, spin_deg=0.0):
    """
    Returns the world transform of a child part snapped to a parent part.
    
    T_W_B = T_W_A @ T_S_A @ R_theta @ R_flip @ T_S_B_inv
    """
    T_W_A = np.asarray(parent_transform, dtype=float)
    
    T_S_A = build_socket_frame(
        origin=parent_socket['origin'],
        axis=parent_socket['axis'],
        ref=parent_socket['ref']
    )
    
    if 'embed_mm' in parent_socket:
        embed = parent_socket['embed_mm']
        T_S_A[0:3, 3] -= T_S_A[0:3, 2] * embed
    
    T_S_B = build_socket_frame(
        origin=child_socket['origin'],
        axis=child_socket['axis'],
        ref=child_socket['ref']
    )
    
    if 'embed_mm' in child_socket:
        embed = child_socket['embed_mm']
        T_S_B[0:3, 3] -= T_S_B[0:3, 2] * embed
    
    # Assert spin is multiple of step_deg if defined
    if 'spin' in parent_socket and 'step_deg' in parent_socket['spin']:
        step = parent_socket['spin']['step_deg']
        # Handle floating point mod accurately
        mod_val = spin_deg % step
        if not np.isclose(mod_val, 0, atol=1e-5) and not np.isclose(mod_val, step, atol=1e-5):
            raise ValueError(f"spin_deg {spin_deg} is not a multiple of step_deg {step}")
            
    # R_theta (rotation about Z)
    theta = np.radians(spin_deg)
    c, s = np.cos(theta), np.sin(theta)
    R_theta = np.array([
        [c, -s, 0, 0],
        [s,  c, 0, 0],
        [0,  0, 1, 0],
        [0,  0, 0, 1]
    ], dtype=float)
    
    # R_flip (180 around X to make axes face each other)
    R_flip = np.array([
        [1,  0,  0, 0],
        [0, -1,  0, 0],
        [0,  0, -1, 0],
        [0,  0,  0, 1]
    ], dtype=float)
    
    T_S_B_inv = np.linalg.inv(T_S_B)
    
    T_W_B = T_W_A @ T_S_A @ R_theta @ R_flip @ T_S_B_inv
    
    # Asserts
    if not np.isclose(np.linalg.det(T_W_B[:3, :3]), 1.0, atol=1e-5):
        raise ValueError("Determinant of snapped frame is not +1")
        
    # Check antiparallel axes
    parent_axis_world = (T_W_A @ T_S_A)[0:3, 2]
    child_axis_world = (T_W_B @ T_S_B)[0:3, 2]
    
    if not np.isclose(np.dot(parent_axis_world, child_axis_world), -1.0, atol=1e-5):
        raise ValueError("Mated axes are not antiparallel")
        
    # Assert socket origins coincide within 0.1mm (ponytail: parts actually touching)
    p_orig_w = (T_W_A @ T_S_A)[0:3, 3]
    c_orig_w = (T_W_B @ T_S_B)[0:3, 3]
    origin_dist = float(np.linalg.norm(p_orig_w - c_orig_w))
    if origin_dist > 0.1:
        raise ValueError(f"Socket origins not touching: dist={origin_dist:.4f}mm exceeds 0.1mm tolerance")
        
    return T_W_B
