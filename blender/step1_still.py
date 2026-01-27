# blender/step1_still.py

import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Add cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object

# Material
mat = bpy.data.materials.new(name="CubeMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.2, 0.6, 1.0, 1)
bsdf.inputs["Roughness"].default_value = 0.4
cube.data.materials.append(mat)

# Camera
bpy.ops.object.camera_add(location=(5, -5, 4))
camera = bpy.context.object
camera.rotation_euler = (1.1, 0, 0.8)
bpy.context.scene.camera = camera

# Key Light
bpy.ops.object.light_add(type='AREA', location=(4, -4, 5))
key = bpy.context.object
key.data.energy = 800

# Fill Light
bpy.ops.object.light_add(type='POINT', location=(-4, -2, 3))
fill = bpy.context.object
fill.data.energy = 300

# World background (contrast!)
world = bpy.context.scene.world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 0.8

# Render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.filepath = '/tmp/step1.png'
scene.render.resolution_x = 800
scene.render.resolution_y = 600

bpy.ops.render.render(write_still=True)
