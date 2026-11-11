"""Reopen the saved scene, verify real geometry/interfaces, then GLB round-trip."""
import bpy, json, hashlib, struct
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'01_游戏开发/Models/首关场景_v04_20261111'
REPORT=OUT/'场景核验_v04_20261111.json'
report=json.loads(REPORT.read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'首关_开张第一单_v04_20261111.blend'))
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
portal_intruders=[]
for ob in objects_under(portal):
    if ob.type!='MESH':continue
    verts=[ob.matrix_world@v.co for v in ob.data.vertices]
    for face in ob.data.polygons:
        ps=[verts[i] for i in face.vertices]
        if (min(p.x for p in ps)<7.2-.001 and max(p.x for p in ps)>4.8+.001
            and min(p.z for p in ps)<2.1-.001 and max(p.z for p in ps)>.001):
            portal_intruders.append(ob.name);break
check('portal_ornaments_keep_clear_opening',not portal_intruders,portal_intruders)
check('static_nominal_paths',report['static_navigation']['all_reachable'],report['static_navigation']['method'])
decor=[bpy.data.objects[n] for n in report['decoration_roots']]
ground_decor=[o for o in decor if 'footprint' in o]
decor_lane=[];decor_stands=[];decor_overlaps=[]
for root in ground_decor:
    b=bbox(objects_under(root))
    if b[1][0]<5.7-.001 and b[1][1]>3.3+.001:decor_lane.append(root.name)
    for stand in stands:
        p=stand.matrix_world.translation
        dx=max(b[0][0]-p.x,0,p.x-b[0][1]);dy=max(b[1][0]-p.y,0,p.y-b[1][1])
        if (dx*dx+dy*dy)**.5<.375:decor_stands.append([root.name,stand.name])
    for station in roots:
        sb=bbox(objects_under(station))
        if min(b[0][1],sb[0][1])-max(b[0][0],sb[0][0])>.001 and min(b[1][1],sb[1][1])-max(b[1][0],sb[1][0])>.001:
            decor_overlaps.append([root.name,station.name])
check('decor_leaves_main_lane_clear',not decor_lane,decor_lane)
check('decor_clear_of_operating_stands',not decor_stands,decor_stands)
check('decor_does_not_overlap_workstations',not decor_overlaps,decor_overlaps)
check('decor_marked_noninteractive',all(o.get('non_interactive') for o in decor),[o.name for o in decor])
exterior=[bpy.data.objects[n] for n in report['exterior_roots']]
trees=[o for o in exterior if o.get('asset_id')=='env_ginkgo']
check('three_ginkgo_trees',len(trees)==3,[o.name for o in trees])
beds=[o for o in exterior if o.get('asset_id')=='env_planting_bed']
check('eight_low_planting_beds',len(beds)==8,[o.name for o in beds])
grass_roots=beds+[o for o in exterior if o.get('asset_id')=='env_grass_cluster']
check('all_grass_uses_rounded_paper_style',len(grass_roots)==30 and all(o.get('foliage_style')=='rounded_folded_paper' for o in grass_roots),{'groups':len(grass_roots),'styles':sorted({o.get('foliage_style','missing') for o in grass_roots})})
check('exterior_marked_noninteractive',all(o.get('non_interactive') for o in exterior),len(exterior))
outer_ground=[o for o in exterior if o.get('role')=='exterior_ground']
outer_box=bbox([c for root in outer_ground for c in objects_under(root)]) if outer_ground else None
check('exterior_ground_20x15m',outer_box is not None and near(outer_box[0][0],-4) and near(outer_box[0][1],16) and near(outer_box[1][0],-3.5) and near(outer_box[1][1],11.5),outer_box)
intruders=[];entry_blockers=[]
for root in exterior:
    if root.get('role') in ('exterior_ground','exterior_path'):continue
    for ob in objects_under(root):
        if ob.type!='MESH':continue
        verts=[ob.matrix_world@v.co for v in ob.data.vertices]
        for face in ob.data.polygons:
            ps=[verts[i] for i in face.vertices]
            xs=[p.x for p in ps];ys=[p.y for p in ps];zs=[p.z for p in ps]
            if min(xs)<12-.001 and max(xs)>0+.001 and min(ys)<8-.001 and max(ys)>0+.001 and max(zs)>.001:
                intruders.append(ob.name);break
            if min(xs)<7.2-.001 and max(xs)>4.8+.001 and max(zs)>.20:
                if (min(ys)<0 and max(ys)>-3.5) or (min(ys)<11.5 and max(ys)>8):
                    entry_blockers.append(ob.name);break
check('exterior_stays_outside_work_area',not intruders,sorted(set(intruders)))
check('front_and_rear_approaches_clear',not entry_blockers,sorted(set(entry_blockers)))
previous=json.loads((ROOT/'01_游戏开发/Models/首关场景_v03_20261110/场景核验_v03_20261110.json').read_text(encoding='utf-8'))
# Ornament heights may change; footprints, roots and gameplay interfaces must not.
xy_changes=[]
for name,box in report['station_geometry_bounds'].items():
    old=previous['station_geometry_bounds'][name]
    if any(not near(box[a][b],old[a][b],.01) for a in (0,1) for b in (0,1)):
        xy_changes.append({'name':name,'old':old[:2],'new':box[:2]})
