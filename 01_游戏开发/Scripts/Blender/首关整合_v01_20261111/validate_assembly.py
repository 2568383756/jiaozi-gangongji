"""Reopen the saved assembled BLEND and record concrete asset checks."""
from pathlib import Path
import bpy, json, hashlib, struct
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=ROOT/'01_游戏开发/Models/首关整合_v01_20261111'
path=OUT/'首关_角色道具整合_v01_20261111.blend'
report_path=OUT/'整合核验_v01_20261111.json'
report=json.loads(report_path.read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
scene=bpy.context.scene
checks=list(report.get('build_checks',report['checks'][:4]))
def check(name,condition,detail=None):
    checks.append(dict(name=name,pass_=bool(condition),detail=detail))
    checks[-1]['pass']=checks[-1].pop('pass_')
def descendants(root):
    result=[root]
    for o in root.children:result.extend(descendants(o))
    return result
def bounds(root):
    points=[];dg=bpy.context.evaluated_depsgraph_get()
    for ob in descendants(root):
        if ob.type!='MESH':continue
        eo=ob.evaluated_get(dg);me=eo.to_mesh()
        points.extend(eo.matrix_world@v.co for v in me.vertices);eo.to_mesh_clear()
    return [[min(p[k] for p in points),max(p[k] for p in points)] for k in range(3)]

check('saved_file_reopened',True)
loaded_interfaces={name:[round(float(x),7) for row in bpy.data.objects[name].matrix_world for x in row]
                   for name in report['interfaces'] if name in bpy.data.objects}
check('saved_21_interfaces_unchanged',loaded_interfaces==report['interfaces'] and len(loaded_interfaces)==21)
check('metric_units',scene.unit_settings.scale_length==1)
check('two_armatures',len([o for o in scene.objects if o.type=='ARMATURE'])==2)
check('packed_file_images',all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.users))
measurements=[]
for item in report['characters']:
    cid=item['id'];rig=bpy.data.objects['rig_'+cid]
    root=bpy.data.objects['character_'+cid];held=bpy.data.objects[item['carried_root']]
    check(cid+'_identity_scale',max(abs(s-1) for s in root.scale)<1e-6)
    check(cid+'_five_game_actions',all(bpy.data.actions.get(cid+'_'+n) for n in ['Idle','Walk','CarryIdle','CarryWalk','Work']))
    check(cid+'_one_sheet',held.parent.name==item['socket'])
    ranges=[]
    for clip in ['CarryIdle','CarryWalk']:
        action=bpy.data.actions[cid+'_'+clip]
        rig.animation_data.action=action
        if action.slots: rig.animation_data.action_slot=action.slots[0]
        for frame in range(1,66,8):
            scene.frame_set(frame);bpy.context.view_layer.update()
            b=bounds(held)
            expected=rig.matrix_world @ rig.pose.bones['HoldPoint'].matrix
            error=max(abs(expected[r][c]-held.matrix_world[r][c]) for r in range(4) for c in range(4))
            ranges.append({'clip':clip,'frame':frame,'z':b[2],'hold_bone_matrix_error':error})
    check(cid+'_paper_tracks_hold_bone',all(s['hold_bone_matrix_error']<1e-5 for s in ranges))
    check(cid+'_sampled_sheets_above_floor',all(s['z'][0]>.02 for s in ranges),ranges)
    check(cid+'_sampled_sheets_in_low_carry_band',all(s['z'][1]<.60 for s in ranges),
          'Art height envelope only, not a full triangle-intersection or face-occlusion test.')
    rig.animation_data.action=bpy.data.actions[cid+'_CarryIdle']
    if rig.animation_data.action.slots: rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    scene.frame_set(1);bpy.context.view_layer.update();b=bounds(held)
    measurements.append({'character':cid,'root_world':list(root.location),'carried_bounds':b,
                         'hold_world':list(held.matrix_world.translation)})

images=[]
for p in sorted(OUT.glob('*.png')):
    raw=p.read_bytes()
    w,h=struct.unpack('>II',raw[16:24])
    images.append({'file':p.name,'width':w,'height':h,'sha256':hashlib.sha256(raw).hexdigest()})
check('three_rendered_previews',len(images)==3 and all(i['width']==1920 and i['height']==1440 for i in images))
report['reopen_measurements']=measurements
report['previews']=images
report['checks']=checks
report['all_passed']=all(c['pass'] for c in checks)
report['blend_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ASSEMBLY_VALIDATION',len(checks),'PASS' if report['all_passed'] else 'FAIL',flush=True)
if not report['all_passed']:
    print([c for c in checks if not c['pass']]);raise RuntimeError('Assembly validation failed')
