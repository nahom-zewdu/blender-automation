import bpy
import math

# 0. Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Helper functions
def create_box(name, location, color):
    # Add cube
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
    obj.scale = (1.1, 1.1, 1.1)  # overshoot
    obj.keyframe_insert(data_path="scale", frame=start_frame + 5)
    obj.scale = (1, 1, 1)
    obj.keyframe_insert(data_path="scale", frame=end_frame)
    
    # Small rotation
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", frame=start_frame)
    obj.rotation_euler = (0, 0, math.radians(10))
    obj.keyframe_insert(data_path="rotation_euler", frame=end_frame)

# 4. Camera setup
bpy.ops.object.camera_add(location=(0, -8, 4))
cam = bpy.context.object
bpy.context.scene.camera = cam

# Track center object
constraint = cam.constraints.new(type='TRACK_TO')
constraint.target = objs[1]  # Worker in the center
constraint.track_axis = 'TRACK_NEGATIVE_Z'
constraint.up_axis = 'UP_Y'

# 5. Lighting (3-point)
# Key light
bpy.ops.object.light_add(type='AREA', location=(5, -5, 5))
key = bpy.context.object
key.data.energy = 1500

# Fill light
bpy.ops.object.light_add(type='AREA', location=(-5, -5, 3))
fill = bpy.context.object
fill.data.energy = 800

# Back light
bpy.ops.object.light_add(type='AREA', location=(0, 5, 5))
back = bpy.context.object
back.data.energy = 500

# 6. Render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 64
scene.eevee.use_soft_shadows = True
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.frame_start = 1
scene.frame_end = 80
scene.render.fps = 30

scene.render.filepath = '/tmp/step3_demo.mp4'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'

# 7. Render animation
bpy.ops.render.render(animation=True)
