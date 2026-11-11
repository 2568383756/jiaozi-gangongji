import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发')
OUT=R/'Scripts/Blender/角色整合_v02_20261111/audit'
results=[]
def activate(rig,a):rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
def evalpoints(mesh):
 ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return p

def ik(rig,targets,wrist,rot):
 for s in ('L','R'):targets[s].location=wrist[s];rig.pose.bones['forearm_'+s].constraints['ProbeIK'].mute=False
 bpy.context.view_layer.update()
 solved={n:rig.pose.bones[n].matrix.copy() for n in ('upper_arm_L','forearm_L','upper_arm_R','forearm_R')}
 for s in ('L','R'):rig.pose.bones['forearm_'+s].constraints['ProbeIK'].mute=True
 bpy.context.view_layer.update()
 for s in ('L','R'):
  for n in ('upper_arm_'+s,'forearm_'+s):rig.pose.bones[n].matrix=solved[n];bpy.context.view_layer.update()
  m=rot[s].to_matrix().to_4x4();m.translation=rig.pose.bones['forearm_'+s].tail;rig.pose.bones['hand_'+s].matrix=m;bpy.context.view_layer.update()
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'Models/首批角色_v01_20261111'/('角色_'+label+'_整合_v01_20261111.blend')),load_ui=False)
 rig=bpy.data.objects['rig_'+cid];mesh=bpy.data.objects['mesh_'+cid]
 activate(rig,bpy.data.actions[cid+'_Idle']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 base={p.name:p.matrix_basis.copy() for p in rig.pose.bones};pts=evalpoints(mesh)
 dom={};rigid={}
 for v in mesh.data.vertices:
  ws=[(g.weight,mesh.vertex_groups[g.group].name) for g in v.groups];w,n=max(ws)
  dom.setdefault(n,[]).append(v.index)
  if w>.95:rigid.setdefault(n,[]).append(v.index)
 masks={s:dom['hand_'+s] for s in ('L','R')};targets={};local={};rots={};offsets={}
 for s in ('L','R'):
  p=rig.pose.bones['hand_'+s];inv=p.matrix.inverted();loc=np.array([list(inv@pts[i]) for i in rigid['hand_'+s]])
  center=loc.mean(axis=0);cov=np.cov((loc-center).T);eig,axes=np.linalg.eigh(cov)
  normal=p.matrix.to_quaternion()@Vector(axes[:,0]);normal=normal if normal.z>=0 else -normal
  rot=normal.rotation_difference(Vector((0,0,1)))@p.matrix.to_quaternion();rots[s]=rot;offsets[s]=Vector(center)
  ob=bpy.data.objects.new('ProbeTarget_'+s,None);bpy.context.scene.collection.objects.link(ob);targets[s]=ob
  c=rig.pose.bones['forearm_'+s].constraints.new('IK');c.name='ProbeIK';c.chain_count=2;c.target=ob;c.iterations=256;c.mute=True
  local[s]={'mask_count':len(masks[s]),'rigid_count':len(loc),'centroid_local':list(center),'pca_eigenvalues':list(eig),'palm_rotation_quaternion':list(rot)}
 for plane in (.34,.35,.36):
  for front in (.27,.28):
   for p in rig.pose.bones:p.matrix_basis=base[p.name].copy()
   bpy.context.view_layer.update();centers={s:Vector(((1 if s=='L' else -1)*.17,-front,plane+.035)) for s in ('L','R')}
   wrist={}
   for repeat in range(5):
    for p in rig.pose.bones:p.matrix_basis=base[p.name].copy()
    bpy.context.view_layer.update()
    for side in ('L','R'):
     shoulder=rig.pose.bones['upper_arm_'+side];m=shoulder.matrix.copy();m.translation.y-=.025;shoulder.matrix=m;bpy.context.view_layer.update()
    h=rig.pose.bones['head'];pivot=h.head.copy();h.matrix=Matrix.Translation(pivot)@Matrix.Rotation(-.14,4,'X')@Matrix.Translation(-pivot)@h.matrix;bpy.context.view_layer.update()
    wrist={s:centers[s]-rots[s]@offsets[s] for s in ('L','R')};ik(rig,targets,wrist,rots)
    pts=evalpoints(mesh)
    for s in ('L','R'):centers[s].z+=plane-min(pts[i].z for i in masks[s])
   pts=evalpoints(mesh);headfaces=[tuple(p.vertices) for p in mesh.data.polygons if all(any(mesh.vertex_groups[g.group].name in ('head','neck') and g.weight>.4 for g in mesh.data.vertices[i].groups) for i in p.vertices)]
   headtree=BVHTree.FromPolygons(pts,headfaces,all_triangles=False)
   case={'character':cid,'contact_plane':plane,'centroid_front':front,'hands':{},'palm_basis':local}
   for s in ('L','R'):
    pp=[pts[i] for i in masks[s]];min_i=min(masks[s],key=lambda i:pts[i].z);near=sorted(masks[s],key=lambda i:pts[i].z)[:max(4,len(pp)//10)]
    gap=min(headtree.find_nearest(pts[i])[3] for i in masks[s])
    case['hands'][s]={'contact_vertex':min_i,'contact':list(pts[min_i]),'bottom':min(v.z for v in pp),'top':max(v.z for v in pp),
      'bbox_xy':[[min(v[k] for v in pp),max(v[k] for v in pp)] for k in (0,1)],'contact_patch_centroid':list(sum((pts[i] for i in near),Vector())/len(near)),
      'wrist_target_error':(rig.pose.bones['forearm_'+s].tail-wrist[s]).length,'nearest_head_surface_gap':gap}
   results.append(case)
   print(cid,plane,front,[(s,round(h['bottom'],4),round(h['top'],4),round(h['wrist_target_error'],4),round(h['nearest_head_surface_gap'],4),[round(v,4) for v in h['contact']]) for s,h in case['hands'].items()],flush=True)
(OUT/'palm_surface_scan_protraction.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
