import os
import subprocess

def render_assembly(metal_path, gem_path, remote_host="ubuntu@192.168.0.134"):
    print("Preparing render job...")
    # SCP files
    subprocess.run(["scp", metal_path, f"{remote_host}:~/metal.obj"], check=True)
    subprocess.run(["scp", gem_path, f"{remote_host}:~/gem.obj"], check=True)
    subprocess.run(["scp", "jobs/render_script.py", f"{remote_host}:~/render_script.py"], check=True)
    
    # Run blender
    print("Executing remote render...")
    subprocess.run([
        "ssh", remote_host, 
        "mkdir -p ~/render_out && blender -b -P ~/render_script.py -- ~/metal.obj ~/gem.obj ~/render_out/"
    ], check=True)
    
    # Retrieve PNGs
    print("Retrieving frames...")
    os.makedirs("jobs/output/render", exist_ok=True)
    subprocess.run(["scp", f"{remote_host}:~/render_out/frame_*.png", "jobs/output/render/"], check=True)
    
    # Optional: Compile to mp4 via ffmpeg
    print("Compiling to MP4...")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", "30", "-pattern_type", "glob", "-i", "jobs/output/render/frame_*.png", 
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "jobs/output/turntable.mp4"
    ])
    print("Render complete: jobs/output/turntable.mp4")

if __name__ == "__main__":
    # Test render
    render_assembly("jobs/output/metal.obj", "catalog/meshes/gem_round_01.obj")
