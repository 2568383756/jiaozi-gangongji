"""Saved-file, GLB reimport and delivery validation; no Unity runtime claims."""
from pathlib import Path
import bpy, hashlib, json, struct
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=ROOT/'01_游戏开发/Models/首关整合_v02_20261111'
REPORT=OUT/'触台整合核验_v02_20261111.json'
BLEND=OUT/'首关_触台比例整合_v02_20261111.blend'
report=json.loads(REPORT.read_text(encoding='utf-8'))
checks=[]
def check(name, condition, detail=None):
    checks.append({'name':name,'pass':bool(condition),'detail':detail})
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def vec(v):return [round(float(x),6) for x in v]
def glb_json(path):
    data=path.read_bytes();magic,version,total=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and total==len(data)
    length,kind=struct.unpack_from('<I4s',data,12);assert kind==b'JSON'
    return json.loads(data[20:20+length])

bpy.ops.wm.open_mainfile(filepath=str(BLEND),load_ui=False)
scene=bpy.context.scene
check('saved_blend_reopened',True)
check('one_unit_one_metre',scene.unit_settings.scale_length==1)
check('two_character_armatures',sum(o.type=='ARMATURE' for o in scene.objects)==2)
check('source_v01_assembly_unchanged',sha(ROOT/report['source'])==report['source_sha256'])
check('all_referenced_character_sources_match',all(sha(ROOT/x['source'])==x['sha256'] for x in report['characters']))
roles={'paper_anchor','interaction_target','player_standing_point'}
anchors={o.name:vec(o.matrix_world.translation) for o in scene.objects if o.get('role') in roles}
check('twenty_one_named_gameplay_interfaces',len(anchors)==21,anchors)
check('six_station_roots',all('station_'+s in bpy.data.objects for s in ['pulp','dry','print','stamp','delivery','shared']))
check('used_file_images_packed',all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.users))
for cid in ['zhituan','yintao']:
    root=bpy.data.objects['character_'+cid]
    rig=bpy.data.objects['rig_'+cid]
    mesh=bpy.data.objects['mesh_'+cid]
    check(cid+'_root_identity_scale',all(abs(x-1)<1e-6 for x in root.scale))
    check(cid+'_five_actions',all(cid+'_'+clip in bpy.data.actions for clip in ['Idle','Walk','CarryIdle','CarryWalk','Work']))
    check(cid+'_carry_sockets_preserved',all(n in rig.data.bones for n in ['HoldPoint','PalmCenter']))
    rig.animation_data.action=bpy.data.actions[cid+'_Work']
    if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    floor_samples=[]
    for frame in [1,6,11,16,21,26,31]:
        scene.frame_set(frame);bpy.context.view_layer.update()
        eo=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh()
        floor_samples.append({'frame':frame,'min_z':min((eo.matrix_world@v.co).z for v in me.vertices)})
        eo.to_mesh_clear()
    check(cid+'_work_feet_not_below_floor',all(v['min_z']>=-.005 for v in floor_samples),floor_samples)

roundtrips=[]
for item in report['exports']:
    path=ROOT/item['file'];data=glb_json(path)
    check(path.stem+'_sha256',sha(path)==item['sha256'])
    check(path.stem+'_embedded_images',bool(data.get('images')) and all('bufferView' in x for x in data['images']))
    check(path.stem+'_static_only',not data.get('skins') and not data.get('animations'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    count=sum(o.type=='MESH' for o in bpy.context.scene.objects)
    check(path.stem+'_mesh_count_roundtrip',count==item['mesh_count'],{'expected':item['mesh_count'],'actual':count})
    errors={}
    if path.parent==OUT:
        for name,position in anchors.items():
            ob=bpy.data.objects.get(name)
            errors[name]=None if ob is None else (ob.matrix_world.translation-Vector(position)).length
        check('environment_21_anchor_positions_roundtrip',all(v is not None and v<1e-5 for v in errors.values()),errors)
    else:
        root=bpy.data.objects.get(path.stem)
        check(path.stem+'_zero_local_root',root is not None and root.matrix_world.translation.length<1e-6)
    roundtrips.append({'file':item['file'],'meshes':count,'images':len(data.get('images',[])),'anchor_errors':errors})
images=[]
for p in sorted(OUT.glob('*.png')):
    raw=p.read_bytes();w,h=struct.unpack('>II',raw[16:24])
    images.append({'file':p.name,'width':w,'height':h,'sha256':sha(p)})
check('six_review_renders',len(images)==6 and all(x['width']==1920 and x['height']==1440 for x in images))
report.update({'delivery_checks':checks,'delivery_check_count':len(checks),
    'delivery_all_passed':all(c['pass'] for c in checks),'glb_roundtrips':roundtrips,
    'previews':images,'saved_gameplay_interfaces':anchors,'blend_sha256':sha(BLEND),
    'validation_boundary':'Asset and geometry checks only; other developer Unity runtime remains untested.'})
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('CONTACT_DELIVERY_CHECKS',len(checks),'PASS' if report['delivery_all_passed'] else 'FAIL',flush=True)
if not report['delivery_all_passed']:
    print([x for x in checks if not x['pass']],flush=True)
    raise RuntimeError('Contact delivery validation failed')
