import bpy,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
OUT=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发/Models/首批角色_v02_20261111')
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
  for backend in ('CUDA',):
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
 path=OUT/('角色_'+label+'_整合_v02_20261111.blend')
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

bpy.ops.wm.read_factory_settings(use_empty=True)
wood=mat('VALIDATION warm paper wood',(.42,.27,.13))
block=mat('VALIDATION thin printing block',(.19,.22,.18))
paper=mat('VALIDATION handmade paper',(.85,.79,.61))
groups=[]
for index,(cid,label) in enumerate([('zhituan','纸团'),('yintao','印桃')]):
 old=set(bpy.context.scene.objects)
 r,a,m=load(cid,label);x=(-.70,.70)[index];r.location.x=x;action(a,cid+'_Work')
 box('VALIDATION_Table_'+cid,(x,-.54,.305),(.82,.60,.05),wood)
 for dx in (-.32,.32):
  for y in (-.32,-.76):box('VALIDATION_Leg_'+cid,(x+dx,y,.14),(.055,.055,.28),wood)
 box('VALIDATION_ThinBlock_'+cid,(x,-.47,.337),(.63,.45,.014),block)
 props=OUT.parent/'首关道具_v01_20261111/首关纸艺道具包_v01_20261111.blend'
 sid=('paper_black','paper_red')[index]
 with bpy.data.libraries.load(str(props),link=False) as (src,dst):dst.collections=['PROPS/'+sid]
 col=dst.collections[0];bpy.context.scene.collection.children.link(col)
 pr=next(o for o in col.all_objects if o.get('asset_id')==sid and o.parent is None)
 pr.location=(x,-.47,.344);pr.rotation_euler=(0,0,math.pi/2)
 group=bpy.data.objects.new('VALIDATION_ContactAssembly_'+cid,None);bpy.context.scene.collection.objects.link(group);group.location.x=x
 bpy.context.view_layer.update()
 for ob in set(bpy.context.scene.objects)-old:
  if ob!=group and ob.parent is None:world=ob.matrix_world.copy();ob.parent=group;ob.matrix_world=world
 groups.append(group)
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
s=setup((1500,1000),2.90,(2.2,-4.4,2.6),(0,-.18,.58))
if '--cpu' in sys.argv:s.cycles.device='CPU';s.cycles.samples=16
if '--side-only' not in sys.argv:
 s.render.filepath=str(OUT/'预览_双人真实触纸_v02_20261111.png');bpy.ops.render.render(write_still=True)
 print('CONTACT_PREVIEW_READY',flush=True)
for group in groups:group.rotation_euler.z=math.pi/2
for v in bpy.data.objects['VALIDATION_Ground'].data.vertices:v.co.x*=10;v.co.y*=10
s.camera.location=(.20,-6,.95);s.camera.rotation_euler=(Vector((.20,0,.62))-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.camera.data.ortho_scale=3.35
s.render.resolution_y=720
s.render.filepath=str(OUT/'预览_双人触纸正侧面_v02_20261111.png');bpy.ops.render.render(write_still=True)
print('CONTACT_SIDE_PREVIEW_READY',flush=True)
