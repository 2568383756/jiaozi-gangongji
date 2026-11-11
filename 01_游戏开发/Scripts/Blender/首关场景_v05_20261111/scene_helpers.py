"""Small Blender modeling helpers. All parented positions are local, meters, Z up."""
import bpy
import math
from mathutils import Vector


def linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + .055) / 1.055) ** 2.4


def rgba(h):
    return tuple(linear(int(h[i:i+2], 16)/255) for i in (0,2,4)) + (1,)


class SceneAPI:
    def __init__(self):
        self.current = None
        self.materials = {}
        palette = dict(wood='C58B42', wood_light='E5AD50', wood_dark='82532C',
                       paper='EBDAB7', paper_edge='C9B28B', ink='292726',
                       teal='4C9992', water='61B6B8', red='C45232',
                       stone='AE997A', roof='3F619A', metal='AA7B40', wet='C4D7CF')
        for name, color in palette.items():
            m = bpy.data.materials.new('MAT_' + name)
            m.use_nodes = True
            m.diffuse_color = rgba(color)
            bsdf = m.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value = rgba(color)
            bsdf.inputs['Roughness'].default_value = .78
            if 'Specular IOR Level' in bsdf.inputs:
                bsdf.inputs['Specular IOR Level'].default_value = .22
            if name == 'water':
                bsdf.inputs['Roughness'].default_value = .28
            else:
                noise = m.node_tree.nodes.new('ShaderNodeTexNoise')
                noise.inputs['Scale'].default_value = 48
                noise.inputs['Detail'].default_value = 1.5
                bump = m.node_tree.nodes.new('ShaderNodeBump')
                bump.inputs['Strength'].default_value = .09
                bump.inputs['Distance'].default_value = .012
                m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
                m.node_tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
            self.materials[name] = m
        self.font = None
        try:
            self.font = bpy.data.fonts.load('C:/Windows/Fonts/simkai.ttf')
        except RuntimeError:
            pass

    def collection(self, name):
        col = bpy.data.collections.get(name)
        if col is None:
            col = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(col)
        self.current = col
        return col

    def finish(self, ob, name, loc, mat=None, parent=None):
        ob.name = name
        for col in list(ob.users_collection):
            col.objects.unlink(ob)
        (self.current or bpy.context.scene.collection).objects.link(ob)
        ob.parent = parent
        ob.location = loc
        if mat is not None and hasattr(ob.data, 'materials'):
            ob.data.materials.append(self.materials[mat] if isinstance(mat, str) else mat)
        return ob

    def box(self, name, loc, size, mat, parent=None, bevel=.02):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.object
        for v in ob.data.vertices:
            v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        self.finish(ob, name, loc, mat, parent)
        if bevel:
            mod = ob.modifiers.new('Paper edge bevel', 'BEVEL')
            mod.width = min(bevel, min(size)*.2)
            mod.segments = 1
        return ob

    def cyl(self, name, loc, radius, depth, mat, parent=None, vertices=12, rotation=None):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
        ob = self.finish(bpy.context.object, name, loc, mat, parent)
        if rotation:
            ob.rotation_euler = rotation
        return ob

    def mesh(self, name, vertices, faces, mat, parent=None):
        me = bpy.data.meshes.new(name + '_mesh')
        me.from_pydata(vertices, [], faces); me.update()
        ob = bpy.data.objects.new(name, me)
        return self.finish(ob, name, (0,0,0), mat, parent)

    def empty(self, name, loc, parent=None, display='PLAIN_AXES', size=.12):
        ob = bpy.data.objects.new(name, None)
        ob.empty_display_type = display
        ob.empty_display_size = size
        return self.finish(ob, name, loc, parent=parent)

    def line(self, name, points, mat, radius=.006, parent=None):
        curve = bpy.data.curves.new(name + '_curve', 'CURVE')
        curve.dimensions = '3D'; curve.resolution_u = 1
        curve.bevel_depth = radius; curve.bevel_resolution = 0
        spl = curve.splines.new('POLY'); spl.points.add(len(points)-1)
        for p, co in zip(spl.points, points):
            p.co = (*co, 1)
        ob = bpy.data.objects.new(name, curve)
        return self.finish(ob, name, (0,0,0), mat, parent)

    def text(self, name, body, loc, size, mat, rotation=None, parent=None):
        curve = bpy.data.curves.new(name + '_font', 'FONT')
        curve.body = body; curve.size = size
        curve.align_x = 'CENTER'; curve.align_y = 'CENTER'
        curve.extrude = .001; curve.resolution_u = 2
        if self.font:
            curve.font = self.font
        ob = bpy.data.objects.new(name, curve)
        self.finish(ob, name, loc, mat, parent)
        if rotation:
            ob.rotation_euler = rotation
        # Convert glyphs to mesh: no font file dependency in delivered blend/GLB.
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.object.convert(target='MESH')
        return bpy.context.object

    def tex_plane(self, name, loc, size, image_path, parent=None, rotation=None):
        bpy.ops.mesh.primitive_plane_add(size=1)
        ob = bpy.context.object
        for v in ob.data.vertices:
            v.co.x *= size[0]; v.co.y *= size[1]
        self.finish(ob, name, loc, parent=parent)
        m = bpy.data.materials.new(name + '_image'); m.use_nodes = True
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(image_path), check_existing=True)
        tex.image.pack()
        m.node_tree.links.new(tex.outputs['Color'], m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
        ob.data.materials.append(m)
        if rotation:
            ob.rotation_euler = rotation
        return ob
