import bpy
import math

# 0. Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Helper functions
def create_box(name, location, color):
    bpy.ops.mesh.primitive_cube_add(size=1.5, location=location)
    obj = bpy.context.object
    obj.name = name

    # Assign material
    mat = bpy.data.materials.new(name=f"{name}_mat")
    mat.diffuse_color = (*color, 1)
    obj.data.materials.append(mat)
    return obj

def add_text(text, location):
    bpy.ops.object.text_add(location=location)
    txt = bpy.context.object
    txt.data.body = text
    txt.data.size = 0.5
    return txt

def create_arrow(start, end):
    # Create cylinder (shaft)
    import mathutils
    direction = mathutils.Vector(end) - mathutils.Vector(start)
    length = direction.length
    midpoint = mathutils.Vector(start) + direction/2

    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.1, depth=length, location=midpoint
    )
    arrow = bpy.context.object

    # Rotate to align with direction
    arrow_vector = mathutils.Vector((0, 0, 1))
    rot_quat = arrow_vector.rotation_difference(direction)
    arrow.rotation_mode = 'QUATERNION'
    arrow.rotation_quaternion = rot_quat

    # Add material
    mat = bpy.data.materials.new(name="Arrow_mat")
    mat.diffuse_color = (1, 1, 0, 1)  # Yellow
    arrow.data.materials.append(mat)

    return arrow

# 2. Create boxes
boxes = [
    ("API", (-3, 0, 0), (0.2, 0.6, 1.0)),     # Blue
    ("Worker", (0, 0, 0), (0.8, 0.4, 0.2)),    # Orange
    ("DB", (3, 0, 0), (0.4, 1.0, 0.4)),        # Green
]

objs = []
for name, loc, color in boxes:
    obj = create_box(name, loc, color)
    add_text(name, (loc[0], loc[1], 1.5))
    objs.append(obj)

# 3. Animate boxes (pop + small rotation)
for i, obj in enumerate(objs):
    start_frame = 1 + i * 20
    end_frame = 20 + i * 20
    
    # Scale animation
    obj.scale = (0, 0, 0)
    obj.keyframe_insert(data_path="scale", frame=start_frame)
    obj.scale = (1.1, 1.1, 1.1)
    obj.keyframe_insert(data_path="scale", frame=start_frame + 5)
    obj.scale = (1, 1, 1)
    obj.keyframe_insert(data_path="scale", frame=end_frame)
    
    # Small rotation
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", frame=start_frame)
    obj.rotation_euler = (0, 0, math.radians(10))
    obj.keyframe_insert(data_path="rotation_euler", frame=end_frame)

# 4. Create arrows (connections)
connections = [(objs[0], objs[1]), (objs[1], objs[2])]
arrow_objs = []
for start, end in connections:
    arrow = create_arrow(start.location, end.location)
    arrow_objs.append(arrow)

# 5. Camera setup (fit all objects)
# Calculate bounding box center
min_x = min(obj.location.x for obj in objs)
max_x = max(obj.location.x for obj in objs)
center_x = (min_x + max_x) / 2
center_y = 0
center_z = 1

bpy.ops.object.camera_add(location=(center_x, -12, 6))
cam = bpy.context.object
bpy.context.scene.camera = cam

# Track center object (Worker)
constraint = cam.constraints.new(type='TRACK_TO')
constraint.target = objs[1]
constraint.track_axis = 'TRACK_NEGATIVE_Z'
constraint.up_axis = 'UP_Y'

# 6. Lighting (3-point)
# Key light
bpy.ops.object.light_add(type='AREA', location=(6, -6, 6))
key = bpy.context.object
key.data.energy = 1500

# Fill light
bpy.ops.object.light_add(type='AREA', location=(-6, -6, 4))
fill = bpy.context.object
fill.data.energy = 800

# Back light
bpy.ops.object.light_add(type='AREA', location=(0, 6, 6))
back = bpy.context.object
back.data.energy = 500

# 7. Render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 64
scene.eevee.use_soft_shadows = True
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.frame_start = 1
scene.frame_end = 100
scene.render.fps = 30

scene.render.filepath = '/tmp/step3_demo_arrows.mp4'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'

# 8. Render animation
bpy.ops.render.render(animation=True)
