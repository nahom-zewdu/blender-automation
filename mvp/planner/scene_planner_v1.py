# planner/scene_planner_v1.py
"""Deterministic rule-based scene planner that generates a scene manifest for the Blender engine."""

import json
import os

# OUTPUT PATH
ASSETS_ROOT = "assets"
MANIFEST_DIR = os.path.join(ASSETS_ROOT, "manifests")
os.makedirs(MANIFEST_DIR, exist_ok=True)

OUTPUT_MANIFEST = os.path.join(MANIFEST_DIR, "scene_auto.scene.json")


# ASSET REGISTRY (logical name → asset id used by engine)
ASSET_REGISTRY = {
    "kid": "kid_1",
    "ball": "ball_1",
    "court": "court_1"
}


# DEFAULT POSITIONS (logical world layout)
LAYOUTS = {
    "court_center": [0, 0, 0],
    "actor_start": [0, 0, 0],
    "object_hold_offset": [0.3, 0, 1],
    "move_target": [3, 0, 0]
}


def build_static_scene(actor, obj, env):
    return {
        "assets": {
            actor: {"location": LAYOUTS["actor_start"]},
            obj: {"location": LAYOUTS["object_hold_offset"]},
            env: {"location": LAYOUTS["court_center"]}
        },
        "animations": []
    }


def build_move_actor(actor, obj, env):
    return {
        "assets": {
            actor: {"location": LAYOUTS["actor_start"]},
            obj: {"location": LAYOUTS["object_hold_offset"]},
            env: {"location": LAYOUTS["court_center"]}
        },
        "animations": [
            {
                "type": "linear_move",
                "asset_id": actor,
                "start": LAYOUTS["actor_start"],
                "end": LAYOUTS["move_target"],
                "frames": [1, 120]
            }
        ]
    }


def build_carry_object(actor, obj, env):
    return {
        "assets": {
            actor: {"location": LAYOUTS["actor_start"]},
            obj: {"location": LAYOUTS["object_hold_offset"]},
            env: {"location": LAYOUTS["court_center"]}
        },
        "animations": [
            {
                "type": "linear_move",
                "asset_id": actor,
                "start": LAYOUTS["actor_start"],
                "end": LAYOUTS["move_target"],
                "frames": [1, 120]
            },
            {
                "type": "follow",
                "target": actor,
                "follower": obj
            }
        ]
    }


def plan_scene(request):
    scene_type = request["scene_type"]

    actor = ASSET_REGISTRY[request["actor"]]
    obj = ASSET_REGISTRY[request["object"]]
    env = ASSET_REGISTRY[request["environment"]]

    if scene_type == "static_scene":
        return build_static_scene(actor, obj, env)

    if scene_type == "move_actor":
        return build_move_actor(actor, obj, env)

    if scene_type == "carry_object":
        return build_carry_object(actor, obj, env)

    raise Exception(f"Unknown scene_type: {scene_type}")


def build_scene_manifest(request):
    scene_data = plan_scene(request)

    manifest = {
        "scene_id": "scene_auto",
        "frame_start": 1,
        "frame_end": 120,
        "assets": {},
        "animations": scene_data["animations"]
    }

    for asset_id, data in scene_data["assets"].items():
        manifest["assets"][asset_id] = {
            "location": data["location"]
        }

    with open(OUTPUT_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)

    print("Scene manifest generated →", OUTPUT_MANIFEST)


REQUEST = {
    "scene_type": "move_actor",   # "static_scene", "move_actor", or "carry_object"
    "actor": "kid",
    "object": "ball",
    "environment": "court"
}

if __name__ == "__main__":
    build_scene_manifest(REQUEST)
