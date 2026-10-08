import subprocess
import sys

def robust_union(path_a, path_b, out_path, timeout=10):
    try:
        subprocess.run(
            [sys.executable, "-m", "geometry.union", path_a, path_b, out_path],
            check=True, timeout=timeout
        )
        return True
    except subprocess.TimeoutExpired:
        print("Union timed out")
        return False
    except subprocess.CalledProcessError:
        print("Union crashed")
        return False
