# mvp/planner_v1_scene_assembler.py
""" simple script to assemble a scene manifest for the MVP, based on a hardcoded spec."""

import json
import os
from math import ceil

# CONFIG
ASSETS_ROOT = "/home/nahom/Downloads/blender/assets"
MANIFEST_DIR = os.path.join(ASSETS_ROOT, "manifests")
SCENE_OUTPUT = os.path.join(MANIFEST_DIR, "scene_auto.scene.json")

GRID_SPACING = 2.0  # used for auto placement
DEFAULT_FRAMES = [1, 120]


def load_asset_manifest(asset_id):
    path = os.path.join(MANIFEST_DIR, f"{asset_id}.json")
    if not os.path.exists(path):
        raise Exception(f"Missing asset manifest: {asset_id}")
    with open(path) as f:
        return json.load(f)


def auto_place(index):
    cols = 3
    row = index // cols
    col = index % cols
    return [col * GRID_SPACING, row * GRID_SPACING, 0]


# VALIDATE + BUILD SCENE
def build_scene(scene_spec):

    assets_out = {}
    animations_out = []

    # --- Validate + place objects ---
    for i, obj in enumerate(scene_spec["objects"]):

        asset_id = obj["asset"]
        manifest = load_asset_manifest(asset_id)

        position = obj.get("position")
        if position is None:
            position = auto_place(i)

        assets_out[asset_id] = {
            "asset_id": asset_id,
            "root_object": manifest["root_object"],
            "location": position,
            "scale": [1, 1, 1]
        }

    # --- Build animation ---
    for anim in scene_spec.get("animations", []):

        asset_id = anim["asset"]

        animations_out.append({
            "asset_id": asset_id,
            "type": anim["type"],
            "start": anim["start"],
            "end": anim["end"],
            "frames": anim.get("frames", DEFAULT_FRAMES)
        })

    # --- Scene manifest ---
    scene_manifest = {
        "scene_id": scene_spec["scene"],
        "frame_start": DEFAULT_FRAMES[0],
        "frame_end": DEFAULT_FRAMES[1],
        "assets": assets_out,
        "animations": animations_out,
        "attachments": scene_spec.get("attachments", [])
    }

    return scene_manifest


def save_scene(scene_data):
    with open(SCENE_OUTPUT, "w") as f:
        json.dump(scene_data, f, indent=2)
    print("Scene manifest generated:", SCENE_OUTPUT)


# MVP SCENE SPEC (manual for now)
SCENE_SPEC = {
    "scene": "kid_playing_ball",

    "objects": [
        {"asset": "court_1", "position": [0, 0, 0]},
        {"asset": "kid_1"},  # auto place
        {"asset": "ball_1"}  # auto place
    ],

    "animations": [
        {
            "asset": "kid_1",
            "type": "linear_move",
            "start": [0, 0, 0],
            "end": [3, 0, 0],
            "frames": [1, 120]
        }
    ],
    "attachments": [
        {
            "child": "ball_1",
            "parent": "kid_1",
            "offset": [0.3, 0, 1]
        }
]

}

if __name__ == "__main__":
    scene = build_scene(SCENE_SPEC)
    save_scene(scene)
