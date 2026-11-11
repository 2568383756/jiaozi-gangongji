"""Shared semantic hand replacement, cuff lining and natural arm posing."""
import bpy,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from hand_geometry import make_hand_geometry
R=HERE.parents[2]
OUT=R/'Models/首批角色_v02_20261111';DRAFT=OUT/'work/hand_draft';DRAFT.mkdir(parents=True,exist_ok=True)

def activate(rig,action):rig.animation_data_create();rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
def posed_points(mesh):
 ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return p
def srgb(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def skin_mat(cid,side=False):
 rgb=(228.2/255,151.3/255,81.4/255) if cid=='zhituan' else (234.7/255,155.4/255,98.8/255)
 m=bpy.data.materials.new('MAT_'+cid+'_SolidHand_'+('side' if side else 'back'));m.use_nodes=True
 color=[srgb(c*(.98 if side else 1)) for c in rgb]
 m.diffuse_color=(*color,1);m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);p.inputs['Base Color'].default_value=(*color,1)
 p.inputs['Roughness'].default_value=.82;p.inputs['Specular IOR Level'].default_value=.20
 return m
def lining_mat(cid):
 m=skin_mat(cid);m.name='MAT_'+cid+'_WristLining';p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 color=(*(srgb(c) for c in (.92,.82,.65)),1);p.inputs['Base Color'].default_value=color;m.diffuse_color=color;return m
def replace_hands(mesh,rig,cid):
 old=mesh.data;names={g.index:g.name for g in mesh.vertex_groups}
 dominant={v.index:names[max(v.groups,key=lambda g:g.weight).group] for v in old.vertices}
 removed={i for i,n in dominant.items() if n in ('hand_L','hand_R')}
 kept=[v for v in old.vertices if v.index not in removed];mapping={v.index:i for i,v in enumerate(kept)}
 vertices=[tuple(v.co) for v in kept];weights=[[(g.group,g.weight) for g in v.groups] for v in kept]
 faces=[];uvs=[];matids=[];smooth=[];sourcefaces=[];cornernormals=[]
 for p in old.polygons:
  if any(i in removed for i in p.vertices):continue
  faces.append(tuple(mapping[i] for i in p.vertices));uvs.append([tuple(old.uv_layers.active.data[j].uv) for j in p.loop_indices]);matids.append(p.material_index);smooth.append(p.use_smooth);sourcefaces.append(p.index);cornernormals.append([tuple(old.corner_normals[j].vector) for j in p.loop_indices])
 materials=list(old.materials);skin_start=len(materials);materials.extend([skin_mat(cid),skin_mat(cid,True),lining_mat(cid)])
 handmeta={}
 for side in ('L','R'):
  bone=rig.data.bones['hand_'+side];finger=(bone.tail_local-bone.head_local).normalized()
  outward=Vector(((1 if side=='L' else -1),0,0));back=(outward-finger*outward.dot(finger)).normalized();across=finger.cross(back).normalized()
  semantic_rest=Matrix((across,finger,back)).transposed().to_4x4();semantic_rest.translation=bone.head_local
  correction=bone.matrix_local.inverted()@semantic_rest
  verts,polys,tags=make_hand_geometry(side,{'w':.080,'l':.095,'t':.050,'wrist_extension':.025})
  start=len(vertices);vertices.extend(tuple(semantic_rest@Vector(p)) for p in verts)
  group=mesh.vertex_groups['hand_'+side].index;weights.extend([[(group,1.0)] for p in verts])
  for f,tag in zip(polys,tags):
   faces.append(tuple(start+i for i in f));uvs.append([((verts[i][0]+.075)/.15,(verts[i][1]+.012)/.132) for i in f]);matids.append(skin_start+(tag=='skin_side'));smooth.append(True);sourcefaces.append(-1);cornernormals.append([(0,0,0)]*len(f))
  pad=[i for i,p in enumerate(verts) if abs(p[2]+.025)<1e-7 and .045<p[1]<.095]
  pad_center=sum((Vector(verts[i]) for i in pad),Vector())/len(pad)
  handmeta[side]={'correction':correction,'vertex_ids':list(range(start,start+len(verts))),'local_vertices':verts,
   'palm_pad_vertex_ids':[start+i for i in pad],'palm_pad_center_local':list(pad_center),
   'contact_probe_vertex_id':start+min(pad,key=lambda i:(Vector(verts[i])-pad_center).length)}
  # Inner cuff lining preserves the original wide sleeve silhouette. A closed
  # shallow annulus bridges the large sleeve cavity to the new short wrist.
  fore=rig.data.bones['forearm_'+side];foregroup=mesh.vertex_groups['forearm_'+side].index
  radius=.065 if cid=='yintao' else .040;segments=24;rings=[]
  for rear in (False,True):
   for row in (0,1,2):
    ring=[];blend=row/2
    for k in range(segments):
     angle=math.tau*k/segments
     outer=fore.matrix_local@Vector((radius*math.cos(angle),fore.length-.012-(.003 if rear else 0),radius*math.sin(angle)))
     inner=semantic_rest@Vector((.023*math.cos(angle),-.004-(.003 if rear else 0),.019*math.sin(angle)))
     ring.append(len(vertices));vertices.append(tuple(outer.lerp(inner,blend)))
     weights.append([(foregroup,1-blend),(group,blend)] if row==1 else [(foregroup if row==0 else group,1.)])
    rings.append(ring)
  for rear in (0,1):
   for row in (0,1):
    a,b=rings[rear*3+row],rings[rear*3+row+1]
    for k in range(segments):
     f=(a[k],a[(k+1)%segments],b[(k+1)%segments],b[k])
     faces.append(f if rear else tuple(reversed(f)));uvs.append([(0,0),(1,0),(1,1),(0,1)]);matids.append(skin_start+2);smooth.append(True);sourcefaces.append(-2);cornernormals.append([(0,0,0)]*4)
  for row in (0,2):
   a,b=rings[row],rings[row+3]
   for k in range(segments):
    f=(a[k],b[k],b[(k+1)%segments],a[(k+1)%segments])
    faces.append(tuple(reversed(f)) if row==0 else f);uvs.append([(0,0),(1,0),(1,1),(0,1)]);matids.append(skin_start+2);smooth.append(True);sourcefaces.append(-2);cornernormals.append([(0,0,0)]*4)
 new=bpy.data.meshes.new('geometry_'+cid+'_SolidHands_v02');new.from_pydata(vertices,[],faces);new.materials.clear()
 for material in materials:new.materials.append(material)
 layer=new.uv_layers.new(name=old.uv_layers.active.name)
 for p,sourceuvs,mi,sm in zip(new.polygons,uvs,matids,smooth):
  p.material_index=mi;p.use_smooth=sm
  for j,uv in zip(p.loop_indices,sourceuvs):layer.data[j].uv=uv
 sourceid=new.attributes.new('source_original_vertex_id','INT','POINT')
 for i,v in enumerate(kept):sourceid.data[i].value=v.index
 for i in range(len(kept),len(vertices)):sourceid.data[i].value=-1
 region=new.attributes.new('authorized_hand_region','INT','FACE')
 for p,sourceface in zip(new.polygons,sourcefaces):region.data[p.index].value=0 if sourceface>=0 else 1 if sourceface==-1 else 2
 faceid=new.attributes.new('source_original_face_id','INT','FACE')
 for p,sourceface in zip(new.polygons,sourcefaces):faceid.data[p.index].value=sourceface
 sharp={tuple(sorted((mapping[e.vertices[0]],mapping[e.vertices[1]]))):bool(e.use_edge_sharp) for e in old.edges if all(i in mapping for i in e.vertices)}
 for e in new.edges:e.use_edge_sharp=sharp.get(tuple(sorted(e.vertices)),False)
 new.normals_split_custom_set([n for ns in cornernormals for n in ns])
 mesh.data=new
 mesh.vertex_groups.clear()
 for gi in sorted(names):mesh.vertex_groups.new(name=names[gi])
 for i,wts in enumerate(weights):
  for gi,w in wts:mesh.vertex_groups[gi].add([i],w,'REPLACE')
 mesh['hand_geometry_version']='solid_paper_hand_v02';mesh['hand_region_authorized_change']=True
 mesh['preserved_nonhand_vertices']=len(kept);mesh['removed_original_hand_vertices']=len(removed)
 return handmeta,{'removed_hand_vertices':len(removed),'preserved_nonhand_vertices':len(kept),'old_vertices':len(old.vertices),'new_vertices':len(vertices),'old_to_new_vertex':mapping,
  'removed_source_face_ids':[p.index for p in old.polygons if any(i in removed for i in p.vertices)],
  'preserved_source_face_ids':[i for i in sourcefaces if i>=0],
  'new_solid_hand_faces':sum(i==-1 for i in sourcefaces),'new_cuff_lining_faces':sum(i==-2 for i in sourcefaces)}
