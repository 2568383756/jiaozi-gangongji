import bpy,math,sys
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
source=(HERE/'render_contact.py').read_text(encoding='utf-8-sig')
exec(source[:source.index("bpy.ops.wm.read_factory_settings(use_empty=True)\nwood=")])
DRAFT=OUT/'work/hand_draft'
def newmat(name,rgb):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes.clear()
 p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');o=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],o.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.85;return m
mat=newmat
def load_draft(cid,label):
 with bpy.data.libraries.load(str(DRAFT/('角色_'+label+'_新手草稿.blend')),link=False) as (src,dst):
  dst.collections=['CHAR_'+cid];dst.actions=[n for n in src.actions if n.startswith(cid+'_')]
 col=dst.collections[0];bpy.context.scene.collection.children.link(col)
 return bpy.data.objects['character_'+cid],bpy.data.objects['rig_'+cid],bpy.data.objects['mesh_'+cid]
for kind in ('Work','Carry'):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 wood=mat('Draft wood',(.42,.27,.13));paper=mat('Draft paper',(.85,.79,.61));block=mat('Draft block',(.19,.22,.18))
 for index,(cid,label) in enumerate([('zhituan','纸团'),('yintao','印桃')]):
  root,rig,mesh=load_draft(cid,label);x=(-.45,.45)[index];root.location.x=x
  action(rig,cid+'_DRAFT_'+kind);bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
  if kind=='Work':
   box('Draft_table_'+cid,(x,-.54,.305),(.80,.60,.050),wood)
   box('Draft_block_'+cid,(x,-.47,.337),(.63,.45,.014),block)
   box('Draft_paper_'+cid,(x,-.47,.347),(.60,.42,.006),paper)
  else:
   ob=box('Draft_carried_paper_'+cid,(0,0,0),(.42,.60,.006),paper)
   for v in ob.data.vertices:v.co.z+=.003
   ob.matrix_world=rig.matrix_world@rig.pose.bones['HoldPoint'].matrix
 s=setup((1500,900),1.85,(.45,-3,1.18),(0,-.23,.43)) if kind=='Work' else setup((1500,900),1.85,(.45,-3,.16),(0,-.18,.48))
 s.cycles.device='CPU';s.cycles.samples=24
 if kind=='Carry':bpy.data.objects['VALIDATION_Ground'].hide_render=True
 s.render.filepath=str(DRAFT/('预览_实心新手_'+kind+'_草稿.png'));bpy.ops.render.render(write_still=True)
 print('DRAFT_RENDER_READY',kind,flush=True)
