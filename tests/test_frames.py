import pytest
import numpy as np
from core.units import assert_mm
from core.frames import build_socket_frame

def test_assert_mm():
    assert_mm("mm")
    assert_mm("MM")
    with pytest.raises(ValueError):
        assert_mm("cm")

def test_build_socket_frame_valid():
    frame = build_socket_frame([1, 2, 3], [0, 0, 1], [1, 0, 0])
    assert np.allclose(frame, [
        [1, 0, 0, 1],
        [0, 1, 0, 2],
        [0, 0, 1, 3],
        [0, 0, 0, 1]
    ], atol=1e-5)
    assert np.isclose(np.linalg.det(frame[:3, :3]), 1.0, atol=1e-5)

def test_build_socket_frame_normalize():
    frame = build_socket_frame([0, 0, 0], [0, 0, 2], [2, 0, 0])
    assert np.allclose(frame[:3, :3], np.eye(3), atol=1e-5)

def test_build_socket_frame_parallel_fails():
    with pytest.raises(ValueError):
        build_socket_frame([0, 0, 0], [0, 0, 1], [0, 0, -1])

def test_build_socket_frame_non_orthogonal_ref():
    frame = build_socket_frame([0, 0, 0], [0, 0, 1], [1, 0, 1])
    assert np.allclose(frame[:3, :3], np.eye(3), atol=1e-5)
