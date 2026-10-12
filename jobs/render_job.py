import bpy
import sys
import os
import math

# Args: metal_path gem_path output_dir
argv = sys.argv
if "--" not in argv:
    print("Error: -- missing")
    sys.exit(1)
args = argv[argv.index("--") + 1:]
metal_path = args[0]
gem_path = args[1]
output_dir = args[2]

has_gem = (gem_path != "NONE")

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Render engine + CUDA
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
prefs.get_devices()
for d in prefs.devices:
    d.use = (d.type == 'CUDA' and 'M4000' in d.name)

# Light paths
scene.cycles.transparent_max_bounces = 24
scene.cycles.transmission_bounces = 24
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 6
scene.cycles.sample_clamp_direct = 10
scene.cycles.sample_clamp_indirect = 4
scene.cycles.caustics_refractive = True
scene.cycles.caustics_reflective = True

# Adaptive sampling
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.01
scene.cycles.samples = 512

# Output
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(output_dir, "frame.png")

# Get objects by import order, not name
before = set(bpy.data.objects.keys())
bpy.ops.wm.obj_import(filepath=metal_path)
metal_obj = [o for o in bpy.data.objects if o.name not in before and o.type == 'MESH'][0]

before = set(bpy.data.objects.keys())
gem_obj = None
if has_gem:
    bpy.ops.wm.obj_import(filepath=gem_path)
    gem_obj = [o for o in bpy.data.objects if o.name not in before and o.type == 'MESH'][0]

# Units and camera scale
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001
max_dim = max(metal_obj.dimensions)
print("MAX_DIM:", max_dim)

if has_gem:
    # Gem material — Glass BSDF, blue sapphire, transparent on shadow rays
    mat = bpy.data.materials.new("Gem")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output_node = nodes.new('ShaderNodeOutputMaterial')
    glass = nodes.new('ShaderNodeBsdfGlass')
    glass.inputs['IOR'].default_value = 2.42
    glass.inputs['Color'].default_value = (0.1, 0.6, 0.9, 1.0)
    glass.inputs['Roughness'].default_value = 0.02
    links.new(glass.outputs['BSDF'], output_node.inputs['Surface'])
    gem_obj.data.materials.clear()
    gem_obj.data.materials.append(mat)

# Metal material — gold PBR
metal_mat = bpy.data.materials.new("Metal")
metal_mat.use_nodes = True
bsdf = metal_mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs['Base Color'].default_value = (1.0, 0.8, 0.4, 1.0)
if 'Metallic' in bsdf.inputs:
    bsdf.inputs['Metallic'].default_value = 1.0
if 'Roughness' in bsdf.inputs:
    bsdf.inputs['Roughness'].default_value = 0.15
metal_obj.data.materials.clear()
metal_obj.data.materials.append(metal_mat)

# Smooth shading
objs_to_smooth = [metal_obj]
if has_gem: objs_to_smooth.append(gem_obj)
for obj in objs_to_smooth:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

# HDRI lighting
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
wn = world.node_tree
wn.nodes.clear()
env = wn.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load("/home/ubuntu/studio_small_09_2k.exr")
bg = wn.nodes.new("ShaderNodeBackground")
wout = wn.nodes.new("ShaderNodeOutputWorld")
wn.links.new(env.outputs['Color'], bg.inputs['Color'])
wn.links.new(bg.outputs['Background'], wout.inputs['Surface'])

# Camera
cam_data = bpy.data.cameras.new('Camera')
cam = bpy.data.objects.new('Camera', cam_data)
bpy.context.collection.objects.link(cam)
scene.camera = cam
cam.location = (0, -max_dim * 4, max_dim * 1.2)

empty = bpy.data.objects.new("Empty", None)
empty.location = (0, 0, max_dim * 0.5)
bpy.context.collection.objects.link(empty)

tt = cam.constraints.new(type='TRACK_TO')
tt.target = empty
tt.track_axis = 'TRACK_NEGATIVE_Z'
tt.up_axis = 'UP_Y'

# Render single still
scene.frame_current = 1
bpy.ops.render.render(write_still=True)
