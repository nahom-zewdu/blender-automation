""" Blender script to create a cinematic 3D bar chart animation"""

import bpy
from mathutils import Vector

# =============================
# 0. Reset scene
# =============================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# =============================
# 1. Data
# =============================
data = [
    ("Jan", 120),
    ("Feb", 180),
    ("Mar", 260),
    ("Apr", 340),
    ("May", 420),
    ("Jun", 520),
]
max_val = max(v for _, v in data)
height_scale = 3.5 / max_val
spacing = 1.8
num_bars = len(data)
chart_width = (num_bars - 1) * spacing + 1.2  # add margin

# =============================
# 2. Materials
# =============================
def create_material(name, color, metallic=0.0, roughness=0.4):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = (*color,1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

floor_mat = create_material("Floor", (0.05, 0.05, 0.06), 0.0, 0.6)
base_mat  = create_material("Base",  (0.12, 0.12, 0.14), 0.0, 0.25)
bar_mat   = create_material("Bar",   (0.25, 0.6, 1.0), 0.1, 0.2)
text_mat  = create_material("Text",  (1,1,1), 0, 0.0)

# =============================
# 3. Infinite floor
# =============================
bpy.ops.mesh.primitive_plane_add(size=50, location=(chart_width/2,0,0))
floor = bpy.context.object
floor.data.materials.append(floor_mat)

# =============================
# 4. Chart base (stand)
# =============================
bpy.ops.mesh.primitive_cube_add(location=(chart_width/2,0,0.15))
base = bpy.context.object
base.scale = (chart_width/2,1.5,0.15)
base.data.materials.append(base_mat)

# Bevel modifier for smooth edges
bevel = base.modifiers.new(name="BevelBase", type='BEVEL')
bevel.width = 0.05
bevel.segments = 5

# Animate base appearance
base.scale.z = 0
base.keyframe_insert("scale", frame=1)
base.scale.z = 0.15
base.keyframe_insert("scale", frame=20)
for fcu in base.animation_data.action.fcurves:
    for kp in fcu.keyframe_points:
        kp.interpolation = 'BEZIER'

# =============================
# 5. Bars and labels
# =============================
bars = []

for i, (label, value) in enumerate(data):
    h = value * height_scale
    x = i * spacing

    # Bar origin at base top
    bpy.ops.mesh.primitive_cube_add(location=(x,0,0.15))
    bar = bpy.context.object
    bar.scale = (0.45,0.45,0)
    bar.data.materials.append(bar_mat)

    # Rounded edges via bevel
    b_bevel = bar.modifiers.new(name="BevelBar", type='BEVEL')
    b_bevel.width = 0.05
    b_bevel.segments = 5
    bars.append((bar, h))

    # Month text
    bpy.ops.object.text_add(location=(x,-1.0,0.17))
    t = bpy.context.object
    t.data.body = label
    t.data.size = 0.35
    t.rotation_euler = (1.57,0,0)
    t.data.materials.append(text_mat)

    # Value text (floating above, start invisible)
    bpy.ops.object.text_add(location=(x,0,h+0.6))
    val = bpy.context.object
    val.data.body = str(value)
    val.data.size = 0.3
    val.data.materials.append(text_mat)
    val.hide_render = True
    val.keyframe_insert("hide_render", frame=1)
    val.hide_render = False
    val.keyframe_insert("hide_render", frame=40)

# =============================
# 6. Bars animation (emerge from base)
# =============================
for i, (bar, h) in enumerate(bars):
    start = 25 + i*10
    peak  = start + 8
    settle= start + 14

    bar.scale.z = 0
    bar.location.z = 0.15
    bar.keyframe_insert("scale", frame=start)
    bar.keyframe_insert("location", frame=start)

    bar.scale.z = h*1.05
    bar.location.z = 0.15 + (h*1.05)/2
    bar.keyframe_insert("scale", frame=peak)
    bar.keyframe_insert("location", frame=peak)

    bar.scale.z = h
    bar.location.z = 0.15 + h/2
    bar.keyframe_insert("scale", frame=settle)
    bar.keyframe_insert("location", frame=settle)

    for fcu in bar.animation_data.action.fcurves:
        for kp in fcu.keyframe_points:
            kp.interpolation = 'BEZIER'

# =============================
# 7. Camera (dynamic cinematic)
# =============================
bpy.ops.object.camera_add(location=(-2,-chart_width-5,4))
cam = bpy.context.object
scene.camera = cam

# Track target
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (chart_width/2,0,1.5)
track = cam.constraints.new(type='TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

# Camera side-follow
cam.keyframe_insert("location", frame=20)
cam.location = (chart_width+2,-chart_width-5,4)
cam.keyframe_insert("location", frame=90)

# Final hero pull-back
cam.location = (chart_width/2,-chart_width-9,6)
cam.keyframe_insert("location", frame=180)

# =============================
# 8. Lighting (studio-quality)
# =============================
def add_light(loc, energy, size=2):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object
    l.data.energy = energy
    l.data.size = size

add_light((chart_width+5,-chart_width-5,7), 1800)   # key
add_light((-5,-chart_width-5,4), 700)               # fill
add_light((chart_width/2,chart_width/2,6), 600)    # rim
add_light((chart_width/2,-chart_width-5,10), 200)  # top subtle

# =============================
# 9. Render
# =============================
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 128
scene.eevee.use_soft_shadows = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 200
scene.render.filepath = "/tmp/step5_chart_studio.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'

# =============================
# 10. Render
# =============================
bpy.ops.render.render(animation=True)
