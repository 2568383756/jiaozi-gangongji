"""Final authorized hands + cuffs, semantic Work and measured carry sockets."""
import sys,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hand_integration import *
SOURCE=R/'Models/首批角色_v01_20261111'
HOOK=R/'Scripts/Blender/角色贴图修正_v01_20261111/garment_materials.py'
REPORT={'version':'v02_20261111_solid_hands','blender':bpy.app.version_string,'surface_z_m':.350,
 'standing_distance_from_near_edge_m':.240,'paper_size_m':[.42,.60],'work_contact_frame':1,
 'carry_calibration':{'mode':'HoldPoint bone HEAD; paper root zero local transform',
  'PalmCenter_semantics':'actual mean of the two new palmar support patches, not hand-bone midpoint',
  'HoldPoint_from_actual_palm_surface':[0,-.280,0],
  'actual_support_from_paper_root':[0,.280,0],
  'legacy_paper_grip_pivot':[0,.210,.006],'legacy_grip_is_not_socket_offset':True},'characters':[]}
def curves(a):return [f for l in a.layers for s in l.strips for b in getattr(s,'channelbags',[]) for f in b.fcurves]
def digest(a):return hashlib.sha256(repr([(f.data_path,f.array_index,[(tuple(k.co),k.interpolation) for k in f.keyframe_points]) for f in curves(a)]).encode()).hexdigest()
def key(rig,frame):
 for p in rig.pose.bones:
  for channel in ('location','rotation_quaternion','scale'):p.keyframe_insert(channel,frame=frame,group=p.name)
