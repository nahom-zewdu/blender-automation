# blender/step2_animation.py

import bpy
from mathutils import Vector

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Create cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object

# Create camera
bpy.ops.object.camera_add(location=(6, -6, 4))
camera = bpy.context.object
camera.rotation_euler = (1.1, 0, 0.8)
bpy.context.scene.camera = camera

# Create light
bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
light = bpy.context.object
light.data.energy = 1000

# Timeline
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 150
scene.render.fps = 30

# Animate cube rotation
cube.rotation_euler = (0, 0, 0)
cube.keyframe_insert(data_path="rotation_euler", frame=1)

cube.rotation_euler = (0, 0, 6.28)
cube.keyframe_insert(data_path="rotation_euler", frame=150)

# Render settings
scene.render.engine = 'BLENDER_EEVEE'
scene.render.filepath = "/tmp/test.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'

# Render
bpy.ops.render.render(animation=True)
