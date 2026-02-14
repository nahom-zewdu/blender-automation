# scene_builder_2.py
""" blender script to build a simple scene from given 3D model assets and render it to a video"""

import sys
import os
import bpy
from mathutils import Vector

# ---------------- Headless Safety ----------------
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["DISPLAY"] = ":0"

os.makedirs("outputs", exist_ok=True)

# ---------------- Parse Args ----------------
# blender -b -P scene_builder.py -- path1,path2 output.mp4
args = sys.argv
sep = args.index("--")

asset_paths = args[sep + 1].split(",")
output_file = args[sep + 2]

# ---------------- Validate Assets ----------------
for p in asset_paths:
    if not os.path.exists(p):
        raise Exception(f"Asset missing: {p}")
    if os.path.getsize(p) < 1000:
        raise Exception(f"Asset corrupted or too small: {p}")

# ---------------- Reset Scene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------- Import Models ----------------
for path in asset_paths:
    print("Importing:", path)
    bpy.ops.import_scene.gltf(filepath=path)

# ---------------- Collect Mesh Objects ----------------
meshes = [obj for obj in scene.objects if obj.type == "MESH"]
if not meshes:
    raise Exception("No mesh objects imported")

# ---------------- Compute Bounding Box ----------------
min_corner = Vector((1e9, 1e9, 1e9))
max_corner = Vector((-1e9, -1e9, -1e9))

for obj in meshes:
    for v in obj.bound_box:
        world_v = obj.matrix_world @ Vector(v)
        min_corner = Vector((min(min_corner.x, world_v.x),
                             min(min_corner.y, world_v.y),
                             min(min_corner.z, world_v.z)))
        max_corner = Vector((max(max_corner.x, world_v.x),
                             max(max_corner.y, world_v.y),
                             max(max_corner.z, world_v.z)))

center = (min_corner + max_corner) / 2
size = (max_corner - min_corner).length

print("Scene center:", center)
print("Scene size:", size)

# ---------------- Move Objects to Origin ----------------
for obj in meshes:
    obj.location -= center

# ---------------- Camera ----------------
cam_data = bpy.data.camimport sys
import os
import bpy
from mathutils import Vector

# ---------------- Headless Safety ----------------
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["DISPLAY"] = ":0"

os.makedirs("outputs", exist_ok=True)

# ---------------- Parse Args ----------------
# Usage: blender -b -P scene_builder.py -- path1,path2 output.png
args = sys.argv
sep = args.index("--")

asset_paths = args[sep + 1].split(",")
output_file = args[sep + 2]

# ---------------- Validate Assets ----------------
for p in asset_paths:
    if not os.path.exists(p):
        raise Exception(f"Asset missing: {p}")
    if os.path.getsize(p) < 1000:
        raise Exception(f"Asset corrupted or too small: {p}")

# ---------------- Reset Scene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------- Import Models ----------------
for path in asset_paths:
    print("Importing:", path)
    bpy.ops.import_scene.gltf(filepath=path)

# ---------------- Collect Mesh Objects ----------------
meshes = [obj for obj in scene.objects if obj.type == "MESH"]
if not meshes:
    raise Exception("No mesh objects imported")

# ---------------- Compute Bounding Box ----------------
min_corner = Vector((1e9, 1e9, 1e9))
max_corner = Vector((-1e9, -1e9, -1e9))

for obj in meshes:
    for v in obj.bound_box:
        world_v = obj.matrix_world @ Vector(v)
        min_corner = Vector((min(min_corner.x, world_v.x),
                             min(min_corner.y, world_v.y),
                             min(min_corner.z, world_v.z)))
        max_corner = Vector((max(max_corner.x, world_v.x),
                             max(max_corner.y, world_v.y),
                             max(max_corner.z, world_v.z)))

center = (min_corner + max_corner) / 2
size = (max_corner - min_corner).length

print("Scene center:", center)
print("Scene size:", size)

# ---------------- Move Objects to Origin ----------------
for obj in meshes:
    obj.location -= center

# ---------------- Scale Objects ----------------
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

distance = max(size * scale_factor * 2.0, 5.0)
cam_obj.location = (distance, -distance, distance)
direction = Vector((0, 0, 0)) - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

# ---------------- Lighting ----------------
# Sun
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = max(size*5.0, 10)
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (distance, distance, distance)

# Fill lights
fill_positions = [
    (-distance, -distance, distance),
    (distance, -distance, distance),
    (-distance, distance, distance),
]
for i, pos in enumerate(fill_positions):
    fill_data = bpy.data.lights.new(f"Fill{i}", type="POINT")
    fill_data.energy = max(size*20.0, 200)
    fill = bpy.data.objects.new(f"Fill{i}", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = pos

# ---------------- World Background ----------------
if bpy.data.worlds:
    world = bpy.data.worlds[0]
else:
    world = bpy.data.worlds.new("World")

scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[1].default_value = max(size, 1.5)

# ---------------- Render Engine ----------------
bpy.context.scene.render.engine = "CYCLES"

prefs = bpy.context.preferences
cycles_prefs = prefs.addons["cycles"].preferences
cycles_prefs.compute_device_type = "NONE"   # Force CPU
bpy.context.scene.cycles.device = "CPU"

bpy.context.scene.cycles.samples = 64
bpy.context.scene.cycles.use_adaptive_sampling = True

# ---------------- Render Resolution ----------------
bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.resolution_percentage = 100

# ---------------- Output ----------------
bpy.context.scene.render.filepath = os.path.join("outputs", output_file)
bpy.context.scene.render.image_settings.file_format = "PNG"

# ---------------- Render ----------------
bpy.ops.render.render(write_still=True)

print("Render done:", output_file)
eras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

distance = max(size * 2.5, 5.0)
cam_obj.location = (distance, -distance, distance)
direction = Vector((0, 0, 0)) - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

# ---------------- Lighting ----------------
# Strong Sun
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = max(size*20.0, 50)
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (distance, distance, distance)

# Fill lights
fill_positions = [
    (-distance, -distance, distance),
    (distance, -distance, distance),
    (-distance, distance, distance),
]
for i, pos in enumerate(fill_positions):
    fill_data = bpy.data.lights.new(f"Fill{i}", type="POINT")
    fill_data.energy = max(size*100.0, 300)
    fill = bpy.data.objects.new(f"Fill{i}", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = pos

# ---------------- World Background ----------------
if bpy.data.worlds:
    world = bpy.data.worlds[0]
else:
    world = bpy.data.worlds.new("World")

scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[1].default_value = max(size, 2.5)  # stronger background

# ---------------- Render Engine ----------------
bpy.context.scene.render.engine = "CYCLES"
prefs = bpy.context.preferences
cycles_prefs = prefs.addons["cycles"].preferences
cycles_prefs.compute_device_type = "NONE"   # CPU
bpy.context.scene.cycles.device = "CPU"

bpy.context.scene.cycles.samples = 128
bpy.context.scene.cycles.use_adaptive_sampling = True

# ---------------- Render Resolution ----------------
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100

# ---------------- VIDEO SETTINGS ----------------
scene.frame_start = 1
scene.frame_end = 10
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
scene.render.ffmpeg.gopsize = 10
scene.render.ffmpeg.audio_codec = 'NONE'

scene.render.filepath = os.path.join("outputs", output_file)

# ---------------- RENDER ----------------
bpy.ops.render.render(animation=True)

print("Video render done:", output_file)
