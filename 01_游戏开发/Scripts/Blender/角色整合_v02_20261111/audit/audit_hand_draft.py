import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发');DRAFT=R/'Models/首批角色_v02_20261111/work/hand_draft'
def box(lo,hi,matrix=Matrix.Identity(4)):
 p=[matrix@Vector((x,y,z)) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
 f=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
 return BVHTree.FromPolygons(p,f,all_triangles=False)
report=[]
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 bpy.ops.wm.open_mainfile(filepath=str(DRAFT/('角色_'+label+'_新手草稿.blend')),load_ui=False)
 mesh=bpy.data.objects['mesh_'+cid];rig=bpy.data.objects['rig_'+cid]
 for kind in ('Work','Carry'):
  action=bpy.data.actions[cid+'_DRAFT_'+kind];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
  ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();p=[ev.matrix_world@v.co for v in me.vertices]
  handids={v.index for v in me.vertices if mesh.vertex_groups[max(v.groups,key=lambda g:g.weight).group].name in ('hand_L','hand_R')}
  body=[tuple(t.vertices) for t in me.loop_triangles if not any(i in handids for i in t.vertices)];tree=BVHTree.FromPolygons(p,body,all_triangles=True)
  fixtures={'table':box((-.40,-.84,.275),(.40,-.24,.33)),'block':box((-.315,-.695,.330),(.315,-.245,.344)),'paper':box((-.30,-.68,.344),(.30,-.26,.350))} if kind=='Work' else {'carried_paper':box((-.21,-.30,0),(.21,.30,.006),rig.matrix_world@rig.pose.bones['HoldPoint'].matrix)}
  result={'character':cid,'pose':kind,'intersections':{}}
  for n,t in fixtures.items():
   hits=tree.overlap(t);result['intersections'][n]={'count':len(hits),'examples':[{'triangle':body[a],'xyz':[list(p[i]) for i in body[a]]} for a,b in hits[:2]]}
  report.append(result);print(cid,kind,{n:v['count'] for n,v in result['intersections'].items()},flush=True);ev.to_mesh_clear()
(DRAFT/'新手草稿身体与纸台碰撞.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