check('station_xy_bounds_preserved_from_v03',not xy_changes,xy_changes)
spec=json.loads((ROOT/'01_游戏开发/Art/场景关卡/首关三视图_v02_20261110/尺寸与布局_v02_20261110.json').read_text(encoding='utf-8-sig'))
root_changes=[]
for s in spec['stations']:
    expected=Vector((*s['center_xz'],0))
    if (bpy.data.objects[s['id']].matrix_world.translation-expected).length>.001:root_changes.append(s['id'])
check('station_root_centers_match_dimensions',not root_changes,root_changes)
old_anchors={a['name']:a for a in previous['anchors']}
interface_changes=[]
for a in report['anchors']:
    if a['role'] not in ('paper_anchor','interaction_target','player_standing_point'):continue
    old=old_anchors.get(a['name'])
    if not old or old['parent']!=a['parent'] or old['role']!=a['role'] or (Vector(old['local'])-Vector(a['local'])).length>.001:
        interface_changes.append(a['name'])
check('all_gameplay_anchor_interfaces_preserved_from_v03',not interface_changes,interface_changes)
gamecam=bpy.data.objects['CAM_Gameplay_Orthographic']
check('game_camera_preserved',near(gamecam.data.ortho_scale,14.4,.001) and (gamecam.location-Vector((6.3,-13,18.3))).length<.001,{'location':list(gamecam.location),'ortho_scale':gamecam.data.ortho_scale})
from bpy_extras.object_utils import world_to_camera_view
overview=bpy.data.objects['CAM_Exterior_Overview']
projected=[world_to_camera_view(scene,overview,ob.matrix_world@Vector(p))
    for ob in scene.objects if ob.type=='MESH' and not any(c.name.startswith(('90_','99_')) for c in ob.users_collection)
    for p in ob.bound_box]
frame_range=[[min(p[i] for p in projected),max(p[i] for p in projected)] for i in range(2)]
check('overview_contains_full_scene',all(a>=.015 and b<=.985 for a,b in frame_range),frame_range)
check('packed_paper_materials',len([i for i in bpy.data.images if i.packed_file])>=2,{'packed_images':len([i for i in bpy.data.images if i.packed_file])})
check('no_external_images',all(i.packed_file or i.source in ('GENERATED','VIEWER') for i in bpy.data.images),[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file])
reference={o.name:list(o.matrix_world.translation) for o in anchors+targets+roots+exterior}
expected_meshes={o.name for o in scene.objects if o.type=='MESH' and not any(c.name.startswith(('90_','99_')) for c in o.users_collection)}
native_font_count=len(bpy.data.fonts)
asset_kinds=sorted({o.get('asset_id') for o in scene.objects if o.get('asset_id')})
native_object_count=len(scene.objects)
check('no_external_font_dependency',native_font_count==0,{'fonts':native_font_count})
previews={p.name:list(struct.unpack('>II',p.read_bytes()[16:24])) for p in OUT.glob('预览_*_v04_20261111.png')}
check('seven_previews_at_1920x1440',len(previews)==7 and all(size==[1920,1440] for size in previews.values()),previews)
report['preview_images']=previews
report['rendering']['denoiser']=scene.cycles.denoiser
report['rendering']['use_denoising']=scene.cycles.use_denoising
report['rendering']['resolution']=[scene.render.resolution_x,scene.render.resolution_y]
# Load export in a new empty scene to check actual handed-off artifact.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'首关_开张第一单_v04_20261111.glb'))
bpy.context.view_layer.update()
actual_meshes={o.name for o in bpy.context.scene.objects if o.type=='MESH'}
missing=sorted(expected_meshes-actual_meshes)
check('glb_meshes_roundtrip',not missing,{'expected':len(expected_meshes),'imported':len(actual_meshes),'missing':missing})
normal_nodes=sum(n.type=='NORMAL_MAP' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes)
check('glb_paper_textures_and_normals',len(bpy.data.images)>=2 and normal_nodes>0,{'images':len(bpy.data.images),'normal_map_nodes':normal_nodes})
errors=[]
for name,loc in reference.items():
    ob=bpy.data.objects.get(name)
    if ob is None:errors.append({'name':name,'error':'missing'})
    elif (ob.matrix_world.translation-Vector(loc)).length>.001:
        errors.append({'name':name,'error':'coordinate mismatch','expected':loc,'actual':list(ob.matrix_world.translation)})
check('glb_root_and_anchor_coordinates',not errors,errors)
report['verification']={'checks':checks,'passed':all(c['passed'] for c in checks),'native_objects':native_object_count,'asset_kinds':asset_kinds,'unity_tested':False,'render_review':'See production notes for visual review; automated checks validate geometry and export, not artistic quality.'}
report['files']={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.iterdir() if p.suffix in ('.blend','.glb','.png')}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('VALIDATION',json.dumps({'passed':report['verification']['passed'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},ensure_ascii=False),flush=True)
if not report['verification']['passed']:raise RuntimeError('Scene validation failed; see JSON')
