"""Locate existing waist texture contamination; read-only source/model inspection."""
from pathlib import Path
import bpy, json, hashlib
import numpy as np
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
path=ROOT/'01_游戏开发/Models/首批角色_v01_20261111/角色_纸团_整合_v01_20261111.blend'
source=ROOT/'01_游戏开发/Imports/角色源仓_20261111/source_checkout/deliverables/卡通人物_搬运走路.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(path)
bpy.ops.wm.open_mainfile(filepath=str(path))
ob=bpy.data.objects['mesh_zhituan']; me=ob.data
vertex_count=len(me.vertices)
uv=me.uv_layers.active.data
uv_array=np.empty(len(uv)*2,dtype=np.float32);uv.foreach_get('uv',uv_array)
source_uv=uv_array.copy()
textures={}
for i,mat in enumerate(me.materials):
    tex=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if mat and mat.use_nodes else None
    if tex:
        arr=np.empty(tex.size[0]*tex.size[1]*4,dtype=np.float32);tex.pixels.foreach_get(arr)
        textures[i]=(tex,arr.reshape((tex.size[1],tex.size[0],4)))
def sample(mi,t):
    if mi not in textures:return None
    image,arr=textures[mi];x=min(arr.shape[1]-1,max(0,int(t[0]*arr.shape[1])));y=min(arr.shape[0]-1,max(0,int(t[1]*arr.shape[0])))
    return [round(float(x),6) for x in arr[y,x,:3]]
def is_orange(rgb):
    if rgb is None:return False
    r,g,b=rgb
    return r>.30 and r>g*1.18 and g>b*1.25 and r-b>.12
groups={g.index:g.name for g in ob.vertex_groups}
def dominant(v):
    g=max(v.groups,key=lambda g:g.weight,default=None)
    return groups[g.group] if g else ''
faces=[];candidates=[]
for poly in me.polygons:
    verts=[me.vertices[i] for i in poly.vertices]
    center=sum((ob.matrix_world@v.co for v in verts),Vector())/len(verts)
    bone=[dominant(v) for v in verts]
    if not (.10<center.z<.43 and abs(center.x)>.10):continue
    if not all(b in ('hips','spine','chest','thigh_L','thigh_R') for b in bone):continue
    uvs=[uv[i].uv.copy() for i in poly.loop_indices]
    center_uv=sum(uvs,Vector((0,0)))/len(uvs)
    probes=[center_uv]+[center_uv*.5+p*.5 for p in uvs]
    rgb=[sample(poly.material_index,p) for p in probes]
    ratio=sum(is_orange(c) for c in rgb)/len(rgb)
    record={'face_index':poly.index,'vertices':list(poly.vertices),'material_index':poly.material_index,
            'center_rest_m':[round(v,6) for v in center], 'normal_rest':list(poly.normal),
            'dominant_bones':bone,'uvs':[[round(c,7) for c in p] for p in uvs],
            'uv_bbox_2048_top_left_pixels':[round(min(p.x for p in uvs)*2048),round((1-max(p.y for p in uvs))*2048),round(max(p.x for p in uvs)*2048),round((1-min(p.y for p in uvs))*2048)],
            'rgb_probes':rgb,'orange_probe_fraction':ratio}
    candidates.append(record)
    if ratio>=.5:faces.append(record)
result={'source_model':str(path.relative_to(ROOT)),'source_model_sha256':before,
        'method':'Read existing UVs and original image texels on rest-space lateral garment faces. Orange filter is diagnostic, not an automatic repair mask.',
        'image_files':[{'material_index':i,'image':im.name,'filepath':im.filepath,'size':list(im.size)} for i,(im,_) in textures.items()],
        'garment_candidate_face_count':len(candidates),'orange_candidate_face_count':len(faces),
        'orange_faces':faces,'all_lateral_garment_faces':candidates,
        'rest_geometry_note':'Positions/UVs sampled without pose evaluation; contamination present in rest-space material data and does not require skinning.',
        'source_file_unchanged':sha(path)==before}
if source.exists():
    source_sha=sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    original=next(o for o in bpy.context.scene.objects if o.type=='MESH')
    orig_uv=original.data.uv_layers.active.data
    arr=np.empty(len(orig_uv)*2,dtype=np.float32);orig_uv.foreach_get('uv',arr)
    result['upstream_comparison']={'source':str(source.relative_to(ROOT)),'sha256':source_sha,
        'same_uv_count':len(arr)==len(source_uv),'uv_max_absolute_difference':float(np.max(np.abs(arr-source_uv))) if len(arr)==len(source_uv) else None,
        'same_vertex_count':len(original.data.vertices)==vertex_count,
        'source_file_unchanged':sha(source)==source_sha}
    textures={}
    for i,mat in enumerate(original.data.materials):
        tex=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if mat and mat.use_nodes else None
        if tex:
            pixels=np.empty(tex.size[0]*tex.size[1]*4,dtype=np.float32);tex.pixels.foreach_get(pixels)
            textures[i]=(tex,pixels.reshape((tex.size[1],tex.size[0],4)))
    confirmed=[]
    for face in faces:
        p=sum((Vector(t) for t in face['uvs']),Vector((0,0)))/len(face['uvs'])
        rgb=sample(face['material_index'],p)
        if is_orange(rgb):confirmed.append({'face_index':face['face_index'],'source_rgb':rgb})
    result['upstream_comparison']['same_orange_on_original_4096_centroid_count']=len(confirmed)
    result['upstream_comparison']['original_4096_texel_evidence']=confirmed
out=HERE/'纸团侧腰材质定位_v01_20261111.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('WAIST_AUDIT',out,'orange_faces',len(faces),'garment_faces',len(candidates))
