import bpy
import time

bpy.context.scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'

print("Detecting devices...")
prefs.get_devices()

for dev in prefs.devices:
    if dev.type == 'CUDA':
        print(f"Enabling CUDA device: {dev.name}")
        dev.use = True
    else:
        dev.use = False

bpy.context.scene.cycles.device = 'GPU'
bpy.context.scene.cycles.samples = 64

print(f"Blender version: {bpy.app.version_string}")
print("Rendering test...")
start_t = time.time()
bpy.ops.render.render(write_still=False)
print(f"Render complete in {time.time() - start_t:.2f} seconds!")
