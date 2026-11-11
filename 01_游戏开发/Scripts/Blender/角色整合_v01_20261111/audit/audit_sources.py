import bpy, json, hashlib, math, traceback
from pathlib import Path
from mathutils import Vector

ROOT=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发')
SOURCE=ROOT/'Imports/角色源仓_20261111/source_checkout/deliverables'
OUT=ROOT/'Scripts/Blender/角色整合_v01_20261111/audit'

def vec(v): return [round(float(x),7) for x in v]
def bounds(points):
    lo=[min(p[k] for p in points) for k in range(3)]
    hi=[max(p[k] for p in points) for k in range(3)]
    return {'min':vec(lo),'max':vec(hi),'size':vec([hi[k]-lo[k] for k in range(3)])}
def curves(action):
    result=[]
    if hasattr(action,'fcurves'): result.extend(action.fcurves)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in getattr(strip,'channelbags',[]): result.extend(bag.fcurves)
    return result
def set_action(rig,action):
    rig.animation_data_create(); rig.animation_data.action=action
    slots=list(action.slots)
    if slots: rig.animation_data.action_slot=slots[0]

report={'blender':bpy.app.version_string,'source_commit':'86562a37fb6cf75f0ea41419b072b4129f207538','files':[]}
for path in sorted(SOURCE.glob('*.blend')):
    try:
        bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
        scene=bpy.context.scene
        rec={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'fps':scene.render.fps/scene.render.fps_base,'frame_range':[scene.frame_start,scene.frame_end],
             'unit_system':scene.unit_settings.system,'unit_scale':scene.unit_settings.scale_length,
             'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None} for o in scene.objects],
             'meshes':[],'rigs':[],'actions':[]}
        rigs=[o for o in scene.objects if o.type=='ARMATURE']
        for rig in rigs:
            rig.data.pose_position='REST'
            rec['rigs'].append({'name':rig.name,'location':vec(rig.location),'rotation':vec(rig.rotation_euler),
                'scale':vec(rig.scale),'bone_count':len(rig.data.bones),
                'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,
                          'head':vec(rig.matrix_world@b.head_local),'tail':vec(rig.matrix_world@b.tail_local),
                          'deform':b.use_deform} for b in rig.data.bones],
                'constraints':[{'bone':p.name,'constraints':[c.type for c in p.constraints]} for p in rig.pose.bones if p.constraints],
                'active_action':rig.animation_data.action.name if rig.animation_data and rig.animation_data.action else None,
                'nla_tracks':[t.name for t in rig.animation_data.nla_tracks] if rig.animation_data else []})
        bpy.context.view_layer.update()
        all_points=[]
        for ob in [o for o in scene.objects if o.type=='MESH']:
            me=ob.data;me.calc_loop_triangles()
            pts=[ob.matrix_world@v.co for v in me.vertices]
            is_skin=any(m.type=='ARMATURE' for m in ob.modifiers)
            if is_skin: all_points.extend(pts)
            maxinf=0;bad=0;unweighted=0
            for v in me.vertices:
                ws=[g.weight for g in v.groups if g.weight>1e-7]
                maxinf=max(maxinf,len(ws))
                if not ws:unweighted+=1
                elif abs(sum(ws)-1)>1e-4:bad+=1
            rec['meshes'].append({'name':ob.name,'skinned':is_skin,'vertices':len(me.vertices),'polygons':len(me.polygons),
                'triangles':len(me.loop_triangles),'uv_layers':[l.name for l in me.uv_layers],
                'vertex_groups':[g.name for g in ob.vertex_groups],'max_influences':maxinf,
                'unweighted_vertices':unweighted,'non_normalized_vertices':bad,
                'shape_keys':[k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [],
                'modifiers':[{'type':m.type,'name':m.name} for m in ob.modifiers],
                'materials':[m.name if m else None for m in me.materials],
                'raw_world_bounds':bounds(pts),'scale':vec(ob.scale),'rotation':vec(ob.rotation_euler)})
        rec['skin_rest_bounds']=bounds(all_points)
        rec['images']=[{'name':im.name,'size':list(im.size),'filepath':im.filepath,
                        'packed':bool(im.packed_file),'source':im.source,'colorspace':im.colorspace_settings.name}
                       for im in bpy.data.images if im.type!='RENDER_RESULT']
        rec['materials']=[{'name':m.name,'nodes':[n.type for n in m.node_tree.nodes] if m.node_tree else []}
                          for m in bpy.data.materials]
        for action in bpy.data.actions:
            fc=curves(action)
            ac={'name':action.name,'frame_range':vec(action.frame_range),'curves':len(fc),
                'key_count':sum(len(f.keyframe_points) for f in fc),
                'slots':[s.identifier for s in action.slots],
                'channels':sorted(set(f.data_path for f in fc)),'samples':[]}
            for rig in rigs:
                rig.data.pose_position='POSE';set_action(rig,action)
            start,end=map(int,action.frame_range)
            endpoint_matrices=[]
            for frame in sorted(set([start,end]+[round(start+(end-start)*f) for f in (.25,.5,.75)])):
                scene.frame_set(frame);bpy.context.view_layer.update()
                sample={'frame':frame,'bones':{}}
                for rig in rigs:
                    for name in ('root','hips','head','hand_L','hand_R','foot_L','foot_R'):
                        p=rig.pose.bones.get(name)
                        if p: sample['bones'][name]={'head':vec(rig.matrix_world@p.head),'tail':vec(rig.matrix_world@p.tail)}
                    if frame in (start,end):endpoint_matrices.append([tuple(float(v) for row in p.matrix for v in row) for p in rig.pose.bones])
                ac['samples'].append(sample)
            if len(endpoint_matrices)==2:
                ac['loop_max_bone_matrix_delta']=max(abs(a-b) for aa,bb in zip(*endpoint_matrices) for a,b in zip(aa,bb))
            rec['actions'].append(ac)
        report['files'].append(rec)
        (OUT/'source_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('AUDIT',path.name,rec['skin_rest_bounds'],[(m['vertices'],m['triangles']) for m in rec['meshes'] if m['skinned']],flush=True)
    except Exception:
        report['files'].append({'file':str(path),'error':traceback.format_exc()})
        (OUT/'source_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(traceback.format_exc(),flush=True)
print('AUDIT_COMPLETE',str(OUT/'source_audit.json'),flush=True)
