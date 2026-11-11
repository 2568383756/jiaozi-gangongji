"""Read-only geometry diagnostics for the pre-hand-repair v02 characters."""
from pathlib import Path
import bpy,json,hashlib,math
from mathutils import Vector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
report={'version':'v01_20261111','scope':'Existing v02 hands only; no model or texture changes.',
        'note':'A C-shaped visible silhouette is not equivalent to a topological hole. Boundary counts of bone-weight subsets include intentional wrist seams.',
        'characters':{}}
def rounded(v):return [round(float(x),6) for x in v]
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 path=ROOT/f'01_游戏开发/Models/首批角色_v02_20261111/角色_{label}_整合_v02_20261111.blend'
 before=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path))
 rig=bpy.data.objects['rig_'+cid];mesh=bpy.data.objects['mesh_'+cid]
 rig.animation_data.action=bpy.data.actions[cid+'_Work']
 if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
 names={g.index:g.name for g in mesh.vertex_groups}
 masks={s:[v.index for v in mesh.data.vertices if v.groups and names[max(v.groups,key=lambda g:g.weight).group]=='hand_'+s] for s in ('L','R')}
 samples=[]
 for frame in (1,8,16,24,31):
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
  ob=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ob.to_mesh()
  points=[ob.matrix_world@v.co for v in me.vertices]
  row={'frame':frame,'hands':{}}
  for side,ids in masks.items():
   ps=[points[i] for i in ids];zmin=min(p.z for p in ps);low=[points[i] for i in ids if points[i].z<=zmin+.003]
   hand=rig.pose.bones['hand_'+side];axis=(rig.matrix_world.to_3x3()@(hand.tail-hand.head)).normalized()
   near_ids=[i for i in ids if points[i].z<=zmin+.003]
   row['hands'][side]={'dominant_hand_vertex_count':len(ids),
    'bounds_xyz':[[round(min(p[k] for p in ps),6),round(max(p[k] for p in ps),6)] for k in range(3)],
    'wrist':rounded(rig.matrix_world@hand.head),'bone_tip':rounded(rig.matrix_world@hand.tail),
    'bone_longitudinal_axis_world':rounded(axis),'bone_axis_angle_to_forward_degrees':round(math.degrees(axis.angle(Vector((0,-1,0)))),3),
    'lowest_support_band_m':.003,'near_bottom_vertex_count':len(low),
    'near_bottom_vertex_ids':near_ids,'near_bottom_xy_span':rounded((max(p.x for p in low)-min(p.x for p in low),max(p.y for p in low)-min(p.y for p in low))),
    'rig_has_finger_bones':any(('finger' in b.name or 'thumb' in b.name) for b in rig.data.bones)}
  samples.append(row);ob.to_mesh_clear()
 report['characters'][cid]={'file':str(path.relative_to(ROOT)),'sha256':before,'source_unchanged':hashlib.sha256(path.read_bytes()).hexdigest()==before,'samples':samples}
(HERE/'旧手部形状诊断_v01_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('HAND_DIAGNOSTIC_WRITTEN')
