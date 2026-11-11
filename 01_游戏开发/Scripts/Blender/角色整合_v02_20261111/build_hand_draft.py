"""Authorized solid-hand preview; final outputs remain untouched."""
import sys, importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hand_integration import *

reports=[]
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'Models/首批角色_v01_20261111'/('角色_'+label+'_整合_v01_20261111.blend')),load_ui=False);bpy.context.preferences.filepaths.save_version=0
 rig=bpy.data.objects['rig_'+cid];mesh=bpy.data.objects['mesh_'+cid]
 hook=R/'Scripts/Blender/角色贴图修正_v01_20261111/garment_materials.py';spec=importlib.util.spec_from_file_location('garment_repair',hook);repair=importlib.util.module_from_spec(spec);spec.loader.exec_module(repair);repair.apply(mesh,cid)
 poses={}
 for name in ('Idle','CarryIdle'):
  activate(rig,bpy.data.actions[cid+'_'+name]);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();poses[name]={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
  if name=='CarryIdle':
   hold=rig.pose.bones['HoldPoint'].matrix.copy();hold.translation.y-=.070
 meta,info=replace_hands(mesh,rig,cid);targets={}
 for side in ('L','R'):
  target=bpy.data.objects.new('TEMP_NewHandTarget_'+side,None);bpy.context.scene.collection.objects.link(target);targets[side]=target
  c=rig.pose.bones['forearm_'+side].constraints.new('IK');c.name='TEMP_NewHandIK';c.target=target;c.chain_count=2;c.iterations=256;c.use_tail=True;c.mute=True
  rig.pose.bones['upper_arm_'+side].ik_stretch=0;rig.pose.bones['forearm_'+side].ik_stretch=0
 rec={'character_id':cid,'mesh_info':info,'poses':{}}
 for kind in ('Work','Carry'):
  a=bpy.data.actions.new(cid+'_DRAFT_'+kind);a.use_fake_user=True;a.slots.new(id_type='OBJECT',name=rig.name);activate(rig,a)
  assign(rig,poses['Idle' if kind=='Work' else 'CarryIdle'])
  if kind=='Work':
   if cid=='yintao':
    h=rig.pose.bones['hips'];m=h.matrix.copy();m.translation.y+=.03;h.matrix=m;bpy.context.view_layer.update()
   for side in ('L','R'):
    p=rig.pose.bones['upper_arm_'+side];m=p.matrix.copy();m.translation.y-=.025;p.matrix=m;bpy.context.view_layer.update()
   p=rig.pose.bones['head'];v=p.head.copy();p.matrix=Matrix.Translation(v)@Matrix.Rotation(-.14,4,'X')@Matrix.Translation(-v)@p.matrix;bpy.context.view_layer.update()
  geomrot=Quaternion((0,0,1),math.pi) if kind=='Work' else Quaternion((1,0,0),math.pi)
  rots={s:geomrot@meta[s]['correction'].to_quaternion().inverted() for s in ('L','R')}
  desired={s:Vector(((1 if s=='L' else -1)*(.17 if kind=='Work' else .19),-.277 if kind=='Work' else hold.translation.y+.28,.350 if kind=='Work' else hold.translation.z)) for s in ('L','R')}
  wrist={s:desired[s]-geomrot@Vector(meta[s]['palm_pad_center_local']) for s in ('L','R')}
  natural_arms(rig,wrist,rots)
  # HoldPoint is preserved exactly for the carry protocol, independently of new palm topology.
  if kind=='Carry':
   rig.pose.bones['HoldPoint'].matrix=hold
   rig.pose.bones['PalmCenter'].matrix=Matrix.Translation((desired['L']+desired['R'])*.5)
  for p in rig.pose.bones:
   for channel in ('location','rotation_quaternion','scale'):p.keyframe_insert(channel,frame=1,group=p.name)
  pp=posed_points(mesh);record={}
  for side in ('L','R'):
   ids=meta[side]['palm_pad_vertex_ids'];probe=meta[side]['contact_probe_vertex_id']
   record[side]={'pad_vertices':ids,'pad_center':list(sum((pp[i] for i in ids),Vector())/len(ids)),
    'probe_vertex_id':probe,'probe_xyz':list(pp[probe]),'wrist':list(rig.pose.bones['hand_'+side].head),
    'wrist_ik_error':(rig.pose.bones['hand_'+side].head-wrist[side]).length}
  rec['poses'][kind]=record
 for side in ('L','R'):
  rig.pose.bones['forearm_'+side].constraints.remove(rig.pose.bones['forearm_'+side].constraints['TEMP_NewHandIK']);bpy.data.objects.remove(targets[side],do_unlink=True)
 activate(rig,bpy.data.actions[cid+'_DRAFT_Work']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 bpy.ops.wm.save_as_mainfile(filepath=str(DRAFT/('角色_'+label+'_新手草稿.blend')))
 reports.append(rec);print('HAND_DRAFT_READY',cid,json.dumps(rec['poses'],ensure_ascii=False),flush=True)
(DRAFT/'新手草稿几何与锚点.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
