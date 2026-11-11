import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发')
records=[]
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'Models/首批角色_v01_20261111'/('角色_'+label+'_整合_v01_20261111.blend')),load_ui=False)
 rig=bpy.data.objects['rig_'+cid];mesh=bpy.data.objects['mesh_'+cid];rig.data.pose_position='REST';bpy.context.view_layer.update()
 dominant={v.index:mesh.vertex_groups[max(v.groups,key=lambda g:g.weight).group].name for v in mesh.data.vertices}
 rec={'id':cid,'hands':{}}
 for side in ('L','R'):
  name='hand_'+side;bone=rig.data.bones[name];ids=[i for i,n in dominant.items() if n==name]
  handset=set(ids);polys=[p for p in mesh.data.polygons if any(i in handset for i in p.vertices)]
  mixed=[p for p in polys if not all(i in handset for i in p.vertices)]
  neighborids=sorted({i for p in mixed for i in p.vertices if i not in handset})
  local=[bone.matrix_local.inverted()@mesh.data.vertices[i].co for i in ids]
  sampleuvs=[]
  for p in polys[::max(1,len(polys)//100)]:
   if all(i in handset for i in p.vertices):sampleuvs.append(list(sum((mesh.data.uv_layers.active.data[j].uv for j in p.loop_indices),Vector((0,0)))/len(p.loop_indices)))
  rec['hands'][side]={'bone_head':list(bone.head_local),'bone_tail':list(bone.tail_local),'bone_matrix':[list(row) for row in bone.matrix_local],
   'vertex_count':len(ids),'hand_vertex_ids':ids,'remove_faces_if_any_hand':len(polys),'mixed_face_count':len(mixed),
   'boundary_nonhand_vertex_ids':neighborids,'neighbor_bones':list({dominant[i] for i in neighborids}),
   'local_bounds':[[min(p[k] for p in local),max(p[k] for p in local)] for k in range(3)],'uv_samples':sampleuvs}
 records.append(rec);print(cid,{s:{k:v for k,v in h.items() if k not in ('hand_vertex_ids','uv_samples','boundary_nonhand_vertex_ids')} for s,h in rec['hands'].items()},flush=True)
(R/'Scripts/Blender/角色整合_v02_20261111/audit/hand_regions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
