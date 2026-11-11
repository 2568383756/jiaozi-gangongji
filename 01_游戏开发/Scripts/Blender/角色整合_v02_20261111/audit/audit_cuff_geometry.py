import bpy,json
from pathlib import Path
R=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发')
results=[]
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'Models/首批角色_v01_20261111'/('角色_'+label+'_整合_v01_20261111.blend')),load_ui=False)
 rig=bpy.data.objects['rig_'+cid];mesh=bpy.data.objects['mesh_'+cid];rec={'id':cid,'arms':{}}
 for side in ('L','R'):
  name='forearm_'+side;bone=rig.data.bones[name];inv=bone.matrix_local.inverted();items=[]
  for v in mesh.data.vertices:
   dom=mesh.vertex_groups[max(v.groups,key=lambda g:g.weight).group].name
   if dom!=name:continue
   p=inv@v.co;items.append({'id':v.index,'xyz':[p.x,p.y-bone.length,p.z],'radius':(p.x*p.x+p.z*p.z)**.5})
  rec['arms'][side]={'bone_length':bone.length,'vertices':items,'bins':[]}
  for low,high in [(-1,-.08),(-.08,-.04),(-.04,-.02),(-.02,0),(0,.02),(.02,.04),(.04,.08),(.08,1)]:
   vals=[i for i in items if low<=i['xyz'][1]<high]
   if vals:rec['arms'][side]['bins'].append({'y_relative_wrist':[low,high],'count':len(vals),'radius':[min(i['radius'] for i in vals),max(i['radius'] for i in vals)]})
  print(cid,side,'length',bone.length,rec['arms'][side]['bins'],flush=True)
 results.append(rec)
(R/'Scripts/Blender/角色整合_v02_20261111/audit/cuff_geometry.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
