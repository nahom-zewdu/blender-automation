# blender/step2_animation.py

import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object

# Animate rotation
cube.rotation_mode = 'XYZ'
cube.rotation_euler = (0, 0, 0)
cube.keyframe_insert(data_path="rotation_euler", frame=1)

cube.rotation_euler = (0, 0, 3.14)
cube.keyframe_insert(data_path="rotation_euler", frame=120)

# Camera
bpy.ops.object.camera_add(location=(6, -6, 4))
bpy.context.scene.camera = bpy.context.object

# Light
bpy.ops.object.light_add(type='POINT', location=(4, -4, 6))

# Render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.frame_start = 1
scene.frame_end = 120
scene.render.filepath = '/tmp/step2.mp4'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'

bpy.ops.render.render(animation=True)
