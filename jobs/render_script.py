import bpy
import math
import sys
import os

# Args: metal_path gem_path out_dir
argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
else:
    args = ["metal.obj", "gem.obj", "./"]

metal_path, gem_path, out_dir = args[0], args[1], args[2]

# Setup CYCLES
bpy.context.scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
for dev in prefs.devices:
    dev.use = (dev.type == 'CUDA' and 'M4000' in dev.name)

bpy.context.scene.cycles.device = 'GPU'
bpy.context.scene.cycles.samples = 128
bpy.context.scene.cycles.use_denoising = True
bpy.context.scene.cycles.denoiser = 'OPENIMAGEDENOISE'

# Light paths
bpy.context.scene.cycles.max_bounces = 32
bpy.context.scene.cycles.transmission_bounces = 32
bpy.context.scene.cycles.transparent_max_bounces = 32

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Import meshes
bpy.ops.wm.obj_import(filepath=metal_path)
metal_obj = bpy.context.selected_objects[0]
bpy.ops.wm.obj_import(filepath=gem_path)
gem_obj = bpy.context.selected_objects[0]

# Metal Material
mat_gold = bpy.data.materials.new(name="Gold")
mat_gold.use_nodes = True
bsdf = mat_gold.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.8, 0.3, 1)
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.08
if metal_obj.data.materials:
    metal_obj.data.materials[0] = mat_gold
else:
    metal_obj.data.materials.append(mat_gold)
bpy.ops.object.shade_smooth()

# Gem Material (Shadow ray trick)
mat_gem = bpy.data.materials.new(name="Diamond")
mat_gem.use_nodes = True
nodes = mat_gem.node_tree.nodes
links = mat_gem.node_tree.links
for n in nodes: nodes.remove(n)

out_node = nodes.new(type='ShaderNodeOutputMaterial')
mix_node = nodes.new(type='ShaderNodeMixShader')
glass_node = nodes.new(type='ShaderNodeBsdfGlass')
transp_node = nodes.new(type='ShaderNodeBsdfTransparent')
light_path = nodes.new(type='ShaderNodeLightPath')

glass_node.inputs['IOR'].default_value = 2.418
glass_node.inputs['Roughness'].default_value = 0.0

links.new(light_path.outputs['Is Shadow Ray'], mix_node.inputs['Fac'])
links.new(glass_node.outputs['BSDF'], mix_node.inputs[1])
links.new(transp_node.outputs['BSDF'], mix_node.inputs[2])
links.new(mix_node.outputs['Shader'], out_node.inputs['Surface'])

if gem_obj.data.materials:
    gem_obj.data.materials[0] = mat_gem
else:
    gem_obj.data.materials.append(mat_gem)
    
# Apply Shade Smooth to gem (optional, but good for facets? No, diamonds are flat faceted!)
bpy.context.view_layer.objects.active = gem_obj
bpy.ops.object.shade_flat()

# Lighting (Procedural Studio)
world = bpy.data.worlds['World']
world.use_nodes = True
bg_node = world.node_tree.nodes["Background"]
bg_node.inputs['Color'].default_value = (0.05, 0.05, 0.05, 1) # Dark studio
bg_node.inputs['Strength'].default_value = 1.0

# Add 3-point lights
light_data1 = bpy.data.lights.new(name="Key", type='AREA')
light_data1.energy = 2000
light_data1.size = 5.0
light_obj1 = bpy.data.objects.new(name="KeyLight", object_data=light_data1)
bpy.context.collection.objects.link(light_obj1)
light_obj1.location = (10, -10, 10)
light_obj1.rotation_euler = (math.radians(45), 0, math.radians(45))

# Camera
cam_data = bpy.data.cameras.new(name="Camera")
cam_data.lens = 85 # telephoto for jewelry
cam_obj = bpy.data.objects.new(name="Camera", object_data=cam_data)
bpy.context.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Turntable setup
empty = bpy.data.objects.new("Target", None)
bpy.context.collection.objects.link(empty)

cam_obj.parent = empty
cam_obj.location = (0, -25, 10)
cam_obj.rotation_euler = (math.radians(70), 0, 0)

empty.rotation_euler = (0, 0, 0)
empty.keyframe_insert(data_path="rotation_euler", frame=1)
empty.rotation_euler = (0, 0, math.radians(360))
empty.keyframe_insert(data_path="rotation_euler", frame=60)

for fc in empty.animation_data.action.fcurves:
    for kf in fc.keyframe_points:
        kf.interpolation = 'LINEAR'

# Output settings
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 60
bpy.context.scene.render.filepath = os.path.join(out_dir, "frame_")
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Render animation
bpy.ops.render.render(animation=True)
