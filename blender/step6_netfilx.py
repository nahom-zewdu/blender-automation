""" Blender script to create a cinematic 3D bar chart animation,
set up camera and lighting, and render the animation to a video file."""

import bpy
from mathutils import Vector

# =============================
# 0. Reset scene
# =============================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# =============================
# 1. Components
# =============================
components = [
    ("User Device", (-5, 0, 0.3)),
    ("API Gateway", (-2, 0, 0.3)),
    ("Load Balancer", (0, 0, 0.3)),
    ("Content Service", (2, 1, 0.3)),
    ("Database", (2, -1, 0.3)),
    ("CDN / Edge", (5, 0, 0.3)),
    ("Analytics", (0, 2.5, 0.3))
]

# =============================
# 2. Materials
# =============================
def create_material(name, color, metallic=0.1, roughness=0.3):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = (*color,1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

floor_mat = create_material("Floor", (0.05,0.05,0.06), 0.0, 0.6)
comp_mat  = create_material("Comp",  (0.2,0.6,1.0))
arrow_mat = create_material("Arrow", (1,0.5,0))
text_mat  = create_material("Text",  (1,1,1))

# =============================
# 3. Floor
# =============================
bpy.ops.mesh.primitive_plane_add(size=50, location=(0,0,0))
floor = bpy.context.object
floor.data.materials.append(floor_mat)

# =============================
# 4. Components (cubes) + labels
# =============================
comp_objs = []
label_objs = []

for name, loc in components:
    bpy.ops.mesh.primitive_cube_add(location=(loc[0], loc[1], 0.15))
    comp = bpy.context.object
    comp.scale = (0.7,0.7,0)  # start flat
    comp.data.materials.append(comp_mat)
    # Bevel
    b = comp.modifiers.new("Bevel","BEVEL")
    b.width = 0.05
    b.segments = 6
    comp_objs.append(comp)

    # Label text
    bpy.ops.object.text_add(location=(loc[0], loc[1], 0.9))
    txt = bpy.context.object
    txt.data.body = name
    txt.data.size = 0.25
    txt.data.materials.append(text_mat)
    txt.rotation_euler = (0,0,0)
    txt.hide_render = True
    txt.keyframe_insert("hide_render", frame=1)
    txt.hide_render = False
    txt.keyframe_insert("hide_render", frame=15)
    label_objs.append(txt)

# =============================
# 5. Animate components popping up
# =============================
for i, comp in enumerate(comp_objs):
    start = 20 + i*10
    peak  = start + 8
    settle= start + 14
    h = 1.0  # cube height

    comp.scale.z = 0
    comp.keyframe_insert("scale", frame=start)

    comp.scale.z = h*1.05
    comp.keyframe_insert("scale", frame=peak)

    comp.scale.z = h
    comp.keyframe_insert("scale", frame=settle)

    for fcu in comp.animation_data.action.fcurves:
        for kp in fcu.keyframe_points:
            kp.interpolation = 'BEZIER'

# =============================
# 6. Arrows (edges) between components
# =============================
connections = [
    (0,1),(1,2),(2,3),(2,4),(3,5),(4,5),(2,6)
]

for idx, (start_idx,end_idx) in enumerate(connections):
    start = Vector(comp_objs[start_idx].location)
    end   = Vector(comp_objs[end_idx].location)
    mid = (start + end)/2
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.05, depth=(end-start).length, location=mid)
    arrow = bpy.context.object
    arrow.data.materials.append(arrow_mat)
    # rotate arrow to face
    direction = end - start
    arrow.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    arrow.scale = (1,1,1)
    # animate arrow appearing
    arrow.scale.z = 0
    arrow.keyframe_insert("scale", frame=40 + idx*10)
    arrow.scale.z = 1
    arrow.keyframe_insert("scale", frame=50 + idx*10)
    for fcu in arrow.animation_data.action.fcurves:
        for kp in fcu.keyframe_points:
            kp.interpolation = 'BEZIER'

# =============================
# 7. Camera (cinematic)
# =============================
bpy.ops.object.camera_add(location=(-10,-10,7))
cam = bpy.context.object
scene.camera = cam

target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (0,0,0.5)
track = cam.constraints.new(type="TRACK_TO")
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

# Camera animation
cam.keyframe_insert("location", frame=20)
cam.location = (12,-12,10)
cam.keyframe_insert("location", frame=100)
cam.location = (0,-20,12)
cam.keyframe_insert("location", frame=180)

# =============================
# 8. Lighting (studio-quality)
# =============================
def add_light(loc, energy, size=2):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object
    l.data.energy = energy
    l.data.size = size

add_light((12,-12,10), 1800)
add_light((-12,-12,8), 800)
add_light((0,12,15), 600)

# =============================
# 9. Render settings
# =============================
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 128
scene.eevee.use_soft_shadows = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 200
scene.render.filepath = "/tmp/step5_netflix_system.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'

# =============================
# 10. Render
# =============================
bpy.ops.render.render(animation=True)
