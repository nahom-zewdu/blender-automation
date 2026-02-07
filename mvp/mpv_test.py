"""
MVP Test Script for Blender
- Imports 3D assets (kid, ball, court)
- Normalizes their scale
- Sets up a simple animation of the kid and ball moving across the court
- Configures camera and lighting
- Prepares render settings for output video
"""
import bpy
import math
from mathutils import Vector

# -------------------------
# RESET SCENE
# -------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)

# -------------------------
# IMPORT FUNCTION
# -------------------------
def import_asset(path):
    before = set(bpy.data.objects)

    if path.endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=path)
    elif path.endswith(".glb") or path.endswith(".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        raise Exception("Unsupported format")

    after = set(bpy.data.objects)
    return list(after - before)


# -------------------------
# WRAP ASSET INTO ROOT
# -------------------------
def wrap_asset(name, objects):
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)

    for obj in objects:
        obj.parent = root

    return root


# -------------------------
# SCALE NORMALIZATION
# -------------------------
def normalize_height(root, target_height):
    bpy.context.view_layer.update()

    min_z = min((root.matrix_world @ Vector(b)).z for b in root.bound_box)
    max_z = max((root.matrix_world @ Vector(b)).z for b in root.bound_box)

    current_height = max_z - min_z
    if current_height == 0:
        return

    scale_factor = target_height / current_height
    root.scale *= scale_factor


# -------------------------
# SIMPLE MOVE ANIMATION
# -------------------------
def animate_move(obj, start, end, frame_start, frame_end):
    obj.location = start
    obj.keyframe_insert(data_path="location", frame=frame_start)

    obj.location = end
    obj.keyframe_insert(data_path="location", frame=frame_end)


# -------------------------
# IMPORT ASSETS
# -------------------------
kid_objs = import_asset("assets/kid.fbx")
ball_objs = import_asset("assets/ball.glb")
court_objs = import_asset("assets/court.fbx")

kid = wrap_asset("ASSET_KID", kid_objs)
ball = wrap_asset("ASSET_BALL", ball_objs)
court = wrap_asset("ASSET_COURT", court_objs)

# -------------------------
# NORMALIZE SCALE
# -------------------------
normalize_height(kid, 1.2)     # kid ≈ 1.2m tall
normalize_height(ball, 0.24)   # basketball ≈ 24cm
normalize_height(court, 10.0)  # arbitrary

# -------------------------
# POSITION OBJECTS
# -------------------------
court.location = (0, 0, 0)
kid.location = (0, 0, 0)
ball.location = (0.3, 0, 1)

# -------------------------
# ANIMATE SIMPLE MOVEMENT
# -------------------------
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 120

animate_move(kid, Vector((0, 0, 0)), Vector((3, 0, 0)), 1, 120)
animate_move(ball, Vector((0.3, 0, 1)), Vector((3.3, 0, 1)), 1, 120)

# -------------------------
# CAMERA
# -------------------------
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam)

cam.location = (6, -6, 4)
cam.rotation_euler = (math.radians(65), 0, math.radians(45))
bpy.context.scene.camera = cam

# -------------------------
# LIGHT
# -------------------------
light_data = bpy.data.lights.new(name="Light", type='SUN')
light = bpy.data.objects.new(name="Light", object_data=light_data)
bpy.context.scene.collection.objects.link(light)
light.location = (5, 5, 10)

# -------------------------
# RENDER SETTINGS
# -------------------------
bpy.context.scene.render.filepath = "//output.mp4"
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.ffmpeg.format = 'MPEG4'

print("MVP scene ready")