def assign(rig,base):
 for p in rig.pose.bones:p.matrix_basis=base[p.name].copy();p.rotation_mode='QUATERNION'
 bpy.context.view_layer.update()
def ik(rig,targets,wrist,rots):
 for side in ('L','R'):targets[side].location=wrist[side];rig.pose.bones['forearm_'+side].constraints['TEMP_NewHandIK'].mute=False
 bpy.context.view_layer.update();mats={n:rig.pose.bones[n].matrix.copy() for n in ('upper_arm_L','forearm_L','upper_arm_R','forearm_R')}
 for side in ('L','R'):rig.pose.bones['forearm_'+side].constraints['TEMP_NewHandIK'].mute=True
 bpy.context.view_layer.update()
 for side in ('L','R'):
  for n in ('upper_arm_'+side,'forearm_'+side):rig.pose.bones[n].matrix=mats[n];bpy.context.view_layer.update()
  m=rots[side].to_matrix().to_4x4();m.translation=rig.pose.bones['forearm_'+side].tail;rig.pose.bones['hand_'+side].matrix=m;bpy.context.view_layer.update()
def natural_arms(rig,wrist,rots):
 for side in ('L','R'):
  upper=rig.pose.bones['upper_arm_'+side];fore=rig.pose.bones['forearm_'+side];S=upper.head.copy();W=wrist[side]
  A=rig.data.bones[upper.name].length;B=rig.data.bones[fore.name].length;direction=W-S;distance=direction.length;direction.normalize()
  if distance>A+B+.0001:raise RuntimeError('Target exceeds unchanged arm length')
  along=(A*A-B*B+distance*distance)/(2*distance);height=max(0,A*A-along*along)**.5
  pole=Vector(((.20 if side=='L' else -.20),0,-1));pole=(pole-direction*pole.dot(direction)).normalized();E=S+direction*along+pole*height
  for p,start,end in ((upper,S,E),(fore,E,W)):
   base=p.matrix.copy();axis=(p.tail-p.head).normalized();rot=axis.rotation_difference((end-start).normalized())@base.to_quaternion()
   m=rot.to_matrix().to_4x4();m.translation=start;p.matrix=m;bpy.context.view_layer.update()
  m=rots[side].to_matrix().to_4x4();m.translation=W;rig.pose.bones['hand_'+side].matrix=m;bpy.context.view_layer.update()
