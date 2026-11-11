"""Read-only Blender audit of existing character contact geometry; never saves BLEND."""
from pathlib import Path
import json, hashlib, math
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODELS = ROOT / '01_游戏开发/Models'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def bounds(points):
    if not points:
        return None
    return [[round(min(p[i] for p in points), 6), round(max(p[i] for p in points), 6)] for i in range(3)]

def vec(v):
    return [round(float(c), 6) for c in v]

def set_action(rig, action):
    rig.animation_data_create()
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]

result = {'scope': 'Read-only existing files, no IK solve, no saved model modification; mesh regions classified by dominant bone weight.',
          'blender': bpy.app.version_string, 'characters': {}, 'station_interfaces': [],
          'limitations': ['Vertex-in-slab checks are diagnostic only; they do not prove triangle/solid collision absence.',
                         'Bone centers are not physical palm surfaces; contact must use evaluated mesh or calibrated surface helpers.',
                         'No Unity runtime, physics, state ownership or input testing.']}
for cid, label in [('zhituan', '纸团'), ('yintao', '印桃')]:
    path = MODELS / '首批角色_v01_20261111' / f'角色_{label}_整合_v01_20261111.blend'
    original_sha = sha(path)
    bpy.ops.wm.open_mainfile(filepath=str(path))
    rig = bpy.data.objects[f'rig_{cid}']
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    groups = {}
    for ob in meshes:
        names = {g.index: g.name for g in ob.vertex_groups}
        by_name = {}
        for vertex in ob.data.vertices:
            dominant = max(vertex.groups, key=lambda g:g.weight, default=None)
            name = names.get(dominant.group, '') if dominant else ''
            by_name[vertex.index] = name
        groups[ob.name] = by_name
    char = {'source': str(path.relative_to(ROOT)), 'sha256_before': original_sha,
            'bone_lengths': {b.name: round(b.length,6) for b in rig.data.bones if any(k in b.name for k in ('arm','hand'))},
            'rest_bones': {b.name:{'head':vec(b.head_local), 'tail':vec(b.tail_local)} for b in rig.data.bones if any(k in b.name for k in ('arm','hand','head','chest','foot'))},
            'clips': {}}
    for clip, end in [('Work',31), ('CarryIdle',61), ('CarryWalk',65)]:
        action = bpy.data.actions[f'{cid}_{clip}']
        set_action(rig, action)
        samples = []
        for frame in sorted(set([1, end, 1+(end-1)//4, 1+(end-1)//2, 1+3*(end-1)//4])):
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            pts = {k:[] for k in ('all','head','torso','arms','hands','feet')}
            dominant_pts = {}
            for ob in meshes:
                evaluated = ob.evaluated_get(dg)
                mesh = evaluated.to_mesh()
                for v in mesh.vertices:
                    p = evaluated.matrix_world @ v.co
                    pts['all'].append(p)
                    bone = groups[ob.name].get(v.index, '')
                    dominant_pts.setdefault(bone, []).append(p)
                    if bone.startswith(('head','ribbon','pigtail')): region = 'head'
                    elif bone.startswith('hand'): region = 'hands'
                    elif 'arm' in bone: region = 'arms'
                    elif 'foot' in bone: region = 'feet'
                    else: region = 'torso'
                    pts[region].append(p)
                evaluated.to_mesh_clear()
            palms = {side: rig.matrix_world @ ((rig.pose.bones['hand_'+side].head+rig.pose.bones['hand_'+side].tail)*.5) for side in ('L','R')}
            shoulder = {side:rig.matrix_world @ rig.pose.bones['upper_arm_'+side].head for side in ('L','R')}
            samples.append({'frame':frame,'palms':{s:vec(v) for s,v in palms.items()}, 'shoulders':{s:vec(v) for s,v in shoulder.items()},
                            'mesh_bounds_by_dominant_bone':{k:bounds(v) for k,v in pts.items()},
                            'dominant_group_bounds':{k:bounds(v) for k,v in dominant_pts.items()},
                            'lower_body_z_slices':{f'{lo:.2f}-{hi:.2f}':bounds([p for p in pts['torso']+pts['feet'] if lo<=p.z<=hi]) for lo,hi in ((0,.12),(.12,.25),(.25,.35),(.35,.45))},
                            'lower_body_disc_candidates':[
                                {'center_y':cy,'radius_to_enclose_feet':round(max((math.hypot(p.x,p.y-cy) for p in pts['feet']),default=0),6),
                                 'radius_to_enclose_lower_non_arm_mesh_below_035':round(max((math.hypot(p.x,p.y-cy) for p in pts['torso']+pts['feet'] if p.z<.35),default=0),6)}
                                for cy in (-.06,-.04,-.02,0)],
                            'radial_extent_xy_by_region':{k:round(max((math.hypot(p.x,p.y) for p in v),default=0),6) for k,v in pts.items()},
                            'head_front_y_at_z_bands':{f'{lo:.2f}-{hi:.2f}':bounds([p for p in pts['head'] if lo<=p.z<=hi]) for lo,hi in ((.35,.45),(.45,.55),(.55,.65),(.65,.75))},
                            'candidate_table_slabs':[
                                {'platform_lift':lift,'root_edge_distance':edge,'table_top':top,
                                 'head_vertex_count_in_top_slab':sum(1 for p in pts['head'] if abs(p.x)<.8 and -edge-1.<p.y<-edge and top-.08<p.z+lift<top),
                                 'hand_vertex_count_in_top_slab':sum(1 for p in pts['hands'] if abs(p.x)<.8 and -edge-1.<p.y<-edge and top-.08<p.z+lift<top),
                                 'palm_center_z':[round(v.z+lift,6) for v in palms.values()],
                                 'palm_center_inward_of_edge':[round(-edge-v.y,6) for v in palms.values()]}
                                for lift,edge,top in ((0,.425,.65),(.24,.425,.65),(.24,.325,.65),(.24,.275,.65),(0,.275,.42))]})
        char['clips'][clip] = samples
    char['source_unchanged'] = sha(path) == original_sha
    result['characters'][cid] = char

scene_path = MODELS/'首关场景_v05_20261111/首关_开张第一单_v05_20261111.blend'
if scene_path.exists():
    scene_sha = sha(scene_path)
    bpy.ops.wm.open_mainfile(filepath=str(scene_path))
    for ob in bpy.context.scene.objects:
        if ob.get('role') in ('player_standing_point','interaction_target','paper_anchor'):
            result['station_interfaces'].append({'name':ob.name,'role':ob['role'],'position':vec(ob.matrix_world.translation)})
    result['scene_source']={'path':str(scene_path.relative_to(ROOT)),'sha256':scene_sha,'unchanged':sha(scene_path)==scene_sha}

out=HERE/'现有角色触台诊断_v01_20261111.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('AUDIT_SAVED',out)
