# scene_builder.py
"""Build a simple scene from GLB assets and render image or video (GPU enabled)."""

import sys
import os
import bpy
from mathutils import Vector

# ---------------- Environment ----------------
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["DISPLAY"] = ":0"

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- Parse Args ----------------
args = sys.argv
sep = args.index("--")

asset_paths = args[sep + 1].split(",")
output_file = args[sep + 2]
output_ext = output_file.lower().split(".")[-1]
output_base = os.path.join(OUTPUT_DIR, output_file.rsplit(".", 1)[0])

# ---------------- Validate Assets ----------------
for p in asset_paths:
    if not os.path.exists(p):
        raise Exception(f"Missing asset: {p}")
    if os.path.getsize(p) < 1000:
        raise Exception(f"Corrupt asset: {p}")

# ---------------- Reset Scene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------- Import Assets ----------------
for path in asset_paths:
    print("Importing:", path)
    bpy.ops.import_scene.gltf(filepath=path)

meshes = [obj for obj in scene.objects if obj.type == "MESH"]
if not meshes:
    raise Exception("No mesh objects imported")

# ---------------- Compute Bounding Box ----------------
min_corner = Vector((1e9, 1e9, 1e9))
max_corner = Vector((-1e9, -1e9, -1e9))

for obj in meshes:
    for v in obj.bound_box:
        world_v = obj.matrix_world @ Vector(v)
        min_corner.x = min(min_corner.x, world_v.x)
        min_corner.y = min(min_corner.y, world_v.y)
        min_corner.z = min(min_corner.z, world_v.z)
        max_corner.x = max(max_corner.x, world_v.x)
        max_corner.y = max(max_corner.y, world_v.y)
        max_corner.z = max(max_corner.z, world_v.z)

center = (min_corner + max_corner) / 2
size = (max_corner - min_corner).length

# ---------------- Normalize + Center ----------------
for obj in meshes:
    obj.location -= center

scale_factor = 1.0
if size < 1:
    scale_factor = 2 / size
elif size > 10:
    scale_factor = 8 / size

for obj in meshes:
    obj.scale *= scale_factor
    obj.location.z = 0

# ---------------- Camera ----------------
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

distance = max(size * scale_factor * 2.5, 5)
cam_obj.location = (distance, -distance, distance * 1.4)
direction = Vector((0, 0, 0)) - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

# ---------------- Lighting ----------------
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (distance, distance, distance)

fill_positions = [
    (-distance, -distance, distance),
    (distance, -distance, distance),
    (-distance, distance, distance),
]

for i, pos in enumerate(fill_positions):
    light = bpy.data.lights.new(f"Fill{i}", type="POINT")
    light.energy = 200
    obj = bpy.data.objects.new(f"Fill{i}", light)
    bpy.context.collection.objects.link(obj)
    obj.location = pos

# ---------------- World (Prevent White Screen) ----------------
world = bpy.data.worlds.new("World") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")

bg.inputs[0].default_value = (0.05, 0.05, 0.05, 1)  # dark gray
bg.inputs[1].default_value = 1.0  # strength

# ---------------- Render Engine ----------------
scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.cycles.use_adaptive_sampling = True

# -------- GPU Try --------
try:
    prefs = bpy.context.preferences
    cycles = prefs.addons["cycles"].preferences
    cycles.compute_device_type = "CUDA"
    cycles.get_devices()
    for d in cycles.devices:
        d.use = True
    scene.cycles.device = "GPU"
    print("Using GPU")
except:
    scene.cycles.device = "CPU"
    print("GPU failed → using CPU")

# ---------------- Resolution ----------------
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100

# ---------------- Validate Output ----------------
import glob
import time

time.sleep(1)  # give filesystem a moment to finalize file

if output_ext == "png":
    expected = output_base + ".png"
    if not os.path.exists(expected) or os.path.getsize(expected) < 2000:
        raise Exception("PNG render failed or empty")
    print("FINAL OUTPUT:", expected)

elif output_ext == "mp4":
    # Blender sometimes alters filename → search safely
    pattern = output_base + "*.mp4"
    matches = glob.glob(pattern)

    if not matches:
        raise Exception("MP4 not generated")

    final_video = max(matches, key=os.path.getsize)

    if os.path.getsize(final_video) < 5000:
        raise Exception("MP4 too small / empty")

    print("FINAL OUTPUT:", final_video)

else:
    raise Exception("Unsupported output format (png or mp4)")

# ---------------- Validate Output ----------------
final_path = output_base + (".png" if output_ext == "png" else ".mp4")

if not os.path.exists(final_path) or os.path.getsize(final_path) < 5000:
    raise Exception("Render failed or empty output")

print("FINAL OUTPUT:", final_path)
