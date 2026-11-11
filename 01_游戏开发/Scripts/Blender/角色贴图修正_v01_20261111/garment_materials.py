"""Localized editable garment repair. No source atlas, vertices or weights changed.

Call apply(mesh, cid) after the character is normalized to 1.2 metres, before
export. Existing face slots/UVs remain untouched outside explicit garment zones.
New material uses packed BaseColor + tangent Normal images for glTF portability.
"""
import bpy, math, hashlib
import numpy as np
from mathutils import Vector

VERSION='v01_20261111'
ALLOWED={'hips','spine','chest'}

def _digest(mesh):
    m=mesh.data
    a=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',a)
    weights=[(v.index,tuple((g.group,round(g.weight,8)) for g in v.groups)) for v in m.vertices]
    return {'vertices':hashlib.sha256(a.tobytes()).hexdigest(),
            'weights':hashlib.sha256(repr(weights).encode()).hexdigest(),
            'vertex_count':len(m.vertices),'polygon_count':len(m.polygons)}

def _image(name,array,colorspace):
    im=bpy.data.images.get(name)
    if im:return im
    im=bpy.data.images.new(name,width=array.shape[1],height=array.shape[0],alpha=True)
    im.colorspace_settings.name=colorspace
    im.pixels.foreach_set(array.astype(np.float32).ravel());im.update();im.pack()
    return im

