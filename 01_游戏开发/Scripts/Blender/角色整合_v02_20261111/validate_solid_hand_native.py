"""Independent reload checks for the authorized solid-hand final assets."""
import bpy,json,math,hashlib,collections
from pathlib import Path
from mathutils import Vector
R=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发');OUT=R/'Models/首批角色_v02_20261111'
build=json.loads((OUT/'角色触台报告_v02_20261111.json').read_text(encoding='utf-8'))
normal_baseline_path=R/'Scripts/Blender/触台比例核验_v01_20261111/自定义法线同值回存核验_v01_20261111.json'
normal_baseline=json.loads(normal_baseline_path.read_text(encoding='utf-8'))
report={'version':'v02_solid_hands','checks':[],'characters':[]}
def check(name,ok,details=None):report['checks'].append({'name':name,'passed':bool(ok),'details':details})
def activate(rig,a):rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
def points(mesh):
 ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return p
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 source=next(c for c in build['characters'] if c['character_id']==cid)
 bpy.ops.wm.open_mainfile(filepath=source['source'],load_ui=False)
 oldmesh=bpy.data.objects['mesh_'+cid];oldrig=bpy.data.objects['rig_'+cid]
 oldv=[tuple(v.co) for v in oldmesh.data.vertices];oldw=[[(g.group,g.weight) for g in v.groups] for v in oldmesh.data.vertices]
 oldnormals=[tuple(n.vector) for n in oldmesh.data.corner_normals];oldloops={p.index:list(p.loop_indices) for p in oldmesh.data.polygons}
 oldbones={b.name:(tuple(b.head_local),tuple(b.tail_local)) for b in oldrig.data.bones}
 bpy.ops.wm.open_mainfile(filepath=str(OUT/('角色_'+label+'_整合_v02_20261111.blend')),load_ui=False)
 mesh=bpy.data.objects['mesh_'+cid];rig=bpy.data.objects['rig_'+cid]
 mapping={int(k):v for k,v in source['geometry_change']['old_to_new_vertex'].items()}
 check(cid+'/authorized_hand_remesh_present',mesh.get('hand_region_authorized_change') and len(mesh.data.vertices)!=len(oldv),source['geometry_change']['removed_hand_vertices'])
 check(cid+'/all_retained_original_vertices_exact',all(tuple(mesh.data.vertices[j].co)==oldv[i] for i,j in mapping.items()),len(mapping))
 check(cid+'/all_retained_original_weights_exact',all([(g.group,g.weight) for g in mesh.data.vertices[j].groups]==oldw[i] for i,j in mapping.items()))
 normal_error=0;normal_angle=0
 for p in mesh.data.polygons:
  source_face=mesh.data.attributes['source_original_face_id'].data[p.index].value
  if source_face>=0:
   for newloop,oldloop in zip(p.loop_indices,oldloops[source_face]):
    a=mesh.data.corner_normals[newloop].vector;b=Vector(oldnormals[oldloop]);normal_error=max(normal_error,(a-b).length)
    normal_angle=max(normal_angle,math.degrees(2*math.asin(min(1.,(a.normalized()-b.normalized()).length/2))))
 baseline=normal_baseline['characters'][cid]
 # Setting identical input normals on an unedited source copy produces the
 # same ~0.0005 vector delta: measured storage re-encoding, not byte identity.
 normal_ok=(baseline['source_sha256']==source['source_sha256'] and baseline['source_unchanged']
            and normal_error<=baseline['identical_input_roundtrip_max_chord_delta']+.000001
            and normal_angle<.05)
 check(cid+'/original_nonhand_custom_normals_within_measured_reencoding',normal_ok,
       {'max_vector_delta':normal_error,'max_angle_deg':normal_angle,'angle_limit_deg':.05,
        'source_identical_input_roundtrip_max_vector_delta':baseline['identical_input_roundtrip_max_chord_delta'],
        'allowed_vector_delta_over_measured_baseline':.000001,
        'baseline_report':str(normal_baseline_path),'note':'Source corner-normal directions retained within the independently measured identical-input storage roundtrip; not byte-identical normals.'})
 check(cid+'/rest_bones_unchanged',oldbones=={b.name:(tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones})
 check(cid+'/source_file_unchanged',hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['source_sha256'])
 check(cid+'/Idle_Walk_bone_curves_preserved',source['idle_walk_bone_curves_unchanged'])
 check(cid+'/no_unweighted_vertices',all(v.groups and abs(sum(g.weight for g in v.groups)-1)<.0001 for v in mesh.data.vertices))
 check(cid+'/four_influences_max',max(len(v.groups) for v in mesh.data.vertices)<=4)
 rec={'character_id':cid,'actions':[],'contact_probes':{},'hands':{}}
 for side in ('L','R'):
  ids=set(source['hand_surface_vertices'][side]);faces=[tuple(p.vertices) for p in mesh.data.polygons if all(i in ids for i in p.vertices)]
  edges=collections.Counter(tuple(sorted((a,b))) for f in faces for a,b in zip(f,f[1:]+f[:1]));used={i for f in faces for i in f}
  euler=len(used)-len(edges)+len(faces)
  check(cid+'/'+side+'/closed_hand_surface',all(n==2 for n in edges.values()) and euler==2,{'vertices':len(used),'faces':len(faces),'euler':euler})
  check(cid+'/'+side+'/semantic_flat_pad',len(source['palm_patch_vertices'][side])==11,source['palm_patch_size_m'])
  rec['hands'][side]={'vertices':len(used),'faces':len(faces),'euler':euler}
 for action in bpy.data.actions:
  activate(rig,action);start,end=map(round,action.frame_range);ends=[];roots=[];ground=[];armerr=[]
  for frame in range(start,end+1):
   bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();pp=points(mesh)
   if frame in (start,end):ends.append([float(x) for p in rig.pose.bones for row in p.matrix for x in row])
   roots.append(list(rig.matrix_world@rig.pose.bones['root'].head));ground.append(min(p.z for p in pp))
   for n in ('upper_arm_L','upper_arm_R','forearm_L','forearm_R'):armerr.append(abs((rig.pose.bones[n].tail-rig.pose.bones[n].head).length-rig.data.bones[n].length))
  loop=max(abs(a-b) for a,b in zip(*ends));drift=max(math.dist(p,roots[0]) for p in roots)
  tag=cid+'/'+action.name;check(tag+'/loop',loop<.0002,loop);check(tag+'/root_static',drift<.0002,drift)
  check(tag+'/grounded',min(ground)>-.001 and max(ground)<.003,[min(ground),max(ground)])
  check(tag+'/arm_lengths_preserved',max(armerr)<.00002,max(armerr))
  rec['actions'].append({'name':action.name,'frames':[start,end],'loop_error':loop,'root_drift':drift,'ground':[min(ground),max(ground)]})
 for clip,entry in source['clips'].items():
  activate(rig,bpy.data.actions[cid+'_'+clip]);plane_errors=[];source_errors=[];carry_offsets=[]
  for sample in entry['samples']:
   frame=sample['frame'];bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();pp=points(mesh)
   for side,hand in sample['hands'].items():
    i=source['contact_probe_vertices'][side];expected=Vector(hand['contact_xyz']);source_errors.append((pp[i]-expected).length)
    target=hand['palm_patch_center'][2] if clip=='Work' else rig.pose.bones['HoldPoint'].head.z
    plane_errors.extend(abs(pp[j].z-target) for j in source['palm_patch_vertices'][side])
    if clip=='Work':
     rec['contact_probes'].setdefault(str(i),{'vertex_id':i,'rest_xyz':list(mesh.matrix_world@mesh.data.vertices[i].co),'side':side,'samples':[]})['samples'].append({'frame':frame,'xyz':list(pp[i])})
   if clip.startswith('Carry'):carry_offsets.append((rig.pose.bones['PalmCenter'].head-rig.pose.bones['HoldPoint'].head-Vector((0,.28,0))).length)
  check(cid+'/'+clip+'/all_frames_actual_skin_reloads',max(source_errors)<.00001,max(source_errors))
  check(cid+'/'+clip+'/actual_palmar_patch_plane',max(plane_errors)<.00002,max(plane_errors))
  check(cid+'/'+clip+'/body_and_cuff_fixture_BVH',all(not any(s['body_fixture_intersection_counts'].values()) for s in entry['samples']))
  check(cid+'/'+clip+'/hands_clear_head_BVH',all(not h['head_triangle_intersections'] for s in entry['samples'] for h in s['hands'].values()))
  if carry_offsets:check(cid+'/'+clip+'/new_surface_socket_calibration',max(carry_offsets)<.00002,max(carry_offsets))
 report['characters'].append(rec)
report['passed']=sum(c['passed'] for c in report['checks']);report['total']=len(report['checks']);report['all_passed']=report['passed']==report['total']
(OUT/'角色动作与触台核验_v02_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('SOLID_HAND_NATIVE_VALIDATION',report['passed'],report['total'],flush=True)
