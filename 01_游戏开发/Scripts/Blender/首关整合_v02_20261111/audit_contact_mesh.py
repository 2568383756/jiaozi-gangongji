"""Independent evaluated-mesh contact and body/station intersection audit.

Samples both characters at seven operating points. Broad phase uses AABBs;
reported intersections use triangle BVHs, not overlapping bounding boxes.
Hands are excluded from body intersections because contact is intentional;
their actual skinned vertex probes are checked separately against real surfaces.
"""
from pathlib import Path
import bpy, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OUT=ROOT/'01_游戏开发/Models/首关整合_v02_20261111'
assembly=json.loads((OUT/'触台整合核验_v02_20261111.json').read_text(encoding='utf-8'))
character_report=json.loads((ROOT/'01_游戏开发/Models/首批角色_v02_20261111/角色触台报告_v02_20261111.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'首关_触台比例整合_v02_20261111.blend'),load_ui=False)
scene=bpy.context.scene

def descendants(o):
    result=[o]
    for child in o.children:result.extend(descendants(child))
    return result
def vec(v):return [round(float(x),7) for x in v]
def bounds(points):return [Vector(tuple(min(p[k] for p in points) for k in range(3))),Vector(tuple(max(p[k] for p in points) for k in range(3)))]
def boxes_overlap(a,b):return all(a[0][k] <= b[1][k] and b[0][k] <= a[1][k] for k in range(3))
def mesh_data(ob,exclude_hands=False):
    eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=eo.to_mesh()
    mesh.calc_loop_triangles();points=[eo.matrix_world@v.co for v in mesh.vertices]
    hand_vertices=set()
    hand_materials={i for i,mat in enumerate(ob.data.materials) if mat and '_SolidHand_' in mat.name}
    if exclude_hands and not hand_materials:
        names={g.index:g.name for g in ob.vertex_groups}
        for v in ob.data.vertices:
            if v.groups and names[max(v.groups,key=lambda g:g.weight).group] in {'hand_L','hand_R'}:
                hand_vertices.add(v.index)
    # Sleeve linings can legitimately be weighted to a hand bone. Only the
    # explicit skin materials are contact hands; lining stays in body checks.
    triangles=[tuple(t.vertices) for t in mesh.loop_triangles
        if not (exclude_hands and hand_materials and mesh.polygons[t.polygon_index].material_index in hand_materials)
        and not any(i in hand_vertices for i in t.vertices)]
    eo.to_mesh_clear()
    if not triangles:return None
    return {'points':points,'triangles':triangles,'bounds':bounds(points),
            'bvh':BVHTree.FromPolygons(points,triangles,all_triangles=True,epsilon=0)}

station_meshes={}
for station in assembly['station_adaptation']['stations']:
    root=bpy.data.objects[station['id']]
    station_meshes[station['id']]=[(ob.name,mesh_data(ob)) for ob in descendants(root)
        if ob.type=='MESH' and not ob.hide_render and not ob.hide_viewport]

checks=[];cases=[]
def check(name,condition,detail=None):checks.append({'name':name,'pass':bool(condition),'detail':detail})
for cid in ['zhituan','yintao']:
    root=bpy.data.objects['character_'+cid];rig=bpy.data.objects['rig_'+cid];mesh=bpy.data.objects['mesh_'+cid]
    rig.animation_data.action=bpy.data.actions[cid+'_Work']
    if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    # Frame-1 lower-surface vertices independently inspected in the source mesh.
    probes=next(c['contact_probe_vertices'] for c in character_report['characters'] if c['character_id']==cid)
    group_names={g.index:g.name for g in mesh.vertex_groups}
    foot_ids={side:[v.index for v in mesh.data.vertices if v.groups and group_names[max(v.groups,key=lambda g:g.weight).group]=='foot_'+side] for side in ['L','R']}
    for station in assembly['station_adaptation']['stations']:
        for wf in station['work_frames']:
            root.location=wf['standing_world'];root.rotation_euler=(0,0,math.radians(wf['facing_z_degrees']))
            samples=[]
            for frame in [1,8,16,24,31]:
                scene.frame_set(frame);bpy.context.view_layer.update();body=mesh_data(mesh,True)
                intersections=[]
                for name,part in station_meshes[station['id']]:
                    if part and boxes_overlap(body['bounds'],part['bounds']):
                        hits=body['bvh'].overlap(part['bvh'])
                        if hits:
                            inv=root.matrix_world.inverted()
                            examples=[]
                            names={g.index:g.name for g in mesh.vertex_groups}
                            for ci,si in hits[:3]:
                                ids=body['triangles'][ci]
                                examples.append({'vertex_ids':list(ids),'posed_character_local':[vec(inv@body['points'][i]) for i in ids],
                                    'dominant_bones':[names[max(mesh.data.vertices[i].groups,key=lambda g:g.weight).group] for i in ids]})
                            intersections.append({'object':name,'triangle_pairs':len(hits),'examples':examples})
                contacts=[]
                if frame in (1,31):
                    for side,vertex_id in probes.items():
                        point=body['points'][vertex_id]
                        nearest=[]
                        for name,part in station_meshes[station['id']]:
                            if not part or name not in wf['allowed_contact_surface_names']:continue
                            result=part['bvh'].find_nearest(point)
                            if result[0] is not None:nearest.append((result[3],name,vec(result[0])))
                        if not nearest:raise RuntimeError('Missing actual named contact surface '+str(wf['allowed_contact_surface_names']))
                        distance,name,hit=min(nearest)
                        contacts.append({'side':side,'vertex_id':vertex_id,'world':vec(point),
                                         'nearest_surface':name,'distance_m':distance,'surface_point':hit})
                samples.append({'frame':frame,'body_intersections':intersections,'contacts':contacts,
                                'mesh_floor_z':float(body['bounds'][0].z),
                                'foot_min_z':{side:min(body['points'][i].z for i in ids) for side,ids in foot_ids.items()}})
            label=cid+'_'+station['id']+'_'+str(wf['slot'] or 'main')
            check(label+'_no_body_triangles_cross_station',not any(x['body_intersections'] for x in samples))
            check(label+'_both_feet_grounded',all(-.005<=z<=.010 for s in samples for z in s['foot_min_z'].values()))
            check(label+'_real_palm_contacts_within_2mm',all(c['distance_m']<=.002 for s in samples for c in s['contacts']))
            cases.append({'character':cid,'station':station['id'],'slot':wf['slot'],'standing_world':wf['standing_world'],
                          'samples':samples})
            print('MESH_CASE',label,'hits',sum(len(s['body_intersections']) for s in samples),flush=True)

dual_cases=[]
dry=next(s for s in assembly['station_adaptation']['stations'] if s['id']=='station_dry')
for ordering in [('zhituan','yintao'),('yintao','zhituan')]:
    for cid,slot in zip(ordering,['A','B']):
        wf=next(w for w in dry['work_frames'] if w['slot']==slot)
        root=bpy.data.objects['character_'+cid]
        root.location=wf['standing_world'];root.rotation_euler=(0,0,math.radians(wf['facing_z_degrees']))
    collisions=[]
    for frame in [1,16,31]:
        scene.frame_set(frame);bpy.context.view_layer.update()
        a=mesh_data(bpy.data.objects['mesh_'+ordering[0]])
        b=mesh_data(bpy.data.objects['mesh_'+ordering[1]])
        collisions.append({'frame':frame,'triangle_pairs':len(a['bvh'].overlap(b['bvh']))})
    check('dual_drying_'+ordering[0]+'_at_A_no_character_mesh_intersections',all(c['triangle_pairs']==0 for c in collisions))
    dual_cases.append({'A':ordering[0],'B':ordering[1],'frames':collisions})

report={'version':'v01_20261111','method':'Evaluated triangles; only explicit _SolidHand_ skin materials excluded from body BVH, sleeve linings included; real palm probes nearest named allowed surfaces.',
        'frames':[1,8,16,24,31],'cases':cases,'checks':checks,'check_count':len(checks),
        'dual_drying_cases':dual_cases,
        'all_passed':all(c['pass'] for c in checks),'unity_physics_tested':False,
        'limits':'Five sampled pose frames for station/body intersections; does not prove every interpolated instant, navigation or the runtime controller.'}
(OUT/'触台网格独立核验_v01_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('CONTACT_MESH_AUDIT',len(checks),'PASS' if report['all_passed'] else 'FAIL',flush=True)
if not report['all_passed']:raise RuntimeError('Contact geometry requires review; inspect JSON case details')
