import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
R=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发')
code=(R/'Scripts/Blender/角色整合_v02_20261111/audit/历史_旧C手构建器_仅供阅读.py.txt').read_text(encoding='utf-8')
exec(code[:code.index("for cid,label in [('zhituan'")])
references['table']=box_bvh((-.40,-.84,.275),(.40,-.24,.33))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'角色_印桃_整合_v01_20261111.blend'),load_ui=False)
rig=bpy.data.objects['rig_yintao'];mesh=bpy.data.objects['mesh_yintao']
activate(rig,bpy.data.actions['yintao_Idle']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
base={p.name:p.matrix_basis.copy() for p in rig.pose.bones};pp=points(mesh)
dom={};rigid={}
for v in mesh.data.vertices:
 w,n=max((g.weight,mesh.vertex_groups[g.group].name) for g in v.groups);dom.setdefault(n,[]).append(v.index)
 if w>.95:rigid.setdefault(n,[]).append(v.index)
masks={s:dom['hand_'+s] for s in ('L','R')};offset={};original={};targets={}
handids=set(masks['L']+masks['R']);mesh.data.calc_loop_triangles()
bodyfaces=[tuple(t.vertices) for t in mesh.data.loop_triangles if not any(i in handids for i in t.vertices)]
for side in ('L','R'):
 hand=rig.pose.bones['hand_'+side];inv=hand.matrix.inverted();loc=np.array([list(inv@pp[i]) for i in rigid['hand_'+side]])
 center=loc.mean(axis=0);eig,axes=np.linalg.eigh(np.cov((loc-center).T))
 normal=hand.matrix.to_quaternion()@Vector(axes[:,0]);normal=normal if normal.z>=0 else -normal
 original[side]=normal.rotation_difference(Vector((0,0,1)))@hand.matrix.to_quaternion();offset[side]=Vector(center)
 target=bpy.data.objects.new('TEMP_ContactTarget_'+side,None);bpy.context.scene.collection.objects.link(target);targets[side]=target
 c=rig.pose.bones['forearm_'+side].constraints.new('IK');c.name='TEMP_ContactIK';c.target=target;c.chain_count=2;c.iterations=256;c.use_tail=True;c.mute=True
 rig.pose.bones['upper_arm_'+side].ik_stretch=0;rig.pose.bones['forearm_'+side].ik_stretch=0
headfaces=[tuple(p.vertices) for p in mesh.data.polygons if all(any(mesh.vertex_groups[g.group].name in ('head','neck') and g.weight>.4 for g in mesh.data.vertices[i].groups) for i in p.vertices)]
results=[]
for angle in (-1.2,-.8,-.4,0,.4,.8,1.2,1.57):
 rot={s:Quaternion((1,0,0),angle)@original[s] for s in ('L','R')}
 centers={s:Vector(((1 if s=='L' else -1)*.17,-.28,.39)) for s in ('L','R')}
 for repeat in range(8):
  pose(rig,base);hips=rig.pose.bones['hips'];hm=hips.matrix.copy();hm.translation.y+=.03;hips.matrix=hm;bpy.context.view_layer.update()
  for side in ('L','R'):
   shoulder=rig.pose.bones['upper_arm_'+side];m=shoulder.matrix.copy();m.translation.y-=.025;shoulder.matrix=m;bpy.context.view_layer.update()
  head=rig.pose.bones['head'];pivot=head.head.copy();head.matrix=Matrix.Translation(pivot)@Matrix.Rotation(-.14,4,'X')@Matrix.Translation(-pivot)@head.matrix;bpy.context.view_layer.update()
  wrist={s:centers[s]-rot[s]@offset[s] for s in ('L','R')};solve(rig,targets,wrist,rot);pp=points(mesh)
  for side in ('L','R'):
   i=min(masks[side],key=lambda i:pp[i].z);centers[side].z+=.35-pp[i].z;centers[side].y+=-.277-pp[i].y
 pp=points(mesh);bodytree=BVHTree.FromPolygons(pp,bodyfaces,all_triangles=True);headtree=BVHTree.FromPolygons(pp,headfaces,all_triangles=False)
 result={'pitch':angle,'intersections':{n:len(bodytree.overlap(tree)) for n,tree in references.items()},'hands':{}}
 for side in ('L','R'):
  i=min(masks[side],key=lambda i:pp[i].z)
  result['hands'][side]={'contact_id':i,'contact':list(pp[i]),'wrist':list(rig.pose.bones['hand_'+side].head),'ik_error':(rig.pose.bones['forearm_'+side].tail-wrist[side]).length,'gap':min(headtree.find_nearest(pp[j])[3] for j in masks[side])}
 results.append(result);print(json.dumps(result),flush=True)
(R/'Scripts/Blender/角色整合_v02_20261111/audit/yintao_cuff_scan.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
