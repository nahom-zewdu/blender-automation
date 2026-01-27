import bpy

def create_box(name, location):
    bpy.ops.mesh.primitive_cube_add(size=1.5, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Boxes
api = create_box("API", (-3, 0, 0))
worker = create_box("Worker", (0, 0, 0))
db = create_box("DB", (3, 0, 0))

# Animate appearance
for i, obj in enumerate([api, worker, db]):
    obj.scale = (0, 0, 0)
    obj.keyframe_insert(data_path="scale", frame=1 + i * 20)
    obj.scale = (1, 1, 1)
    obj.keyframe_insert(data_path="scale", frame=20 + i * 20)

# Camera
bpy.ops.object.camera_add(location=(0, -8, 4))
camera = bpy.context.object
camera.rotation_euler = (1.1, 0, 0)
bpy.context.scene.camera = camera

# Light
bpy.ops.object.light_add(type='AREA', location=(0, -4, 6))

# Render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.frame_end = 80
scene.render.filepath = '/tmp/step3.mp4'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'

bpy.ops.render.render(animation=True)
