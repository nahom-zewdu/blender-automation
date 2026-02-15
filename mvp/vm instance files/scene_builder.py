# scene_builder.py
"""Build a simple scene from GLB assets and render image or video (GPU enabled)."""

import sys
import os
import bpy
from mathutils import Vector

# ---------------- Headless Safety ----------------
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["DISPLAY"] = ":0"

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- Parse Args ----------------
# blender -b -P scene_builder.py -- path1,path2 output.png|mp4
args = sys.argv
sep = args.index("--")

asset_paths = args[sep + 1].split(",")
output_file = args[sep + 2]
output_path = os.path.join(OUTPUT_DIR, output_file)

# ---------------- Validate Assets ----------------
for p in asset_paths:
    if not os.path.exists(p):
        raise Exception(f"Asset missing: {p}")
    if os.path.getsize(p) < 1000:
        raise Exception(f"Asset corrupted: {p}")

# ---------------- Reset Scene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------- Import GLB ----------------
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

# ---------------- Normalize Scene ----------------
for obj in meshes:
    obj.location -= center

scale_factor = 1.0
if size < 1.0:
    scale_factor = 2.0 / size
elif size > 10.0:
    scale_factor = 8.0 / size

for obj in meshes:
    obj.scale *= scale_factor

# ---------------- Camera ----------------
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

distance = max(size * scale_factor * 2.5, 5.0)
cam_obj.location = (distance, -distance, distance)
direction = Vector((0, 0, 0)) - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

# ---------------- Lighting ----------------
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = max(size * 20.0, 50)
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (distance, distance, distance)

for i, pos in enumerate([
    (-distance, -distance, distance),
    (distance, -distance, distance),
    (-distance, distance, distance),
]):
    light = bpy.data.lights.new(f"Fill{i}", type="POINT")
    light.energy = max(size * 100.0, 300)
    obj = bpy.data.objects.new(f"Fill{i}", light)
    bpy.context.collection.objects.link(obj)
    obj.location = pos

# ---------------- World ----------------
world = bpy.data.worlds.new("World") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[1].default_value = max(size, 2.5)

# ---------------- Render Engine (GPU) ----------------
scene.render.engine = "CYCLES"

prefs = bpy.context.preferences
cycles = prefs.addons["cycles"].preferences
cycles.compute_device_type = "CUDA"
cycles.get_devices()
for d in cycles.devices:
    d.use = True

scene.cycles.device = "GPU"
scene.cycles.samples = 128
scene.cycles.use_adaptive_sampling = True

# ---------------- Resolution ----------------
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100

# ---------------- Output Type ----------------
ext = output_file.lower().split(".")[-1]

scene.render.filepath = output_path

if ext == "png":
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("Image render done:", output_file)

elif ext == "mp4":
    scene.frame_start = 1
    scene.frame_end = 10

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "NONE"

    bpy.ops.render.render(animation=True)
    print("Video render done:", output_file)

else:
    raise Exception("Unsupported output format (use png or mp4)")
