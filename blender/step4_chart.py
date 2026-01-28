# blender/step4_chart.py
import bpy

# 0. Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# 1. Data
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
spacing = 1.6
num_bars = len(data)
chart_width = (num_bars - 1) * spacing + 1.0  # add margin for aesthetics

# 2. Materials
def mat(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    return m

floor_mat = mat("Floor", (0.05, 0.05, 0.06))
base_mat = mat("Base", (0.12, 0.12, 0.14))
bar_mat = mat("Bar", (0.25, 0.6, 1.0))
text_mat = mat("Text", (1, 1, 1))

# 3. Infinite floor
bpy.ops.mesh.primitive_plane_add(size=50, location=(chart_width/2, 0, 0))
floor = bpy.context.object
floor.data.materials.append(floor_mat)

# 4. Chart base / stand
bpy.ops.mesh.primitive_cube_add(location=(chart_width/2, 0, 0.2))
base = bpy.context.object
base.scale = (chart_width/2, 1.5, 0.2)  # full width + slight depth
base.data.materials.append(base_mat)

# Animate base appearance
base.scale.z = 0
base.keyframe_insert("scale", frame=1)
base.scale.z = 0.2
base.keyframe_insert("scale", frame=20)

# 5. Bars + labels
bars = []

for i, (label, value) in enumerate(data):
    h = value * height_scale
    x = i * spacing

    # Bar origin at base top
    bpy.ops.mesh.primitive_cube_add(location=(x, 0, 0.2))
    bar = bpy.context.object
    bar.scale = (0.45, 0.45, 0)  # start at 0 height
    bar.data.materials.append(bar_mat)
    bars.append((bar, h))

    # Month label (on base)
    bpy.ops.object.text_add(location=(x, -1.1, 0.22))
    txt = bpy.context.object
    txt.data.body = label
    txt.data.size = 0.32
    txt.rotation_euler = (1.57, 0, 0)
    txt.data.materials.append(text_mat)

    # Value label (above bar)
    bpy.ops.object.text_add(location=(x, 0, h + 0.6))
    val = bpy.context.object
    val.data.body = str(value)
    val.data.size = 0.3
    val.data.materials.append(text_mat)

# 6. Animate bars (emerge from base)
for i, (bar, h) in enumerate(bars):
    start = 25 + i * 10
    peak = start + 8
    settle = start + 14

    bar.scale.z = 0
    bar.location.z = 0.2
    bar.keyframe_insert("scale", frame=start)
    bar.keyframe_insert("location", frame=start)

    # Overshoot
    bar.scale.z = h * 1.05
    bar.location.z = 0.2 + (h * 1.05)/2
    bar.keyframe_insert("scale", frame=peak)
    bar.keyframe_insert("location", frame=peak)

    # Settle
    bar.scale.z = h
    bar.location.z = 0.2 + h/2
    bar.keyframe_insert("scale", frame=settle)
    bar.keyframe_insert("location", frame=settle)

# 7. Camera (intentional framing + motion)
bpy.ops.object.camera_add(location=(-2, -chart_width - 5, 4))
cam = bpy.context.object
scene.camera = cam

# Track target (center of chart)
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (chart_width/2, 0, 1.5)

track = cam.constraints.new(type="TRACK_TO")
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

# Side-follow motion while bars appear
cam.keyframe_insert("location", frame=20)
cam.location = (chart_width + 2, -chart_width -5, 4)
cam.keyframe_insert("location", frame=90)

# Hero final shot
cam.location = (chart_width/2, -chart_width -8, 6)
cam.keyframe_insert("location", frame=160)

# 8. Lighting
def add_light(loc, energy):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object
    l.data.energy = energy

add_light((chart_width + 5, -chart_width -5, 7), 1800)  # key
add_light((-5, -chart_width -5, 4), 800)                 # fill
add_light((chart_width/2, chart_width/2, 6), 600)       # rim

# 9. Render settings
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 64
scene.eevee.use_soft_shadows = True

scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.fps = 30

scene.frame_start = 1
scene.frame_end = 180

scene.render.filepath = "/tmp/step4_chart_master.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'

# 10. Render
bpy.ops.render.render(animation=True)
