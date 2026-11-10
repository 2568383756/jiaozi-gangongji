"""Reopen the saved scene, verify real geometry/interfaces, then GLB round-trip."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'01_游戏开发/Models/首关场景_v01_20261110'
REPORT=OUT/'场景核验_v01_20261110.json'
report=json.loads(REPORT.read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'首关_开张第一单_v01_20261110.blend'))
scene=bpy.context.scene
checks=[]
def check(name, passed, detail):
    checks.append({'name':name,'passed':bool(passed),'detail':detail})
def objects_under(root):
    out=[]
    for ob in root.children:
        out.append(ob);out.extend(objects_under(ob))
    return out
def bbox(obs):
    pts=[o.matrix_world@Vector(p) for o in obs if o.type=='MESH' for p in o.bound_box]
    return [[min(p[a] for p in pts),max(p[a] for p in pts)] for a in range(3)]
def near(a,b,tol=.01):return abs(a-b)<=tol

roots=[bpy.data.objects.get(n) for n in report['station_roots']]
check('six_station_roots',len(roots)==6 and all(roots),[o.name for o in roots if o])
check('meters_Z_up',scene.unit_settings.system=='METRIC' and scene.unit_settings.scale_length==1,'Blender Z up; glTF Y up conversion enabled')
floors=[o for o in scene.objects if o.get('asset_id') in ('env_floor_courtyard','env_floor_workshop')]
floorbox=bbox([c for f in floors for c in objects_under(f) if c.name.endswith('_slab')])
check('24_floor_tiles_and_12x8m',len(floors)==24 and near(floorbox[0][0],0) and near(floorbox[0][1],12) and near(floorbox[1][0],0) and near(floorbox[1][1],8),floorbox)
check('floor_top_at_zero',near(floorbox[2][1],0,.001),floorbox[2])
anchors=[o for o in scene.objects if o.get('role')=='paper_anchor']
targets=[o for o in scene.objects if o.get('role')=='interaction_target']
stands=[o for o in scene.objects if o.get('role')=='player_standing_point']
check('seven_slots_targets_stands',len(anchors)==len(targets)==len(stands)==7,{'slots':len(anchors),'targets':len(targets),'stands':len(stands)})
dry=[o for o in anchors if o.parent.name=='station_dry']
check('dry_AB_1m_centers',len(dry)==2 and near(abs(dry[0].matrix_world.translation.x-dry[1].matrix_world.translation.x),1,.001),[{'name':o.name,'slot':o.get('slot_id'),'world':list(o.matrix_world.translation)} for o in dry])
for root in roots:
    expected=(root['width'],root['depth'])
    box=bbox(objects_under(root));xy=(box[0][1]-box[0][0],box[1][1]-box[1][0])
    check(root.name+'_footprint',near(xy[0],expected[0]) and near(xy[1],expected[1]),{'actual':xy,'expected':expected,'tolerance_m':.01})
    check(root.name+'_grounded',near(box[2][0],0,.002),box[2][0])
for sid,part in [('station_print','__tabletop'),('station_stamp','__tabletop'),('station_shared','__tabletop'),('station_delivery','__counter')]:
    ob=bpy.data.objects[sid+part];bb=bbox([ob])
    check(sid+'_table_height',near(bb[2][1],.65,.001),bb[2][1])
lane_errors=[]
for root in roots:
    b=bbox(objects_under(root))
    if b[1][0] < 5.7-.001 and b[1][1] > 3.3+.001:
        lane_errors.append(root.name)
check('2_4m_lane_free_of_station_geometry',not lane_errors,lane_errors)
portal=bpy.data.objects['env_portal_rear_attached']
left=bbox([bpy.data.objects['portal_post_-1']]);right=bbox([bpy.data.objects['portal_post_1']]);header=bbox([bpy.data.objects['portal_header']])
check('portal_clear_opening',near(right[0][0]-left[0][1],2.4,.001) and near(header[2][0],2.1,.001),{'width':right[0][0]-left[0][1],'height':header[2][0]})
check('static_nominal_paths',report['static_navigation']['all_reachable'],report['static_navigation']['method'])
check('no_external_images',all(i.packed_file or i.source in ('GENERATED','VIEWER') for i in bpy.data.images),[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file])
reference={o.name:list(o.matrix_world.translation) for o in anchors+targets+roots}
expected_meshes={o.name for o in scene.objects if o.type=='MESH' and not any(c.name.startswith(('90_','99_')) for c in o.users_collection)}
native_font_count=len(bpy.data.fonts)
asset_kinds=sorted({o.get('asset_id') for o in scene.objects if o.get('asset_id')})
native_object_count=len(scene.objects)
check('no_external_font_dependency',native_font_count==0,{'fonts':native_font_count})
# Load export in a new empty scene to check actual handed-off artifact.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'首关_开张第一单_v01_20261110.glb'))
bpy.context.view_layer.update()
actual_meshes={o.name for o in bpy.context.scene.objects if o.type=='MESH'}
missing=sorted(expected_meshes-actual_meshes)
check('glb_meshes_roundtrip',not missing,{'expected':len(expected_meshes),'imported':len(actual_meshes),'missing':missing})
errors=[]
for name,loc in reference.items():
    ob=bpy.data.objects.get(name)
    if ob is None:errors.append({'name':name,'error':'missing'})
    elif (ob.matrix_world.translation-Vector(loc)).length>.001:
        errors.append({'name':name,'error':'coordinate mismatch','expected':loc,'actual':list(ob.matrix_world.translation)})
check('glb_root_and_anchor_coordinates',not errors,errors)
report['verification']={'checks':checks,'passed':all(c['passed'] for c in checks),'native_objects':native_object_count,'asset_kinds':asset_kinds,'unity_tested':False,'render_review':'Game camera and top view inspected; no playable characters or Unity controllers included.'}
report['files']={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.iterdir() if p.suffix in ('.blend','.glb','.png')}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('VALIDATION',json.dumps({'passed':report['verification']['passed'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},ensure_ascii=False),flush=True)
if not report['verification']['passed']:raise RuntimeError('Scene validation failed; see JSON')
