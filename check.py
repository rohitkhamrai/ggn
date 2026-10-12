import bpy
print([attr for attr in dir(bpy.context.scene) if 'node' in attr])