def box_tree(lo,hi,m=Matrix.Identity(4)):
 p=[m@Vector((x,y,z)) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
 f=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
 return BVHTree.FromPolygons(p,f,all_triangles=False)
refs={'table':box_tree((-.40,-.84,.275),(.40,-.24,.33)),
 'thin_block':box_tree((-.315,-.695,.330),(.315,-.245,.344)),
 'paper':box_tree((-.30,-.68,.344),(.30,-.26,.350))}
def supported(op,args):
 fields={p.identifier for p in op.get_rna_type().properties};return op(**{k:v for k,v in args.items() if k in fields})
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 path=SOURCE/('角色_'+label+'_整合_v01_20261111.blend');bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
 bpy.context.preferences.filepaths.save_version=0;scene=bpy.context.scene;scene.render.fps=30
 rig=bpy.data.objects['rig_'+cid];mesh=bpy.data.objects['mesh_'+cid];root=bpy.data.objects['character_'+cid]
 originalmesh=[tuple(v.co) for v in mesh.data.vertices];originalweights=[[(g.group,g.weight) for g in v.groups] for v in mesh.data.vertices]
 originalbones={b.name:([*b.head_local],[*b.tail_local]) for b in rig.data.bones}
 preserved={cid+'_'+n:digest(bpy.data.actions[cid+'_'+n]) for n in ('Idle','Walk')}
 cache={};oldhold={}
 for clip,end in [('Idle',1),('CarryIdle',61),('CarryWalk',65)]:
  activate(rig,bpy.data.actions[cid+'_'+clip]);cache[clip]={};oldhold[clip]={}
  for frame in range(1,end+1):
   scene.frame_set(frame);bpy.context.view_layer.update();cache[clip][frame]={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
   oldhold[clip][frame]=rig.pose.bones['HoldPoint'].matrix.copy()
 spec=importlib.util.spec_from_file_location('garment_repair',HOOK);repair=importlib.util.module_from_spec(spec);spec.loader.exec_module(repair);texture=repair.apply(mesh,cid)
 meta,change=replace_hands(mesh,rig,cid)
 unchanged=all(tuple(mesh.data.vertices[new].co)==originalmesh[old] for old,new in change['old_to_new_vertex'].items())
 weightok=all([(g.group,g.weight) for g in mesh.data.vertices[new].groups]==originalweights[old] for old,new in change['old_to_new_vertex'].items())
 mesh.data.calc_loop_triangles();triangles=len(mesh.data.loop_triangles)
 hand_ids=set(meta['L']['vertex_ids']+meta['R']['vertex_ids'])
 handfaces={s:[tuple(p.vertices) for p in mesh.data.polygons if all(j in set(meta[s]['vertex_ids']) for j in p.vertices)] for s in ('L','R')}
 bodyfaces=[tuple(t.vertices) for t in mesh.data.loop_triangles if not all(i in hand_ids for i in t.vertices)]
 headfaces=[tuple(p.vertices) for p in mesh.data.polygons if all(any(mesh.vertex_groups[g.group].name in ('head','neck') and g.weight>.4 for g in mesh.data.vertices[i].groups) for i in p.vertices)]
 rec={'character_id':cid,'source':str(path),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
  'authorized_geometry_change':'old hand regions replaced; closed new hands and cuff lining added; original wide sleeve exterior retained',
  'nonhand_vertices_exactly_preserved':unchanged,'nonhand_weights_exactly_preserved':weightok,
  'original_bone_rest_positions_preserved':originalbones=={b.name:([*b.head_local],[*b.tail_local]) for b in rig.data.bones},
  'geometry_change':change,'vertices':len(mesh.data.vertices),'triangles':triangles,'bone_count':len(rig.data.bones),
  'texture_hook':texture,'clips':{},'work_samples':[],'contact_probe_vertices':{s:meta[s]['contact_probe_vertex_id'] for s in ('L','R')},
  'hand_surface_vertices':{s:meta[s]['vertex_ids'] for s in ('L','R')},
  'palm_patch_vertices':{s:meta[s]['palm_pad_vertex_ids'] for s in ('L','R')},
  'palm_patch_size_m':[.035,.020995], 'carry_calibration':REPORT['carry_calibration']}
 for clip,end in [('Work',31),('CarryIdle',61),('CarryWalk',65)]:
  rig.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions[cid+'_'+clip])
  action=bpy.data.actions.new(cid+'_'+clip);action.use_fake_user=True;action.slots.new(id_type='OBJECT',name=rig.name);activate(rig,action)
  action['game_clip']=True;action['loop']=True;action['root_motion']=False;action['hand_style']='closed_semantic_paper_hand'
  action['source']='new semantic palm press/rub on neutral feet' if clip=='Work' else 'source '+clip+' legs/hips/head retained; natural arm pose and measured new palm support adapted'
  samples=[];first=None
  for frame in range(1,end+1):
   scene.frame_set(frame);phase=math.tau*(frame-1)/(end-1)
   assign(rig,cache['Idle'][1] if clip=='Work' else cache[clip][frame])
   if clip=='Work':
    if cid=='yintao':
     p=rig.pose.bones['hips'];m=p.matrix.copy();m.translation.y+=.03;p.matrix=m;bpy.context.view_layer.update()
    for side in ('L','R'):
     p=rig.pose.bones['upper_arm_'+side];m=p.matrix.copy();m.translation.y-=.025;p.matrix=m;bpy.context.view_layer.update()
    p=rig.pose.bones['head'];v=p.head.copy();p.matrix=Matrix.Translation(v)@Matrix.Rotation(-.14,4,'X')@Matrix.Translation(-v)@p.matrix;bpy.context.view_layer.update()
    z=.350+.0008*(1-math.cos(phase))*.5;y=-.277+.003*math.sin(phase)
    desired={s:Vector(((1 if s=='L' else -1)*.17,y,z)) for s in ('L','R')};geomrot=Quaternion((0,0,1),math.pi)
   else:
    hold=oldhold[clip][frame].copy();hold.translation.y-=.070
    desired={s:hold.translation+Vector(((1 if s=='L' else -1)*.19,.28,0)) for s in ('L','R')};geomrot=Quaternion((1,0,0),math.pi)
   rots={s:geomrot@meta[s]['correction'].to_quaternion().inverted() for s in ('L','R')}
   wrist={s:desired[s]-geomrot@Vector(meta[s]['palm_pad_center_local']) for s in ('L','R')};natural_arms(rig,wrist,rots)
   rig.pose.bones['PalmCenter'].matrix=Matrix.Translation((desired['L']+desired['R'])*.5)
   rig.pose.bones['HoldPoint'].matrix=Matrix.Translation((desired['L']+desired['R'])*.5+Vector((0,-.28,0))) if clip=='Work' else hold
   bpy.context.view_layer.update()
   if frame==end and first is not None:assign(rig,first)
   if frame==1:first={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
   key(rig,frame);pp=posed_points(mesh)
   body=BVHTree.FromPolygons(pp,bodyfaces,all_triangles=True);head=BVHTree.FromPolygons(pp,headfaces,all_triangles=False)
   fixture=refs if clip=='Work' else {'carried_paper':box_tree((-.21,-.30,0),(.21,.30,.006),rig.pose.bones['HoldPoint'].matrix)}
   sample={'frame':frame,'hands':{},'hold_point':list(rig.pose.bones['HoldPoint'].head),'palm_surface_center':list(rig.pose.bones['PalmCenter'].head),
    'body_fixture_intersection_counts':{n:len(body.overlap(t)) for n,t in fixture.items()},'foot_min_z':min(p.z for p in pp)}
   for side in ('L','R'):
    ids=meta[side]['vertex_ids'];pad=meta[side]['palm_pad_vertex_ids'];i=meta[side]['contact_probe_vertex_id'];center=sum((pp[j] for j in pad),Vector())/len(pad)
    surface=BVHTree.FromPolygons(pp,handfaces[side],all_triangles=False)
    sample['hands'][side]={'contact_vertex_id':i,'contact_xyz':list(pp[i]),'palm_patch_center':list(center),
     'palm_patch_vertex_ids':pad,'palm_plane_max_error':max(abs(pp[j].z-(desired[side].z if clip=='Work' else rig.pose.bones['HoldPoint'].head.z)) for j in pad),
     'head_nearest_surface_gap':min(head.find_nearest(pp[j])[3] for j in ids),'head_triangle_intersections':len(head.overlap(surface)),
     'semantic_finger_direction':list(geomrot@Vector((0,1,0))),'semantic_palm_normal':list(geomrot@Vector((0,0,-1))),
     'bottom_z':min(pp[j].z for j in ids),'top_z':max(pp[j].z for j in ids)}
   samples.append(sample)
  for f in curves(action):
   for p in f.keyframe_points:p.interpolation='LINEAR'
  rec['clips'][clip]={'frames':[1,end],'fps':30,'source':action['source'],'samples':samples}
  if clip=='Work':rec['work_samples']=samples
 rec['idle_walk_bone_curves_unchanged']=all(digest(bpy.data.actions[n])==value for n,value in preserved.items())
 rec['preserved_idle_walk_digests']=preserved
 rec['min_head_gap_m']=min(h['head_nearest_surface_gap'] for cl in rec['clips'].values() for s in cl['samples'] for h in s['hands'].values())
 rec['head_triangle_intersections']=sum(h['head_triangle_intersections'] for cl in rec['clips'].values() for s in cl['samples'] for h in s['hands'].values())
 rec['body_fixture_intersections']=sum(sum(s['body_fixture_intersection_counts'].values()) for cl in rec['clips'].values() for s in cl['samples'])
 root['asset_version']='v02_20261111_solid_hands';root['hand_geometry']='closed semantic paper hands';root['work_surface_z']=.35;root['work_standing_distance']=.24
 rig.data.bones['PalmCenter']['role']='carry_palm_surface_center';rig.data.bones['HoldPoint']['offset_from_palms_blender']=[0,-.28,0]
 rig.data.bones['HoldPoint']['role']='carry_socket';rig.data.bones['HoldPoint']['legacy_grip_not_equivalent']=True
 (OUT/'Textures').mkdir(exist_ok=True)
 for image in bpy.data.images:
  if image.source in ('FILE','GENERATED') and image.size[0]>0:
   name=cid+'_basecolor_2048.png' if tuple(image.size)==(2048,2048) else image.name+'.png';dest=OUT/'Textures'/name
   image.filepath_raw=str(dest);image.file_format='PNG';image.save()
   if image.packed_file:image.unpack(method='REMOVE')
   image.source='FILE';image.filepath=str(dest);image.reload();image.pack()
 activate(rig,bpy.data.actions[cid+'_Work']);scene.frame_start=1;scene.frame_end=31;scene.frame_set(1);bpy.context.view_layer.update()
 stem='角色_'+label+'_整合_v02_20261111';blend=OUT/(stem+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 bpy.ops.object.select_all(action='DESELECT')
 for ob in (root,rig,mesh):ob.select_set(True)
 bpy.context.view_layer.objects.active=rig
 supported(bpy.ops.export_scene.gltf,dict(filepath=str(OUT/(stem+'.glb')),export_format='GLB',use_selection=True,
  export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_def_bones=False,
  export_yup=True,export_extras=True,export_materials='EXPORT',export_cameras=False,export_lights=False,
  export_all_influences=False,export_image_format='JPEG',export_jpeg_quality=95,export_image_quality=95,export_current_frame=False))
 supported(bpy.ops.export_scene.fbx,dict(filepath=str(OUT/(stem+'.fbx')),use_selection=True,object_types={'EMPTY','MESH','ARMATURE'},
  axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',add_leaf_bones=False,
  use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,
  bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=True))
 rec['blend']=str(blend);rec['blend_sha256']=hashlib.sha256(blend.read_bytes()).hexdigest();REPORT['characters'].append(rec)
 (OUT/'角色触台报告_v02_20261111.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
 print('SOLID_HAND_CHARACTER_READY',cid,'verts',len(mesh.data.vertices),'triangles',triangles,'head_hits',rec['head_triangle_intersections'],'fixture_hits',rec['body_fixture_intersections'],flush=True)
print('SOLID_HAND_BUILD_FINISHED',flush=True)
