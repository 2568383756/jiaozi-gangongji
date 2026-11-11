"""Measure helper-to-surface distance after applying to the real v01 assembly."""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import adapt_stations
ROOT=HERE.parents[3]
OUT=ROOT/'01_游戏开发/Models/首关工位适配_v01_20261111';OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'01_游戏开发/Models/首关整合_v01_20261111/首关_角色道具整合_v01_20261111.blend'
sha_before=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
def rig_snapshot():
    return {o.name:{'matrix':[float(v) for row in o.matrix_world for v in row],
                    'bones':{b.name:[float(v) for row in b.matrix_local for v in row] for b in o.data.bones},
                    'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None}
            for o in bpy.context.scene.objects if o.type=='ARMATURE'}
rig_before=rig_snapshot()
report=adapt_stations.apply()
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
results=[]
for station in report['stations']:
    for work in station['work_frames']:
        available=[bpy.data.objects.get(name) for name in work['allowed_contact_surface_names']]
        available=[o for o in available if o and o.type=='MESH']
        for hand,info in work['tool_grips'].items():
            grip=bpy.data.objects[info['name']];point=grip.matrix_world.translation
            closest=None
            for ob in available:
                tree=BVHTree.FromObject(ob,dg)
                hit=tree.find_nearest(ob.matrix_world.inverted()@point)
                if hit[0] is None:continue
                world=ob.matrix_world@hit[0];distance=(world-point).length
                if closest is None or distance<closest['distance_m']:
                    closest={'surface':ob.name,'distance_m':distance,'point_world':list(world)}
            results.append({'station':station['id'],'slot':work['slot'],'hand':hand,
                            'grip':grip.name,'grip_world':list(point),'nearest_surface':closest,
                            'pass':closest is not None and closest['distance_m']<=.001})
checks=[{'name':'14_contact_helpers_on_real_mesh','pass':len(results)==14 and all(r['pass'] for r in results)},
        {'name':'character_armatures_unchanged','pass':rig_before==rig_snapshot()},
        {'name':'source_blend_sha_unchanged','pass':sha_before==hashlib.sha256(source.read_bytes()).hexdigest()}]
payload={'version':adapt_stations.VERSION,'blender':bpy.app.version_string,'method':'real evaluated triangle BVH nearest surface; root armature matrices/rest bones/actions compared',
         'contact_results':results,'checks':checks,'all_passed':all(c['pass'] for c in checks),
         'limitations':'This verifies station helper surfaces only. Character mesh collision across all Work frames is independently reviewed by the parent/review agents.'}
(OUT/'工位接口几何核验_v01_20261111.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print('CONTACT_CHECKS',checks,flush=True)
for entry in results:
    if not entry['pass']:print('CONTACT_MISS',entry,flush=True)
