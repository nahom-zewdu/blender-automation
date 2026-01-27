import bpy

values = [1, 2, 3, 2.5]

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bars = []
for i, v in enumerate(values):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 1.5, 0, 0))
    bar = bpy.context.object
    bar.scale.z = 0.01
    bar.keyframe_insert(data_path="scale", frame=1)

    bar.scale.z = v
    bar.keyframe_insert(data_path="scale", frame=60)
    bars.append(bar)

# Camera
bpy.ops.object.camera_add(location=(2, -8, 6))
camera = bpy.context.object
camera.rotation_euler = (1.1, 0, 0)
bpy.context.scene.camera = camera

# Light
bpy.ops.object.light_add(type='POINT', location=(2, -4, 6))

# Render
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.frame_end = 60
scene.render.filepath = '/tmp/step4.mp4'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'

bpy.ops.render.render(animation=True)
