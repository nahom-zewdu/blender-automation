# mvp/engine_v1_scene_builder.py
""" simple script to read a scene manifest and build the scene in blender. """

import bpy
import json
import os
from mathutils import Vector

# CONFIG

ASSETS_ROOT = "assets"
MANIFEST_PATH = os.path.join(ASSETS_ROOT, "manifests", "scene_auto.scene.json")
ASSET_FILES = {
    "kid_1": "kid.glb",
    "ball_1": "ball.glb",
    "court_1": "court.glb"
}

# RESET SCENE

bpy.ops.wm.read_factory_settings(use_empty=True)


# IMPORT
def import_asset(filepath):
    before = set(bpy.data.objects)

    if filepath.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif filepath.lower().endswith(".glb") or filepath.lower().endswith(".gltf"):
        bpy.ops.import_scene.gltf(filepath=filepath)
    else:
        raise Exception("Unsupported format")

    after = set(bpy.data.objects)
    return list(after - before)

def wrap_asset(asset_id, objects):
    root_name = f"ASSET_{asset_id.upper()}"
    root = bpy.data.objects.new(root_name, None)
    bpy.context.scene.collection.objects.link(root)

    for obj in objects:
        if obj.parent is None:
            obj.parent = root

    return root


# LOAD SCENE MANIFEST

with open(MANIFEST_PATH) as f:
    scene_manifest = json.load(f)


# IMPORT ALL ASSETS

ASSETS = {}

for asset_id, asset_data in scene_manifest["assets"].items():

    filepath = os.path.join(ASSETS_ROOT, ASSET_FILES[asset_id])
    print("Importing:", filepath)

    objs = import_asset(filepath)
    root = wrap_asset(asset_id, objs)

    # Apply placement
    root.location = Vector(asset_data["location"])
    root.scale = Vector(asset_data["scale"])

    ASSETS[asset_id] = root


# SET FRAME RANGE

bpy.context.scene.frame_start = scene_manifest["frame_start"]
bpy.context.scene.frame_end = scene_manifest["frame_end"]


# APPLY ANIMATIONS
def animate_linear_move(obj, start, end, f1, f2):
    obj.location = Vector(start)
    obj.keyframe_insert(data_path="location", frame=f1)

    obj.location = Vector(end)
    obj.keyframe_insert(data_path="location", frame=f2)


for anim in scene_manifest.get("animations", []):

    obj = ASSETS[anim["asset_id"]]

    if anim["type"] == "linear_move":
        animate_linear_move(
            obj,
            anim["start"],
            anim["end"],
            anim["frames"][0],
            anim["frames"][1]
        )

print("\nScene Rebuilt Successfully")
