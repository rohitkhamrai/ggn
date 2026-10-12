import numpy as np

def build_socket_frame(origin, axis, ref):
    """
    Builds a 4x4 orthonormal transformation matrix for a socket.
    axis: points outward from the part surface (Z)
    ref: reference direction (X)
    Y = Z x X
    """
    origin = np.asarray(origin, dtype=float)
    Z = np.asarray(axis, dtype=float)
    X = np.asarray(ref, dtype=float)
    
    # Normalize Z
    norm_Z = np.linalg.norm(Z)
    if norm_Z < 1e-8:
        raise ValueError("Axis vector is zero.")
    Z = Z / norm_Z
    
    norm_X_initial = np.linalg.norm(X)
    if norm_X_initial < 1e-8:
        raise ValueError("Reference vector is zero.")
        
    # Assert X and Z are not parallel
    if abs(np.dot(Z, X / norm_X_initial)) > 1 - 1e-5:
        raise ValueError("Reference vector cannot be parallel to axis.")
        
    # Project X onto the plane normal to Z and normalize
    X = X - np.dot(X, Z) * Z
    norm_X = np.linalg.norm(X)
    X = X / norm_X
    
    # Cross product for Y (right-handed)
    Y = np.cross(Z, X)
    
    frame = np.eye(4)
    frame[0:3, 0] = X
    frame[0:3, 1] = Y
    frame[0:3, 2] = Z
    frame[0:3, 3] = origin
    
    # Assert determinant is +1 (tolerance 1e-5)
    det = np.linalg.det(frame[:3, :3])
    if not np.isclose(det, 1.0, atol=1e-5):
        raise ValueError(f"Determinant must be +1, got {det}")
        
    return frame
