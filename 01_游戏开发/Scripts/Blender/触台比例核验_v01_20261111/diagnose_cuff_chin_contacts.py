"""Read-only baseline comparison for original sleeve / lower-jaw surfaces."""
import bpy, json, hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
records={}
saved_pairs={}
for version in ('v02','v01'):
    path=ROOT/f'01_游戏开发/Models/首批角色_{version}_20261111/角色_纸团_整合_{version}_20261111.blend'
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
    ob=bpy.data.objects['mesh_zhituan'];rig=bpy.data.objects['rig_zhituan']
    names={g.index:g.name for g in ob.vertex_groups}
    dominant={v.index:names[max(v.groups,key=lambda g:g.weight).group] for v in ob.data.vertices if v.groups}
    sid=ob.data.attributes.get('source_original_vertex_id')
    mapping={v.index:(sid.data[v.index].value if sid else v.index) for v in ob.data.vertices}
    records[version]={'file':str(path.relative_to(ROOT)),'sha256':sha,'samples':[]}
    for action in ('Work','CarryIdle','CarryWalk'):
        a=bpy.data.actions['zhituan_'+action];rig.animation_data.action=a
        if a.slots:rig.animation_data.action_slot=a.slots[0]
        bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
        pp=[ev.matrix_world@v.co for v in me.vertices]
        # Excludes new lining by material, focuses only on original source sleeve.
        arm=[tuple(t.vertices) for t in me.loop_triangles
             if all(dominant.get(i) in ('forearm_L','forearm_R') for i in t.vertices)
             and 'WristLining' not in me.materials[me.polygons[t.polygon_index].material_index].name]
        jaw=[tuple(t.vertices) for t in me.loop_triangles if all(dominant.get(i) in ('head','neck') for i in t.vertices)]
        ab=BVHTree.FromPolygons(pp,arm,all_triangles=True);jb=BVHTree.FromPolygons(pp,jaw,all_triangles=True)
        overlaps=[(i,j) for i,j in ab.overlap(jb) if not set(arm[i]).intersection(jaw[j])]
        mapped={ (tuple(sorted(mapping[v] for v in arm[i])),tuple(sorted(mapping[v] for v in jaw[j]))) for i,j in overlaps }
        signed=[]
        for v in {v for i,j in overlaps for v in arm[i]}:
            nearest,normal,tri_index,distance=jb.find_nearest(pp[v])
            signed.append({'vertex':v,'source_vertex':mapping[v],
              'local_signed_distance_to_jaw_m':(pp[v]-nearest).dot(normal),
              'point_xyz':list(pp[v]),'nearest_jaw_xyz':list(nearest),'nearest_jaw_normal':list(normal)})
        signed.sort(key=lambda x:x['local_signed_distance_to_jaw_m'])
        current={'action':action,'frame':1,'original_sleeve_jaw_intersections_excluding_shared_vertices':len(overlaps),
                 'mapped_pairs':[[list(a),list(b)] for a,b in sorted(mapped)],
                 'local_vertex_intrusion_estimate_note':'Signed nearest-surface distance for intersecting sleeve vertices, not full mesh penetration depth.',
                 'deepest_signed_vertex_samples':signed[:5],
                 'examples':[]}
        for i,j in overlaps[:8]:
            current['examples'].append({'arm_triangle':arm[i],'jaw_triangle':jaw[j],
               'arm_xyz':[[round(float(c),7) for c in pp[v]] for v in arm[i]],
               'jaw_xyz':[[round(float(c),7) for c in pp[v]] for v in jaw[j]],
               'jaw_groups':[dominant[v] for v in jaw[j]]})
        if version=='v02':saved_pairs[action]=mapped
        else:
            current['final_pair_already_present_in_v01_count']=len(mapped & saved_pairs[action])
            current['final_intersecting_pair_count']=len(saved_pairs[action])
        records[version]['samples'].append(current);ev.to_mesh_clear()
    records[version]['file_unchanged']=sha==hashlib.sha256(path.read_bytes()).hexdigest()
(HERE/'原袖下颌接触来源核查_v01_20261111.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('CUFF_BASELINE_READY')
