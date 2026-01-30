""" Blender script to animate a character walking to a car,
set up camera and lighting, and render the animation to a video file."""
import bpy
from mathutils import Vector


# GET OBJECTS
char = bpy.data.objects["Character"]
car = bpy.data.objects["Car"]

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120

# CLEAN CAMERA & LIGHTS
for obj in list(bpy.data.objects):
    if obj.type in {"CAMERA", "LIGHT"}:
        bpy.data.objects.remove(obj, do_unlink=True)

# MEASURE SCALE
char_height = char.dimensions.z
car_bbox = car.bound_box

# Front-left door approx (works well visually)
car_front = car.matrix_world @ Vector((
    car_bbox[4][0],
    car_bbox[4][1],
    0
))

# CHARACTER START / END
walk_distance = char_height * 3.0

start_pos = Vector((
    car_front.x - walk_distance,
    car_front.y,
    0
))

end_pos = Vector((
    car_front.x - char_height * 0.4,
    car_front.y,
    0
))

char.location = start_pos
char.keyframe_insert(data_path="location", frame=1)

char.location = end_pos
char.keyframe_insert(data_path="location", frame=100)

# CAMERA (SIDE VIEW)
bpy.ops.object.camera_add()
cam = bpy.context.object

mid_x = (start_pos.x + end_pos.x) / 2

cam.location = (
    mid_x,
    start_pos.y - walk_distance * 1.4,
    char_height * 1.4
)

cam.rotation_euler = (1.2, 0, 0)
scene.camera = cam

# LIGHTING (CLEAN & READABLE)
# Key light
bpy.ops.object.light_add(type="AREA")
key = bpy.context.object
key.location = (mid_x, -walk_distance, char_height * 4)
key.data.energy = 1200
key.data.size = 5

# Fill light
bpy.ops.object.light_add(type="AREA")
fill = bpy.context.object
fill.location = (mid_x, walk_distance, char_height * 2)
fill.data.energy = 300
fill.data.size = 6

# Rim light
bpy.ops.object.light_add(type="AREA")
rim = bpy.context.object
rim.location = (mid_x + 3, 0, char_height * 3)
rim.data.energy = 400
rim.data.size = 4

# RENDER SETTINGS
scene.render.engine = "BLENDER_EEVEE"
scene.render.fps = 24
scene.render.filepath = "/tmp/walk_to_car.mp4"
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"

# RENDER
bpy.ops.render.render(animation=True)
