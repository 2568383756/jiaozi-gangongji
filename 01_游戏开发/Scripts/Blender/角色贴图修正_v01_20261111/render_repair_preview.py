from pathlib import Path
import sys,json,math,hashlib
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE))
from garment_materials import apply
OUT=ROOT/'01_游戏开发/Models/角色贴图修正_v01_20261111';OUT.mkdir(parents=True,exist_ok=True)
report_path=OUT/'服装修正核验_v01_20261111.json'
report=json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def setup():
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
 try:
  pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
  for d in pref.devices:d.use=d.type!='CPU'
  s.cycles.device='GPU'
 except Exception:pass
 s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 s.render.resolution_x=1280;s.render.resolution_y=1280;s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.render.film_transparent=False
 world=bpy.data.worlds.new('RepairPreviewWorld');s.world=world;world.use_nodes=True
 world.node_tree.nodes.get('Background').inputs[0].default_value=(.55,.53,.48,1)
 world.node_tree.nodes.get('Background').inputs[1].default_value=.45
 for name,loc,energy,size in [('Key',(3,-4,5),450,4),('Fill',(-4,-2,3),160,4),('Rim',(2,3,4),180,3)]:
  dat=bpy.data.lights.new(name,'AREA');dat.energy=energy;dat.shape='DISK';dat.size=size
  ob=bpy.data.objects.new(name,dat);s.collection.objects.link(ob);ob.location=loc;aim(ob,(0,0,.5))
 data=bpy.data.cameras.new('RepairPreviewCamera');data.type='ORTHO'
 cam=bpy.data.objects.new('RepairPreviewCamera',data);s.collection.objects.link(cam);s.camera=cam
 return s,cam
def render(s,cam,name,loc,target,scale):
 cam.location=loc;aim(cam,target);cam.data.ortho_scale=scale
 s.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 if '--yintao-only' in sys.argv and cid!='yintao':continue
 src=ROOT/f'01_游戏开发/Models/首批角色_v01_20261111/角色_{label}_整合_v01_20261111.blend'
 before=hashlib.sha256(src.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(src))
 rig=bpy.data.objects['rig_'+cid];mesh=bpy.data.objects['mesh_'+cid]
 rig.animation_data.action=bpy.data.actions[cid+'_Work'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
 bpy.context.scene.frame_set(16);bpy.context.view_layer.update();s,cam=setup()
 if cid=='zhituan':render(s,cam,'预览_纸团侧腰_修正前_v01_20261111.png',(3,-.01,.43),(0,-.03,.29),.67)
 result=apply(mesh,cid);bpy.context.view_layer.update()
 if cid=='zhituan':
  render(s,cam,'预览_纸团侧腰_修正后_v01_20261111.png',(3,-.01,.43),(0,-.03,.29),.67)
  render(s,cam,'预览_纸团正面_修正后_v01_20261111.png',(0,-4,.65),(0,0,.60),1.42)
 else:
  render(s,cam,'预览_印桃背侧_核对_v01_20261111.png',(3,1.2,.55),(0,0,.4),.85)
  render(s,cam,'预览_印桃正面_修正后_v01_20261111.png',(0,-4,.65),(0,0,.60),1.42)
 result['input_sha256']=before;result['source_file_unchanged']=hashlib.sha256(src.read_bytes()).hexdigest()==before
 report[cid]=result
(OUT/'服装修正核验_v01_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
