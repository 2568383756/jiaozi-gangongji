"""Final full-body hand orientation and actual-paper carry previews."""
import bpy,math
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
source=(HERE/'render_contact.py').read_text(encoding='utf-8-sig')
exec(source[:source.index("bpy.ops.wm.read_factory_settings(use_empty=True)\nwood=")])
props=OUT.parent/'首关道具_v01_20261111/首关纸艺道具包_v01_20261111.blend'
for clip,frame in [('Idle',1),('Walk',9),('CarryIdle',1),('CarryWalk',17)]:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 for index,(cid,label) in enumerate([('zhituan','纸团'),('yintao','印桃')]):
  root,rig,mesh=load(cid,label);root.location.x=(-.65,.65)[index];action(rig,cid+'_'+clip)
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
  if clip.startswith('Carry'):
   sid=('paper_black','paper_red')[index]
   with bpy.data.libraries.load(str(props),link=False) as (src,dst):dst.collections=['PROPS/'+sid]
   col=dst.collections[0];bpy.context.scene.collection.children.link(col)
   paperroot=next(o for o in col.all_objects if o.get('asset_id')==sid and o.parent is None)
   paperroot.matrix_world=rig.matrix_world@rig.pose.bones['HoldPoint'].matrix
 if clip.startswith('Carry'):
  s=setup((1500,1000),3.3,(1.3,-4.5,.32),(0,-.15,.53));s.camera.data.type='PERSP';s.camera.data.lens=52
 else:s=setup((1400,1000),3.1,(1.6,-5,1.8),(0,-.06,.59))
 s.cycles.device='CPU';s.cycles.samples=16
 s.render.filepath=str(OUT/('预览_新手_'+clip+'_v02_20261111.png'));bpy.ops.render.render(write_still=True)
 print('FINAL_HAND_PREVIEW',clip,flush=True)
