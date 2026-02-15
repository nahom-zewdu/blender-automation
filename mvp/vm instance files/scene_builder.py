# scene_builder.py
"""Build a simple scene from GLB assets and render image or video (GPU enabled)."""

import sys
import os
import glob
import time
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

# ---------------- Normalize ----------------
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
sun_data.energy = 4
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (distance, distance, distance)

for i, pos in enumerate([
    (-distance, -distance, distance),
    (distance, -distance, distance),
    (-distance, distance, distance),
]):
    light = bpy.data.lights.new(f"Fill{i}", type="POINT")
    light.energy = 250
    obj = bpy.data.objects.new(f"Fill{i}", light)
    bpy.context.collection.objects.link(obj)
    obj.location = pos

# ---------------- World ----------------
world = bpy.data.worlds.new("World") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.05, 0.05, 0.05, 1)
bg.inputs[1].default_value = 1.0

# ---------------- Render Engine ----------------
scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.cycles.use_adaptive_sampling = True

# ---- GPU try ----
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
    print("GPU unavailable → using CPU")

# ---------------- Resolution ----------------
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100

# ==================== RENDER ====================

if output_ext == "png":

    scene.render.filepath = output_base + ".png"
    scene.render.image_settings.file_format = "PNG"

    print("Rendering PNG...")
    bpy.ops.render.render(write_still=True)

elif output_ext == "mp4":

    scene.frame_start = 1
    scene.frame_end = 60  # 2 seconds @30fps

    scene.render.filepath = output_base
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.fps = 30

    print("Rendering MP4...")
    bpy.ops.render.render(animation=True)

else:
    raise Exception("Unsupported output format (png or mp4)")

# ==================== VALIDATE ====================

time.sleep(1)

if output_ext == "png":
    final = output_base + ".png"
else:
    matches = glob.glob(output_base + ".mp4")
    if not matches:
        raise Exception("MP4 not generated")
    final = max(matches, key=os.path.getsize)

if not os.path.exists(final) or os.path.getsize(final) < 5000:
    raise Exception("Render failed or empty output")

print("FINAL OUTPUT:", final)
