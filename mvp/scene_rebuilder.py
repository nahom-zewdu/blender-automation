# mvp/scene_rebuilder.py

import bpy
import json
import os
from mathutils import Vector

# CONFIG
ASSETS_ROOT = "assets"
MANIFEST_DIR = os.path.join(ASSETS_ROOT, "manifests")

ASSET_FILES = {
    "kid_1": "kid.glb",
    "ball_1": "ball.glb",
    "court_1": "court.glb"
}

SCENE_MANIFEST = os.path.join(MANIFEST_DIR, "scene_001.scene.json")


# RESET SCENE
bpy.ops.wm.read_factory_settings(use_empty=True)


# IMPORT ASSET (same logic as your generator)
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


# WRAP ASSET (preserve hierarchy)
def wrap_asset(name, objects):
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)

    for obj in objects:
        if obj.parent is None:
            obj.parent = root

    return root


# LOAD SCENE MANIFEST
if not os.path.exists(SCENE_MANIFEST):
    raise Exception("Scene manifest not found")

with open(SCENE_MANIFEST, "r") as f:
    scene_data = json.load(f)


# IMPORT ALL ASSETS FROM MANIFEST
ASSETS = {}

for asset_id, data in scene_data["assets"].items():

    if asset_id not in ASSET_FILES:
        print("Unknown asset:", asset_id)
        continue

    asset_path = os.path.join(ASSETS_ROOT, ASSET_FILES[asset_id])

    print("Importing:", asset_id)

    objs = import_asset(asset_path)
    root = wrap_asset(data["root_object"], objs)

    # Apply transform from scene manifest
    root.location = Vector(data.get("location", [0, 0, 0]))
    root.scale = Vector(data.get("scale", [1, 1, 1]))

    ASSETS[asset_id] = root


# APPLY SCENE FRAME RANGE
bpy.context.scene.frame_start = scene_data["frame_start"]
bpy.context.scene.frame_end = scene_data["frame_end"]


# OPTIONAL: REBUILD SIMPLE LINEAR ANIMATION
# (Only if animation exists in manifest in future)
def animate_move(obj, start, end, f1, f2):
    obj.location = start
    obj.keyframe_insert(data_path="location", frame=f1)

    obj.location = end
    obj.keyframe_insert(data_path="location", frame=f2)


print("\n[SUCCESS] Scene rebuilt deterministically from scene manifest.")
