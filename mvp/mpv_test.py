import bpy
import math
from mathutils import Vector

# RESET SCENE
bpy.ops.wm.read_factory_settings(use_empty=True)


# IMPORT ASSET AND DETECT NEW OBJECTS
def import_asset(path):
    before = set(bpy.data.objects)

    if path.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=path)
    elif path.lower().endswith(".glb") or path.lower().endswith(".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        raise Exception("Unsupported format: " + path)

    after = set(bpy.data.objects)
    return list(after - before)


# SAFE WRAP (PRESERVE INTERNAL HIERARCHY)
def wrap_asset(name, objects):
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)

    for obj in objects:
        if obj.parent is None:   # Only parent top-level objects
            obj.parent = root

    return root


# APPLY TRANSFORMS
def apply_transforms(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)


# COMBINED BOUNDING BOX (ALL CHILD MESHES)
def get_combined_bbox(obj):
    meshes = [o for o in obj.children_recursive if o.type == 'MESH']
    if not meshes:
        return None

    min_v = Vector((1e9, 1e9, 1e9))
    max_v = Vector((-1e9, -1e9, -1e9))

    for m in meshes:
        for corner in m.bound_box:
            world_corner = m.matrix_world @ Vector(corner)
            min_v = Vector(map(min, min_v, world_corner))
            max_v = Vector(map(max, max_v, world_corner))

    return min_v, max_v


# NORMALIZE HEIGHT
def normalize_height(root, target_height):
    bpy.context.view_layer.update()

    bbox = get_combined_bbox(root)
    if not bbox:
        return

    min_v, max_v = bbox
    height = max_v.z - min_v.z
    if height == 0:
        return

    scale_factor = target_height / height
    root.scale *= scale_factor


# DEBUG HEIGHT
def debug_height(name, root):
    bbox = get_combined_bbox(root)
    if not bbox:
        print(name, "NO MESH FOUND")
        return

    min_v, max_v = bbox
    print(name, "height =", round(max_v.z - min_v.z, 4))


# SIMPLE MOVE ANIMATION
def animate_move(obj, start, end, frame_start, frame_end):
    obj.location = start
    obj.keyframe_insert(data_path="location", frame=frame_start)

    obj.location = end
    obj.keyframe_insert(data_path="location", frame=frame_end)


# IMPORT YOUR ASSETS (EDIT PATHS)
kid_objs = import_asset("/home/nahom/Downloads/blender/assets/kid.glb")
ball_objs = import_asset("/home/nahom/Downloads/blender/assets/ball.glb")
court_objs = import_asset("/home/nahom/Downloads/blender/assets/court.glb")

kid = wrap_asset("ASSET_KID", kid_objs)
ball = wrap_asset("ASSET_BALL", ball_objs)
court = wrap_asset("ASSET_COURT", court_objs)

# APPLY TRANSFORMS (STABILIZE)
apply_transforms(kid)
apply_transforms(ball)
apply_transforms(court)

# NORMALIZE SCALE
normalize_height(kid, 1.2)     # kid ≈ 1.2m
normalize_height(ball, 0.24)   # basketball ≈ 24cm
normalize_height(court, 10.0)  # arbitrary ground scale

# DEBUG HEIGHT OUTPUT (CHECK CONSOLE)
debug_height("Kid", kid)
debug_height("Ball", ball)
debug_height("Court", court)

# FIX ROTATION IF MODEL IMPORTED SIDEWAYS
# (Uncomment if kid lies down or rotated wrong)
# kid.rotation_euler[0] = math.radians(90)

# POSITION OBJECTS
court.location = (0, 0, 0)
kid.location = (0, 0, 0)
ball.location = (0.3, 0, 1)

# SIMPLE MOVEMENT ANIMATION (WORLD SPACE ONLY)
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 120

animate_move(kid, Vector((0, 0, 0)), Vector((3, 0, 0)), 1, 120)
animate_move(ball, Vector((0.3, 0, 1)), Vector((3.3, 0, 1)), 1, 120)

print("MVP scene ready (preview in timeline)")
