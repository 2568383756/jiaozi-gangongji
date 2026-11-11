import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发');results=[]
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'Models/首批角色_v01_20261111'/('角色_'+label+'_整合_v01_20261111.blend')),load_ui=False)
 old=bpy.data.objects['mesh_'+cid].data;normals=[tuple(n.vector) for n in old.corner_normals];copy=old.copy()
 copy.normals_split_custom_set(normals)
 error=max((copy.corner_normals[i].vector-Vector(n)).length for i,n in enumerate(normals))
 rec={'character_id':cid,'unchanged_topology_reencoding_max_vector_error':error,'max_angle_degrees':math.degrees(2*math.asin(min(1,error*.5))),
  'source_encoding':old.attributes['custom_normal'].data_type,'method':'Copy the entire untouched source mesh and re-encode its own decoded corner normals; geometry/topology/UV/weights are unchanged.'}
 results.append(rec);print(rec,flush=True)
(R/'Scripts/Blender/角色整合_v02_20261111/audit/法线重编码量化基准_v01_20261111.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
