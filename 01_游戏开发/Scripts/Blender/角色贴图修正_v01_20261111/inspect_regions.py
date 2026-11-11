from pathlib import Path
import bpy, json, numpy as np
from mathutils import Vector
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
out={}
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'01_游戏开发/Models/首批角色_v01_20261111/角色_{label}_整合_v01_20261111.blend'))
 ob=bpy.data.objects['mesh_'+cid];me=ob.data;uv=me.uv_layers.active.data
 names={g.index:g.name for g in ob.vertex_groups}
 images={}
 for i,mat in enumerate(me.materials):
  tex=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
  if tex:
   px=np.empty(tex.size[0]*tex.size[1]*4,dtype=np.float32);tex.pixels.foreach_get(px)
   images[i]=px.reshape((tex.size[1],tex.size[0],4))
 faces=[]
 parents=list(range(len(me.vertices)))
 def find(x):
  while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
  return x
 for edge in me.edges:
  a,b=map(find,edge.vertices)
  if a!=b:parents[b]=a
 for p in me.polygons:
  vs=[me.vertices[i] for i in p.vertices]
  bones=[names[max(v.groups,key=lambda g:g.weight).group] for v in vs]
  if not all(b in ('hips','spine','chest','thigh_L','thigh_R') for b in bones):continue
  c=sum((ob.matrix_world@v.co for v in vs),Vector())/len(vs)
  t=sum((uv[i].uv for i in p.loop_indices),Vector((0,0)))/len(p.loop_indices)
  arr=images.get(p.material_index);rgb=[]
  if arr is not None:
   rgb=[round(float(k),4) for k in arr[min(arr.shape[0]-1,max(0,int(t.y*arr.shape[0]))),min(arr.shape[1]-1,max(0,int(t.x*arr.shape[1]))),:3]]
  faces.append({'f':p.index,'component':find(p.vertices[0]),'z_range':[round(min(v.co.z for v in vs),6),round(max(v.co.z for v in vs),6)],'center':[round(v,5) for v in c],'rgb':rgb,'bones':bones,'normal':list(p.normal),'uv':[round(v,6) for v in t]})
 out[cid]=faces
(HERE/'服装区域面样本_v01_20261111.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
