# mvp/mvp_with_manifest.py
""" load multiple assets, standardize them, generate manifests, and create a simple animated scene """
import bpy
import json
import os
from mathutils import Vector

# CONFIG

ASSETS_ROOT = "assets"

ASSET_FILES = {
    "kid_1": "kid.fbx",
    "ball_1": "ball.glb",
    "court_1": "court.fbx"
}

MANIFEST_DIR = os.path.join(ASSETS_ROOT, "manifests")
os.makedirs(MANIFEST_DIR, exist_ok=True)


# RESET SCENE

bpy.ops.wm.read_factory_settings(use_empty=True)


# IMPORT ASSET
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
        if obj.parent is None:
            obj.parent = root

    return root


# APPLY TRANSFORMS
def apply_transforms(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)


# COMBINED BOUNDING BOX
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


# MANIFEST GENERATOR
def generate_manifest(asset_id, root):
    meshes = [o.name for o in root.children_recursive if o.type == 'MESH']
    armatures = [o.name for o in root.children_recursive if o.type == 'ARMATURE']

    bbox = get_combined_bbox(root)
    height = None
    if bbox:
        min_v, max_v = bbox
        height = float(max_v.z - min_v.z)

    manifest = {
        "asset_id": asset_id,
        "root_object": root.name,
        "meshes": meshes,
        "mesh_count": len(meshes),
        "has_armature": len(armatures) > 0,
        "armatures": armatures,
        "height": height,
        "object_count": len(root.children_recursive),
    }

    path = os.path.join(MANIFEST_DIR, f"{asset_id}.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("Manifest saved:", path)
    return manifest


# IMPORT + STANDARDIZE + MANIFEST

ASSETS = {}

for asset_id, filename in ASSET_FILES.items():

    full_path = os.path.join(ASSETS_ROOT, filename)
    print("\nImporting:", asset_id, "from", full_path)

    objs = import_asset(full_path)
    root = wrap_asset(f"ASSET_{asset_id.upper()}", objs)

    apply_transforms(root)

    # Normalize based on type
    if "kid" in asset_id:
        normalize_height(root, 1.2)
    elif "ball" in asset_id:
        normalize_height(root, 0.24)
    else:
        normalize_height(root, 10.0)

    manifest = generate_manifest(asset_id, root)
    ASSETS[asset_id] = root


# SIMPLE SCENE ASSEMBLY

court = ASSETS["court_1"]
kid = ASSETS["kid_1"]
ball = ASSETS["ball_1"]

court.location = (0, 0, 0)
kid.location = (0, 0, 0)
ball.location = (0.3, 0, 1)


# SIMPLE WORLD-SPACE ANIMATION
def animate_move(obj, start, end, f1, f2):
    obj.location = start
    obj.keyframe_insert(data_path="location", frame=f1)

    obj.location = end
    obj.keyframe_insert(data_path="location", frame=f2)


bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 120

animate_move(kid, Vector((0, 0, 0)), Vector((3, 0, 0)), 1, 120)
animate_move(ball, Vector((0.3, 0, 1)), Vector((3.3, 0, 1)), 1, 120)

print("\nMVP + Manifest ready")
