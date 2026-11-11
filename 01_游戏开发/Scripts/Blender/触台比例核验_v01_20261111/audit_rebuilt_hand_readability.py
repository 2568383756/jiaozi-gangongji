"""Independent read-only audit of evaluated hand support and closed geometry.

Does not import the hand generator or save a Blender file. This is a geometric
diagnostic, not a substitute for inspecting the hand / cuff silhouettes.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--final', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
BASE = ROOT / '01_游戏开发/Models/首批角色_v02_20261111'
report = {'scope': 'Read-only evaluated geometry; no source modifications; no Unity validation.',
          'band_tolerance_m': .002, 'final_files': args.final, 'characters': {}}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rv(vec):
    return [round(float(v), 7) for v in vec]


def topology(polygons):
    edges = Counter()
    neighbours = defaultdict(set)
    verts = set()
    for face in polygons:
        verts.update(face)
        for a, b in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((a, b)))] += 1
            neighbours[a].add(b)
            neighbours[b].add(a)
    seen = set()
    components = 0
    for start in verts:
        if start in seen:
            continue
        components += 1
        pending = [start]
        while pending:
            cur = pending.pop()
            if cur in seen:
                continue
            seen.add(cur)
            pending.extend(neighbours[cur] - seen)
    return {'vertices': len(verts), 'edges': len(edges), 'polygons': len(polygons),
            'components': components, 'euler_characteristic': len(verts)-len(edges)+len(polygons),
            'boundary_edges': sum(v == 1 for v in edges.values()),
            'non_manifold_edges': sum(v != 2 for v in edges.values())}


for cid, label in [('zhituan', '纸团'), ('yintao', '印桃')]:
    path = (BASE / ('角色_' + label + '_整合_v02_20261111.blend') if args.final else
            BASE / 'work/hand_draft' / ('角色_' + label + '_新手草稿.blend'))
    initial_sha = digest(path)
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    rig = bpy.data.objects['rig_' + cid]
    obj = bpy.data.objects['mesh_' + cid]
    names = {g.index: g.name for g in obj.vertex_groups}
    dominant = {v.index: names[max(v.groups, key=lambda g: g.weight).group]
                for v in obj.data.vertices if v.groups}
    skin_materials = {i for i, material in enumerate(obj.data.materials)
                      if material and '_SolidHand_' in material.name}
    assert skin_materials, 'Explicit new hand skin materials are required.'
    skin_vertices = {i for p in obj.data.polygons if p.material_index in skin_materials for i in p.vertices}
    hand_ids = {side: {i for i, n in dominant.items() if n == 'hand_' + side and i in skin_vertices}
                for side in ('L', 'R')}
    forearm_ids = {side: {i for i, n in dominant.items()
                         if n in ('forearm_' + side, 'hand_' + side) and i not in skin_vertices}
                   for side in ('L', 'R')}
    # The lowest chin faces in the source rig belong to neck, not head.
    head_ids = {i for i, n in dominant.items() if n in ('head', 'neck')}
    paper_path = ROOT / '01_游戏开发/Models/首关道具_v01_20261111/GLB/paper_black.glb'
    before_objects = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(paper_path))
    paper_objects = set(bpy.data.objects) - before_objects
    paper_roots = [o for o in paper_objects if o.parent not in paper_objects]
    assert len(paper_roots) == 1, 'Paper GLB must have one explicit attachment root.'
    paper_root = paper_roots[0]
    paper_body = [o for o in paper_objects if o.type == 'MESH' and '__paper_body' in o.name]
    assert len(paper_body) == 1, 'Actual paper body mesh is required for bottom-plane measurement.'
    body_part = paper_body[0]
    body_local = [paper_root.matrix_world.inverted() @ body_part.matrix_world @ v.co for v in body_part.data.vertices]
    paper_bottom_local_z = min(p.z for p in body_local)
    report['paper_asset'] = {'file': str(paper_path.relative_to(ROOT)),
                             'sha256': digest(paper_path), 'attachment': 'Root matrix equals HoldPoint world matrix.',
                             'single_actual_asset_root': True,
                             'mesh_parts': sorted(o.name for o in paper_objects if o.type == 'MESH'),
                             'actual_body_bottom_local_z':paper_bottom_local_z,
                             'actual_body_local_bounds':[[min(p[k] for p in body_local),max(p[k] for p in body_local)] for k in range(3)],
                             'not_overlay': True}
    topologies = {}
    for side, ids in hand_ids.items():
        faces = [tuple(p.vertices) for p in obj.data.polygons if set(p.vertices) <= ids]
        topologies[side] = topology(faces)
    records = []
    poses = [('Work', 'Work'), ('Carry', 'CarryIdle'), ('Carry', 'CarryWalk')] if args.final else [('Work', 'DRAFT_Work'), ('Carry', 'DRAFT_Carry')]
    for kind, action_suffix in poses:
        action = bpy.data.actions[cid + '_' + action_suffix]
        rig.animation_data.action = action
        if action.slots:
            rig.animation_data.action_slot = action.slots[0]
        frames = range(round(action.frame_range[0]), round(action.frame_range[1])+1) if args.final else (1,)
        for frame in frames:
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            mesh.calc_loop_triangles()
            points = [evaluated.matrix_world @ v.co for v in mesh.vertices]
            triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
            head_tri = [t for t in triangles if set(t) <= head_ids]
            head_bvh = BVHTree.FromPolygons(points, head_tri, all_triangles=True)
            hold = rig.matrix_world @ rig.pose.bones['HoldPoint'].matrix
            origin = Vector((0, 0, .350)) if kind == 'Work' else hold @ Vector((0, 0, paper_bottom_local_z))
            normal = Vector((0, 0, 1)) if kind == 'Work' else hold.to_3x3().col[2].normalized()
            item = {'pose': kind, 'action': action.name, 'frame': frame,
                    'target_plane_origin': rv(origin), 'target_plane_normal': rv(normal),
                    'hands': {}}
            if kind == 'Carry':
                paper_root.matrix_world = hold
                bpy.context.view_layer.update()
                paper_points, paper_triangles = [], []
                for part in paper_objects:
                    if part.type != 'MESH':
                        continue
                    pe = part.evaluated_get(bpy.context.evaluated_depsgraph_get())
                    pm = pe.to_mesh()
                    pm.calc_loop_triangles()
                    offset = len(paper_points)
                    paper_points.extend(pe.matrix_world @ v.co for v in pm.vertices)
                    paper_triangles.extend(tuple(offset + i for i in t.vertices) for t in pm.loop_triangles)
                    pe.to_mesh_clear()
                # Cuff linings partly use hand bone weights. Exempt only explicit
                # skin material faces, never every hand-weighted triangle.
                body_triangles = [tuple(t.vertices) for t in mesh.loop_triangles
                                  if mesh.polygons[t.polygon_index].material_index not in skin_materials]
                body_bvh = BVHTree.FromPolygons(points, body_triangles, all_triangles=True)
                paper_bvh = BVHTree.FromPolygons(paper_points, paper_triangles, all_triangles=True)
                overlaps = body_bvh.overlap(paper_bvh)
                item['actual_paper_nonhand_triangle_intersections'] = len(overlaps)
                item['paper_body_examples'] = [
                    {'body_triangle': body_triangles[a],
                     'dominant_groups': [dominant.get(i) for i in body_triangles[a]],
                     'world_xyz': [rv(points[i]) for i in body_triangles[a]]}
                    for a, b in overlaps[:2]]
            for side, ids in hand_ids.items():
                triangles_hand = [t for t in triangles if set(t) <= ids]
                hand_bvh = BVHTree.FromPolygons(points, triangles_hand, all_triangles=True)
                triangles_forearm = [t for t in triangles if set(t) <= forearm_ids[side]]
                forearm_bvh = BVHTree.FromPolygons(points, triangles_forearm, all_triangles=True)
                cuff_head_pairs = forearm_bvh.overlap(head_bvh)
                lining_tri = [tuple(t.vertices) for t in mesh.loop_triangles
                              if set(t.vertices) <= forearm_ids[side]
                              and 'WristLining' in mesh.materials[mesh.polygons[t.polygon_index].material_index].name]
                lining_bvh = BVHTree.FromPolygons(points, lining_tri, all_triangles=True)
                lining_head_pairs = lining_bvh.overlap(head_bvh)
                distances = {i: (points[i]-origin).dot(normal) for i in ids}
                near = [points[i] for i, d in distances.items() if abs(d) <= .002]
                item['hands'][side] = {
                    'min_plane_delta_m': round(min(distances.values()), 7),
                    'max_plane_delta_m': round(max(distances.values()), 7),
                    'support_band_vertex_count': len(near),
                    'support_band_xy_span_m': rv((max(p.x for p in near)-min(p.x for p in near),
                                                  max(p.y for p in near)-min(p.y for p in near))) if near else None,
                    'hand_head_triangle_intersections': len(hand_bvh.overlap(head_bvh)),
                    'forearm_and_cuff_head_triangle_intersections': len(cuff_head_pairs),
                    'new_wrist_lining_head_neck_triangle_intersections': len(lining_head_pairs),
                    'legacy_sleeve_head_neck_triangle_intersections': len(cuff_head_pairs)-len(lining_head_pairs),
                }
                if frame == 1 and cuff_head_pairs:
                    tri_material = {tuple(t.vertices): mesh.materials[mesh.polygons[t.polygon_index].material_index].name
                                    for t in mesh.loop_triangles}
                    item['hands'][side]['forearm_head_examples'] = [
                        {'forearm_triangle': triangles_forearm[a],
                         'forearm_material': tri_material[triangles_forearm[a]],
                         'forearm_xyz': [rv(points[i]) for i in triangles_forearm[a]],
                         'head_neck_triangle': head_tri[b],
                         'head_neck_groups': [dominant[i] for i in head_tri[b]],
                         'head_neck_material': tri_material[head_tri[b]],
                         'head_neck_xyz': [rv(points[i]) for i in head_tri[b]]}
                        for a, b in cuff_head_pairs[:4]]
            records.append(item)
            evaluated.to_mesh_clear()
    report['characters'][cid] = {'file': str(path.relative_to(ROOT)), 'sha256': initial_sha,
                                'source_file_unchanged': initial_sha == digest(path),
                                'head_collision_region': 'Combined head and neck dominant-weight faces, including lower jaw.',
                                'explicit_skin_hand_topology': topologies, 'samples': records}

all_rows = [r for c in report['characters'].values() for r in c['samples']]
all_hands = [h for r in all_rows for h in r['hands'].values()]
carry_rows = [r for r in all_rows if r['pose'] == 'Carry']
carry_hands = [h for r in carry_rows for h in r['hands'].values()]
topologies = [t for c in report['characters'].values() for t in c['explicit_skin_hand_topology'].values()]
core_checks = {
    'source_files_unchanged_during_read': all(c['source_file_unchanged'] for c in report['characters'].values()),
    'four_closed_connected_skin_hands': all(t['components']==1 and t['euler_characteristic']==2 and t['non_manifold_edges']==0 for t in topologies),
    'skin_hands_clear_head_and_lower_jaw': all(h['hand_head_triangle_intersections']==0 for h in all_hands),
    'new_wrist_lining_clear_head_and_lower_jaw': all(h['new_wrist_lining_head_neck_triangle_intersections']==0 for h in all_hands),
    'single_actual_carried_paper_clear_nonhand_body': all(r['actual_paper_nonhand_triangle_intersections']==0 for r in carry_rows),
    'carry_palms_touch_actual_paper_bottom_within_1mm': all(abs(h['max_plane_delta_m']) <= .001 and h['support_band_vertex_count']>=3 for h in carry_hands),
}
report['verification'] = {'core_pass': all(core_checks.values()), 'checks':core_checks,
    'sampled_character_pose_frames':len(all_rows),'carry_frames':len(carry_rows),
    'carry_skin_support_max_error_m':max(abs(h['max_plane_delta_m']) for h in carry_hands),
    'legacy_cloth_contact_observation': {
        'summed_original_sleeve_head_neck_triangle_pairs':sum(h['legacy_sleeve_head_neck_triangle_intersections'] for h in all_hands),
        'classification':'Additional original-sleeve contact observation; not a failure of the requested new hand / carried paper checks.',
        'baseline_report':'原袖下颌接触来源核查_v01_20261111.json',
        'note':'Original v01 sleeves also intersect the neck-weighted lower jaw. See source comparison for changed pose locations and local vertex-depth estimates. No clothing or face edits were made by this audit.'}}
out = HERE / ('新手最终独立核验_v01_20261111.json' if args.final else '新手草稿独立核验_v01_20261111.json')
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('INDEPENDENT_HAND_AUDIT', out)
