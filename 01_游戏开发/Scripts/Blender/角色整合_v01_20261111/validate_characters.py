import bpy,json,math,hashlib,traceback,struct,collections
from pathlib import Path
from mathutils import Vector
ROOT=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发')
OUT=ROOT/'Models/首批角色_v01_20261111'
report={'blender':bpy.app.version_string,'files':[],'checks':[]}
def vec(v):return [float(x) for x in v]
def bounds(points):
 lo=[min(p[k] for p in points) for k in range(3)];hi=[max(p[k] for p in points) for k in range(3)]
 return {'min':lo,'max':hi,'size':[hi[k]-lo[k] for k in range(3)]}
def check(name,ok,details=None):report['checks'].append({'name':name,'passed':bool(ok),'details':details})
def activate(rig,a):
 rig.animation_data_create();rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
def glb_topology(path):
 blob=path.read_bytes();length=struct.unpack_from('<I',blob,12)[0]
 data=json.loads(blob[20:20+length]);binary=28+length
 count=0;duplicates=[]
 for mesh_index,mesh in enumerate(data.get('meshes',[])):
  for prim_index,prim in enumerate(mesh['primitives']):
   a=data['accessors'][prim['indices']];view=data['bufferViews'][a['bufferView']]
   code={5121:'B',5123:'H',5125:'I'}[a['componentType']]
   ids=struct.unpack_from('<'+code*a['count'],blob,binary+view.get('byteOffset',0)+a.get('byteOffset',0))
   count+=len(ids)//3;seen={}
   for i in range(0,len(ids),3):
    ordered=ids[i:i+3];key=tuple(sorted(ordered))
    if key in seen:
     duplicates.append({'mesh':mesh_index,'primitive':prim_index,'first_triangle':seen[key][0],
                        'duplicate_triangle':i//3,'first_indices':seen[key][1],'duplicate_indices':ordered,
                        'note':'Identical vertex references imply identical position, UV, normal and skin attributes; importer removes redundant coincident face.'})
    else:seen[key]=(i//3,ordered)
 return {'encoded_triangles':count,'duplicate_index_faces':duplicates}
for cid,label,tris in [('zhituan','纸团',11287),('yintao','印桃',9771)]:
 for ext in ('blend','glb','fbx'):
  path=OUT/('角色_'+label+'_整合_v01_20261111.'+ext)
  try:
   bpy.ops.wm.read_factory_settings(use_empty=True)
   bpy.context.scene.render.fps=30
   if ext=='blend':bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
   elif ext=='glb':bpy.ops.import_scene.gltf(filepath=str(path))
   else:bpy.ops.import_scene.fbx(filepath=str(path),use_anim=True)
   scene=bpy.context.scene
   rig=next(o for o in scene.objects if o.type=='ARMATURE')
   # The glTF importer creates a hidden Icosphere bone-display widget. Audit
   # only actual skinned character meshes, never that display-only helper.
   meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
   rig.data.pose_position='REST';bpy.context.view_layer.update()
   rest=bounds([o.matrix_world@v.co for o in meshes for v in o.data.vertices])
   tri_count=0
   for ob in meshes:ob.data.calc_loop_triangles();tri_count+=len(ob.data.loop_triangles)
   rec={'character_id':cid,'format':ext,'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'rest_bounds':rest,'triangles':tri_count,'bone_count':len(rig.data.bones),'bones':[b.name for b in rig.data.bones],
        'images':[{'name':i.name,'size':list(i.size),'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'],
        'actions':[]}
   tag=cid+'/'+ext
   check(tag+'/rest_height',abs(rest['size'][2]-1.2)<.002,rest)
   check(tag+'/feet_origin',abs(rest['min'][2])<.002,rest['min'][2])
   if ext=='glb':
    topology=glb_topology(path);rec['encoded_topology']=topology
    check(tag+'/visible_surface_triangle_accounting',topology['encoded_triangles']==tris and
          tri_count+len(topology['duplicate_index_faces'])==tris,
          {'source_and_encoded':tris,'imported':tri_count,'duplicate_faces_removed_by_importer':topology['duplicate_index_faces']})
   else:check(tag+'/triangles_unchanged',tri_count==tris,tri_count)
   check(tag+'/socket_bones',all(n in rig.data.bones for n in ('HoldPoint','PalmCenter')),len(rig.data.bones))
   check(tag+'/24_bones',len(rig.data.bones)==24,len(rig.data.bones))
   check(tag+'/no_runtime_constraints',not any(p.constraints for p in rig.pose.bones))
   check(tag+'/2048_texture',all(i.size[0]==2048 and i.size[1]==2048 for i in bpy.data.images if i.source=='FILE'))
   allnames=[a.name for a in bpy.data.actions]
   check(tag+'/five_game_clips',len(allnames)==5 and all(any(cid+'_'+n in a for a in allnames) for n in ('Idle','Walk','CarryIdle','CarryWalk','Work')),allnames)
   rig.data.pose_position='POSE'
   for action in bpy.data.actions:
    activate(rig,action)
    a,b=action.frame_range;frame_samples=[a,a+(b-a)*.25,a+(b-a)*.5,a+(b-a)*.75,b]
    matrices=[];roots=[];held=[];ground=[]
    for f in frame_samples:
     fi=math.floor(f);scene.frame_set(fi,subframe=f-fi);bpy.context.view_layer.update()
     matrices.append([float(x) for p in rig.pose.bones for row in p.matrix for x in row])
     roots.append(vec(rig.matrix_world@rig.pose.bones['root'].head))
     held.append(vec(rig.matrix_world@rig.pose.bones['HoldPoint'].head))
     dg=bpy.context.evaluated_depsgraph_get();points=[]
     for ob in meshes:
      ev=ob.evaluated_get(dg);me=ev.to_mesh();points.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
     ground.append(min(p.z for p in points))
    delta=max(abs(x-y) for x,y in zip(matrices[0],matrices[-1]))
    drift=max(math.dist(v,roots[0]) for v in roots)
    ac={'name':action.name,'frame_range':[a,b],'duration_seconds':(b-a)/30,'loop_max_matrix_delta':delta,
        'root_translation_max_drift':drift,'hold_samples':held,'minimum_skin_z_samples':ground}
    rec['actions'].append(ac)
    check(tag+'/'+action.name+'/loop_endpoints',delta<.0002,delta)
    check(tag+'/'+action.name+'/root_static',drift<.0002,drift)
    check(tag+'/'+action.name+'/grounded',min(ground)>-.001 and max(ground)<.003,ground)
   report['files'].append(rec)
   print('VALIDATED',tag,tri_count,len(rig.data.bones),allnames,flush=True)
  except Exception:
   report['files'].append({'file':str(path),'error':traceback.format_exc()});check(str(path)+'/exception',False,traceback.format_exc())
   print(traceback.format_exc(),flush=True)
report['passed']=sum(c['passed'] for c in report['checks']);report['total']=len(report['checks'])
report['all_passed']=report['passed']==report['total']
(OUT/'角色复导核验_v01_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('VALIDATION_RESULT',report['passed'],report['total'],flush=True)