def _material(kind):
    name=f'MAT_GarmentRepair_{kind}_{VERSION}'
    material=bpy.data.materials.get(name)
    if material:return material
    size=256; rng=np.random.default_rng(61111)
    noise=rng.normal(0,.002,(size,size)).astype(np.float32)
    # Very subtle paper fibre; no woven grid, grime or atlas-like skin residue.
    for _ in range(3):noise=(noise+np.roll(noise,1,0)+np.roll(noise,-1,0)+np.roll(noise,1,1)+np.roll(noise,-1,1))/5
    base=np.array({'olive':(.565,.525,.185),'red':(.72,.135,.075),'belt':(.93,.815,.615)}[kind],dtype=np.float32)
    rgba=np.ones((size,size,4),dtype=np.float32)
    rgba[:,:,:3]=np.clip(base[None,None,:]+noise[:,:,None],0,1)
    normal=np.ones((size,size,4),dtype=np.float32)
    gy,gx=np.gradient(noise)
    normal[:,:,0]=.5-gx*.8;normal[:,:,1]=.5-gy*.8;normal[:,:,2]=1.
    col=_image(f'TEX_GarmentRepair_{kind}_BaseColor_{VERSION}',rgba,'sRGB')
    nor=_image(f'TEX_GarmentRepair_Paper_Normal_{VERSION}',normal,'Non-Color')
    material=bpy.data.materials.new(name);material.use_nodes=True
    nodes=material.node_tree.nodes;nodes.clear();links=material.node_tree.links
    out=nodes.new('ShaderNodeOutputMaterial');bsdf=nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value=.83
    bsdf.inputs['Metallic'].default_value=0
    bsdf.inputs['Specular IOR Level'].default_value=.23
    tex=nodes.new('ShaderNodeTexImage');tex.image=col;tex.extension='REPEAT'
    norm_tex=nodes.new('ShaderNodeTexImage');norm_tex.image=nor;norm_tex.extension='REPEAT'
    norm=nodes.new('ShaderNodeNormalMap');norm.inputs['Strength'].default_value=.12
    links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    links.new(norm_tex.outputs['Color'],norm.inputs['Color']);links.new(norm.outputs['Normal'],bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    material['repair_scope']='Geometric garment zone only; source atlas is unchanged'
    return material

def apply(mesh,cid):
    before=_digest(mesh)
    if cid not in ('zhituan','yintao'):
        return {'version':VERSION,'character':cid,'changed_faces':0,'geometry_weights_unchanged':True}
    if mesh.get('garment_repair_version')==VERSION:
        return {'version':VERSION,'character':cid,'already_applied':True}
    names={g.index:g.name for g in mesh.vertex_groups}
    def dominant(vertex):
        if not vertex.groups:return ''
        return names[max(vertex.groups,key=lambda g:g.weight).group]
    uv=mesh.data.uv_layers.active.data
    original_texels={}
    for i,mat in enumerate(mesh.data.materials):
        if not mat or not mat.node_tree:continue
        im=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
        if im:
            px=np.empty(im.size[0]*im.size[1]*4,dtype=np.float32);im.pixels.foreach_get(px)
            original_texels[i]=px.reshape((im.size[1],im.size[0],4))
    def front_color(face):
        arr=original_texels.get(face.material_index)
        if arr is None:return (0,0,0)
        t=sum((uv[i].uv for i in face.loop_indices),Vector((0,0)))/len(face.loop_indices)
        return arr[min(arr.shape[0]-1,max(0,int(t.y*arr.shape[0]))),min(arr.shape[1]-1,max(0,int(t.x*arr.shape[1]))),:3]
    indices={}
    cloth='olive' if cid=='zhituan' else 'red'
    for kind in (cloth,'belt'):
        mat=_material(kind)
        mesh.data.materials.append(mat);indices[kind]=len(mesh.data.materials)-1
    changes=[]
    for face in mesh.data.polygons:
        verts=[mesh.data.vertices[i] for i in face.vertices]
        if not all(dominant(v) in ALLOWED for v in verts):continue
        center=sum((v.co for v in verts),Vector())/len(verts)
        x,y,z=center
        # Whole cloth panels, not an orange-colour mask. Texture colour is read
        # ONLY to protect pale lapels within their small front geometric zone.
        # Original images are never edited or copied into a painted replacement.
        zmin=min(v.co.z for v in verts);zmax=max(v.co.z for v in verts)
        rgb=front_color(face)
        pale_lapel=rgb[0]>.80 and rgb[1]>.63 and rgb[2]>.39
        if cid=='zhituan':
            lateral=.132<z<.418
            protect=(y<-.19 and z<.254) or (y<-.145 and z>.303 and pale_lapel) or (y<-.11 and z>.400)
            # Ring vertices lie inside these measured bounds. Requiring every
            # vertex excludes robe triangles spanning above/below the belt.
            belt=zmin>=.245 and zmax<=.305 and .25<z<.305
        else:
            lateral=.185<z<.478
            protect=(y<-.13 and abs(x)<.09 and .21<z<.40) or (y<-.145 and z>.353 and pale_lapel) or (y<-.11 and z>.455)
            belt=zmin>=.289 and zmax<=.362 and .292<z<.362
        if protect:continue
        if not (lateral or belt):continue
        kind='belt' if belt else cloth
        old=face.material_index;face.material_index=indices[kind]
        # Local metres give consistent paper scale. Topology/weights stay fixed.
        for loop_index in face.loop_indices:
            p=mesh.data.vertices[mesh.data.loops[loop_index].vertex_index].co
            u=math.atan2(p.x,-p.y)/(2*math.pi)+.5
            uv[loop_index].uv=(u*2.,p.z*4.)
        changes.append({'face_index':face.index,'zone':kind,'previous_material_index':old,
                        'rest_center':[round(v,6) for v in center]})
    after=_digest(mesh)
    if before!=after:raise RuntimeError('Garment repair unexpectedly changed mesh geometry or weights')
    mesh['garment_repair_version']=VERSION
    mesh['garment_repair_face_count']=len(changes)
    return {'version':VERSION,'character':cid,'changed_faces':len(changes),
            'cloth_faces':sum(x['zone']==cloth for x in changes),
            'belt_faces':sum(x['zone']=='belt' for x in changes),
            'changes':changes,'geometry_weights_unchanged':True,
            'source_atlas_edited':False,'before':before,'after':after}
