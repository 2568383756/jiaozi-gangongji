import bpy,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
OUT=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发/Models/首批角色_v01_20261111')
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.85
 return m

def box(name,loc,size,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name
 for v in o.data.vertices:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
 o.data.materials.append(material);bevel=o.modifiers.new('soft paper edge','BEVEL');bevel.width=.008;bevel.segments=2
 return o

def setup(res=(1400,660),ortho=4.5,pos=(0,-8,.62),target=(0,0,.62)):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
 try:
  prefs=bpy.context.preferences.addons['cycles'].preferences
  for backend in ('OPTIX','CUDA'):
   try:prefs.compute_device_type=backend;prefs.get_devices()
   except Exception:continue
   if any(d.type!='CPU' for d in prefs.devices):
    for d in prefs.devices:d.use=d.type!='CPU'
    s.cycles.device='GPU';break
 except Exception:pass
 s.render.resolution_x=res[0];s.render.resolution_y=res[1];s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.render.film_transparent=False
 s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 w=bpy.data.worlds.new('Validation neutral studio');s.world=w;w.use_nodes=True
 w.node_tree.nodes['Background'].inputs['Color'].default_value=(.55,.53,.49,1)
 w.node_tree.nodes['Background'].inputs['Strength'].default_value=.40
 ground=mat('Validation ground',(.65,.62,.56));box('VALIDATION_Ground',(0,0,-.04),(15,15,.08),ground)
 for name,loc,energy,size in [('Key',(-3,-4,5),280,4),('Fill',(4,-1,3),125,3),('Rim',(0,3,4),180,3)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size
  o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
 cam=bpy.data.cameras.new('Validation camera');ob=bpy.data.objects.new('Validation camera',cam);s.collection.objects.link(ob)
 ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();cam.type='ORTHO';cam.ortho_scale=ortho;s.camera=ob
 return s

def load(cid,label):
 path=OUT/('角色_'+label+'_整合_v01_20261111.blend')
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):
  dst.collections=['CHAR_'+cid];dst.actions=[n for n in src.actions if n.startswith(cid+'_')]
 col=dst.collections[0];bpy.context.scene.collection.children.link(col)
 root=next(o for o in col.all_objects if o.get('character_id')==cid)
 rig=next(o for o in col.all_objects if o.type=='ARMATURE');mesh=next(o for o in col.all_objects if o.type=='MESH')
 return root,rig,mesh

def action(rig,name):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]

def duplicate(root,rig,mesh,suffix):
 col=bpy.context.scene.collection
 nr=root.copy();nr.name=root.name+suffix;col.objects.link(nr)
 ar=rig.copy();ar.data=rig.data.copy();ar.parent=nr;col.objects.link(ar)
 me=mesh.copy();me.parent=ar;col.objects.link(me)
 for mod in me.modifiers:
  if mod.type=='ARMATURE':mod.object=ar
 return nr,ar,me

for cid,label in ([] if '--work-only' in sys.argv else [('zhituan','纸团'),('yintao','印桃')]):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 root,rig,mesh=load(cid,label);rig.data.pose_position='REST'
 sets=[(root,rig,mesh)]+[duplicate(root,rig,mesh,'_View'+str(i)) for i in (1,2)]
 for index,(r,a,m) in enumerate(sets):r.location.x=(index-1)*1.4;r.rotation_euler.z=(0,math.pi/2,math.pi)[index];a.data.pose_position='REST'
 s=setup();s.render.filepath=str(OUT/('预览_'+label+'_三视图_v01_20261111.png'))
 bpy.ops.render.render(write_still=True);print('RENDERED',s.render.filepath,flush=True)
for clip,label in ([('Work','双人通用加工示意')] if '--work-only' in sys.argv else [('CarryIdle','双人持纸验证'),('Work','双人通用加工示意')]):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 rigs=[]
 for index,(cid,charlabel) in enumerate([('zhituan','纸团'),('yintao','印桃')]):
  r,a,m=load(cid,charlabel);r.location.x=(-.78,.78)[index];action(a,cid+'_'+clip);rigs.append(a)
 bpy.context.scene.frame_set(1 if clip=='CarryIdle' else 8);bpy.context.view_layer.update()
 if clip=='CarryIdle':
  paper=mat('VALIDATION unprinted paper',(.80,.73,.56))
  for index,a in enumerate(rigs):
   o=box('VALIDATION_Paper_'+str(index),(0,0,0),(.42,.60,.006),paper)
   for v in o.data.vertices:v.co.z+=.003
   o.matrix_world=a.matrix_world@a.pose.bones['HoldPoint'].matrix
 else:
  ruler=mat('VALIDATION height reference',(.21,.24,.22))
  box('REFERENCE_065m_Ruler',(1.55,.08,.325),(.014,.014,.65),ruler)
  for z in (0,.65):box('REFERENCE_Height_Tick',(1.55,.08,z),(.13,.025,.012),ruler)
  d=bpy.data.curves.new('Height caption','FONT');d.body='0.65 m';d.size=.09;d.align_x='CENTER'
  o=bpy.data.objects.new('REFERENCE_065m_Label',d);bpy.context.scene.collection.objects.link(o)
  o.location=(1.55,.04,.71);o.rotation_euler=(math.pi/2,0,0);d.materials.append(ruler)
 s=setup((1280,900),3.8,(2.3,-5.5,2.6),(0,-.12,.62))
 s.render.filepath=str(OUT/('预览_'+label+'_v01_20261111.png'));bpy.ops.render.render(write_still=True)
 print('RENDERED',s.render.filepath,flush=True)
