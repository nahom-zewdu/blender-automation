# blender/step1_still.py

import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Add cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))

# Camera
bpy.ops.object.camera_add(location=(6, -6, 4))
camera = bpy.context.object
camera.rotation_euler = (1.1, 0, 0.8)
bpy.context.scene.camera = camera

# Light
bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))

# Render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.filepath = '/tmp/step1.png'
scene.render.resolution_x = 800
scene.render.resolution_y = 600

bpy.ops.render.render(write_still=True)
