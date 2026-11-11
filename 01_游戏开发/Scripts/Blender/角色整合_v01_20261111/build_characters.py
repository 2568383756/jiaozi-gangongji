import bpy, math, json, traceback, sys
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion, Euler
ROOT=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发')
SOURCE=ROOT/'Imports/角色源仓_20261111/source_checkout/deliverables'
OUT=ROOT/'Models/首批角色_v01_20261111'
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'Textures').mkdir(exist_ok=True)
SCRIPTS=ROOT/'Scripts/Blender/角色整合_v01_20261111'
CHARACTERS=[('zhituan','纸团','卡通人物_搬运走路.blend'),('yintao','印桃','红衣卡通女孩_搬运走路.blend')]
CLIPS={'Idle':61,'Walk':33,'CarryIdle':61,'CarryWalk':65,'Work':31}
PROVENANCE={'Idle':'New rest-pose breathing and head/arm idle',
 'Walk':'Source CarryWalk leg/hips cycle retimed 64 to 32 intervals, with new alternating arm swing',
 'CarryIdle':'Derived from source CarryWalk frame 1, with inward/raised hands and new breathing',
 'CarryWalk':'Source 64-interval CarryWalk legs/hips/head cycle retained, arms adapted for 0.42 m paper width',
 'Work':'New interruptible generic chest-forward motion derived from source carry stance; exact 0.65 m station/tool contact is deferred to P1 pose/interaction integration'}
REPORT={'blender':bpy.app.version_string,'source_commit':'86562a37fb6cf75f0ea41419b072b4129f207538','characters':[]}

def vector(v):return [round(float(x),7) for x in v]
def actions_curves(a):
 out=[]
 if hasattr(a,'fcurves'):out.extend(a.fcurves)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in getattr(strip,'channelbags',[]):out.extend(bag.fcurves)
 return out

def activate(rig,action):
 rig.animation_data_create();rig.animation_data.action=action
 if len(action.slots):rig.animation_data.action_slot=action.slots[0]

def bounds(points):
 lo=[min(p[k] for p in points) for k in range(3)];hi=[max(p[k] for p in points) for k in range(3)]
 return {'min':vector(lo),'max':vector(hi),'size':vector([hi[k]-lo[k] for k in range(3)])}

def skin_points(mesh):
 dg=bpy.context.evaluated_depsgraph_get();ev=mesh.evaluated_get(dg);me=ev.to_mesh()
 points=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return points

def assign_pose(rig,pose):
 for p in rig.pose.bones:
  p.rotation_mode='QUATERNION';p.matrix_basis=pose.get(p.name,Matrix.Identity(4))
 bpy.context.view_layer.update()

def rotation(p,x=0,y=0,z=0):
 p.rotation_quaternion=Euler((x,y,z),'XYZ').to_quaternion()

def create_action(rig,name):
 a=bpy.data.actions.new(name);a.use_fake_user=True
 slot=a.slots.new(id_type='OBJECT',name=rig.name)
 activate(rig,a);rig.animation_data.action_slot=slot
 return a

def key_pose(rig,frame):
 for p in rig.pose.bones:
  p.keyframe_insert('location',frame=frame,group=p.name)
  p.keyframe_insert('rotation_quaternion',frame=frame,group=p.name)
  p.keyframe_insert('scale',frame=frame,group=p.name)

def retarget_hands(rig,targets,desired,reference_rotations):
 for side in ('L','R'):
  hand=rig.pose.bones['hand_'+side]
  direction=reference_rotations[side]@Vector((0,hand.length,0))
  targets[side].location=desired[side]-direction*.5
  rig.pose.bones['forearm_'+side].constraints['TEMP_CarryIK'].mute=False
 bpy.context.view_layer.update()
 solved={n:rig.pose.bones[n].matrix.copy() for n in ('upper_arm_L','forearm_L','upper_arm_R','forearm_R')}
 for side in ('L','R'):rig.pose.bones['forearm_'+side].constraints['TEMP_CarryIK'].mute=True
 bpy.context.view_layer.update()
 for side in ('L','R'):
  for name in ('upper_arm_'+side,'forearm_'+side):
   rig.pose.bones[name].matrix=solved[name]
   bpy.context.view_layer.update()
  hand=rig.pose.bones['hand_'+side]
  mat=reference_rotations[side].to_matrix().to_4x4()
  mat.translation=rig.pose.bones['forearm_'+side].tail
  hand.matrix=mat
 bpy.context.view_layer.update()

def socket_pose(rig):
 palms=[(rig.pose.bones['hand_'+side].head+rig.pose.bones['hand_'+side].tail)*.5 for side in ('L','R')]
 mid=(palms[0]+palms[1])*.5
 rig.pose.bones['PalmCenter'].matrix=Matrix.Translation(mid)
 rig.pose.bones['HoldPoint'].matrix=Matrix.Translation(mid+Vector((0,-.21,.025)))
 bpy.context.view_layer.update()
 return palms,mid

def selected_export(rig,mesh,root):
 bpy.ops.object.select_all(action='DESELECT')
 for ob in (rig,mesh,root):ob.select_set(True)
 bpy.context.view_layer.objects.active=rig

def supported_call(operator,args):
 props={p.identifier for p in operator.get_rna_type().properties}
 return operator(**{k:v for k,v in args.items() if k in props})

for cid,label,filename in CHARACTERS:
 try:
  bpy.ops.wm.open_mainfile(filepath=str(SOURCE/filename),load_ui=False)
  scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
  bpy.context.preferences.filepaths.save_version=0
  scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
  rig=next(o for o in scene.objects if o.type=='ARMATURE')
  mesh=next(o for o in scene.objects if o.type=='MESH')
  source_carry=next(a for a in bpy.data.actions if '搬运' in a.name)
  raw=[mesh.matrix_world@v.co for v in mesh.data.vertices];bb=bounds(raw)
  factor=1.2/bb['size'][2]
  transform=Matrix.Translation((0,0,-bb['min'][2]*factor))@Matrix.Scale(factor,4)
  mesh.data.transform(transform);rig.data.transform(transform)
  for action in bpy.data.actions:
   for fc in actions_curves(action):
    if fc.data_path.endswith('.location'):
     for key in fc.keyframe_points:
      key.co.y*=factor;key.handle_left.y*=factor;key.handle_right.y*=factor
  rig.name='rig_'+cid;rig.data.name='skeleton_'+cid;mesh.name='mesh_'+cid;mesh.data.name='geometry_'+cid
  collection=bpy.data.collections.new('CHAR_'+cid);scene.collection.children.link(collection)
  for ob in (rig,mesh):
   for col in list(ob.users_collection):col.objects.unlink(ob)
   collection.objects.link(ob)
  root=bpy.data.objects.new('character_'+cid,None);collection.objects.link(root)
  root['character_id']=cid;root['display_name']=label;root['rest_height_m']=1.2
  root['role']='playable_character';root['forward_blender']='-Y';root['forward_gltf']='+Z'
  root['asset_version']='v01_20261111';rig.parent=root
  textures=[]
  for image in list(bpy.data.images):
   if image.source=='FILE' and image.size[0]>0:
    original=list(image.size);image.scale(2048,2048)
    image.filepath_raw=str(OUT/'Textures'/(cid+'_basecolor_2048.png'));image.file_format='PNG';image.save()
    if image.packed_file:image.unpack(method='REMOVE')
    image.filepath=str(OUT/'Textures'/(cid+'_basecolor_2048.png'));image.reload();image.pack()
    textures.append({'name':image.name,'original_size':original,'size':list(image.size),'file':str(OUT/'Textures'/(cid+'_basecolor_2048.png'))})
  activate(rig,source_carry);rig.data.pose_position='POSE'
  source_poses={}
  for frame in range(1,66):
   scene.frame_set(frame);bpy.context.view_layer.update()
   source_poses[frame]={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
  source_names=[a.name for a in bpy.data.actions]
  rig.animation_data.action=None
  for action in list(bpy.data.actions):bpy.data.actions.remove(action)
  bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
  bpy.ops.object.mode_set(mode='EDIT')
  for name,y,z in [('PalmCenter',-.245,.38),('HoldPoint',-.455,.405)]:
   b=rig.data.edit_bones.new(name);b.head=(0,y,z);b.tail=(0,y+.07,z);b.parent=rig.data.edit_bones['root'];b.use_deform=False;b.roll=0
  bpy.ops.object.mode_set(mode='OBJECT')
  rig.data.bones['HoldPoint']['role']='carry_socket';rig.data.bones['HoldPoint']['paper_size_m']=[.42,.60]
  rig.data.bones['HoldPoint']['paper_local_axes']='XY plane, +Z top normal; +Y is ticket top'
  rig.data.bones['HoldPoint']['offset_from_palms_blender']=[0,-.21,.025]
  rig.data.bones['PalmCenter']['role']='carry_palm_center'
  targets={}
  for side in ('L','R'):
   ob=bpy.data.objects.new('TEMP_IK_'+side,None);scene.collection.objects.link(ob);targets[side]=ob
   c=rig.pose.bones['forearm_'+side].constraints.new('IK');c.name='TEMP_CarryIK';c.target=ob;c.chain_count=2;c.use_tail=True;c.iterations=128;c.mute=True
  report={'character_id':cid,'display_name':label,'source':str(SOURCE/filename),'source_actions':source_names,
          'scale_from_source':factor,'rest_bounds':bounds([mesh.matrix_world@v.co for v in mesh.data.vertices]),
          'textures':textures,'clips':{},'core_collection':collection.name,'root':root.name,'rig':rig.name,
          'hold_bone':'HoldPoint','palm_bone':'PalmCenter','hold_offset_from_palm':[0,-.21,.025],
          'paper_size_m':[.42,.60],'paper_root':'bottom-face center','geometry_unchanged_except_uniform_scale':True}
  report['integration_limitations']=['Work is a P0 generic chest-forward gesture, not verified tool/table contact. Short-limb shape is retained; exact 0.65 m workstations require P1 pose and interaction-point integration.',
    'Use Generic rig initially; the two characters have different accessory bones and are not automatically interchangeable Humanoid avatars.',
    'Source yintao contains one coincident duplicate triangle; GLB retains 9771 encoded triangles while Blender reimport deduplicates to 9770. Visible surface, UV and weights are preserved.']
  for clip,end in CLIPS.items():
   action=create_action(rig,cid+'_'+clip)
   action['game_clip']=True;action['loop']=True;action['root_motion']=False
   action['source']=PROVENANCE[clip]
   samples=[];first_pose=None
   for frame in range(1,end+1):
    scene.frame_set(frame)
    phase=2*math.pi*(frame-1)/(end-1)
    carry_frame=1+round((frame-1)*64/(end-1))
    if clip in ('CarryWalk','Walk'):base=source_poses[carry_frame]
    elif clip in ('CarryIdle','Work'):base=source_poses[1]
    else:base={}
    assign_pose(rig,base)
    for side in ('L','R'):rig.pose.bones['forearm_'+side].constraints['TEMP_CarryIK'].mute=True
    if clip=='Idle':
     rig.pose.bones['hips'].location.z=.0025*(1-math.cos(phase))
     rotation(rig.pose.bones['chest'],x=.012*math.sin(phase))
     rotation(rig.pose.bones['head'],y=.018*math.sin(phase))
     for sign,side in ((1,'L'),(-1,'R')):
      rotation(rig.pose.bones['upper_arm_'+side],x=.025*math.sin(phase),z=-sign*.025)
    if clip=='Walk':
     for sign,side in ((1,'L'),(-1,'R')):
      rotation(rig.pose.bones['upper_arm_'+side],x=sign*.28*math.sin(phase))
      rotation(rig.pose.bones['forearm_'+side],x=-.08)
      rotation(rig.pose.bones['hand_'+side])
    if clip in ('CarryIdle','Work'):
     rig.pose.bones['hips'].location.z+=.002*(1-math.cos(phase))
     rotation(rig.pose.bones['head'],y=.008*math.sin(phase))
    bpy.context.view_layer.update()
    if clip in ('CarryWalk','CarryIdle','Work'):
     current_mid=sum(((rig.pose.bones['hand_'+s].head+rig.pose.bones['hand_'+s].tail)*.5 for s in ('L','R')),Vector())*.5
     refs={s:rig.pose.bones['hand_'+s].matrix.to_quaternion() for s in ('L','R')}
     if clip=='Work':refs={s:Quaternion((0,0,1),math.pi) for s in ('L','R')}
     desired={}
     for sign,side in ((1,'L'),(-1,'R')):
      if clip=='Work':
       desired[side]=Vector((sign*.175,-.265-.020*(1-math.cos(phase)),.405+.008*math.sin(phase+sign*.22)))
      else:
       bob=.008*(1-math.cos(phase*2)) if clip=='CarryWalk' else .002*(1-math.cos(phase))
       desired[side]=Vector((sign*.19+current_mid.x,-.245,.380+bob))
     retarget_hands(rig,targets,desired,refs)
    # Ground the lowest sole while keeping the root stationary. Hips carry the
    # tiny contact correction; no scene/object root motion is introduced.
    zmin=min(p.z for p in skin_points(mesh))
    hips=rig.pose.bones['hips'];m=hips.matrix.copy();m.translation.z+=.001-zmin;hips.matrix=m
    bpy.context.view_layer.update()
    palms,mid=socket_pose(rig)
    if frame==end and first_pose is not None:
     assign_pose(rig,first_pose);palms,mid=socket_pose(rig)
    key_pose(rig,frame)
    if frame==1:first_pose={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
    points=skin_points(mesh)
    if frame in (1,end,1+(end-1)//4,1+(end-1)//2,1+3*(end-1)//4):
     samples.append({'frame':frame,'palm_L':vector(palms[0]),'palm_R':vector(palms[1]),'palm_center':vector(mid),
                     'palm_span':(palms[0]-palms[1]).length,'hold_point':vector(rig.pose.bones['HoldPoint'].head),
                     'skin_bounds':bounds(points)})
   for fc in actions_curves(action):
    for key in fc.keyframe_points:key.interpolation='LINEAR'
   report['clips'][clip]={'action':action.name,'frame_range':[1,end],'fps':30,'duration_seconds':(end-1)/30,
                          'source':action['source'],'samples':samples}
  for side in ('L','R'):
   rig.pose.bones['forearm_'+side].constraints.remove(rig.pose.bones['forearm_'+side].constraints['TEMP_CarryIK'])
   bpy.data.objects.remove(targets[side],do_unlink=True)
  mesh.data.calc_loop_triangles()
  report['vertices']=len(mesh.data.vertices);report['triangles']=len(mesh.data.loop_triangles)
  report['bone_count']=len(rig.data.bones);report['deform_bone_count']=sum(b.use_deform for b in rig.data.bones)
  report['materials']=[m.name for m in mesh.data.materials]
  report['unweighted_vertices']=sum(not any(g.weight>1e-7 for g in v.groups) for v in mesh.data.vertices)
  report['max_influences']=max(sum(g.weight>1e-7 for g in v.groups) for v in mesh.data.vertices)
  activate(rig,bpy.data.actions[cid+'_CarryWalk']);scene.frame_start=1;scene.frame_end=65;scene.frame_set(1)
  stem='角色_'+label+'_整合_v01_20261111'
  blend=OUT/(stem+'.blend');glb=OUT/(stem+'.glb');fbx=OUT/(stem+'.fbx')
  bpy.ops.wm.save_as_mainfile(filepath=str(blend))
  selected_export(rig,mesh,root)
  supported_call(bpy.ops.export_scene.gltf,dict(filepath=str(glb),export_format='GLB',use_selection=True,
     export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,
     export_def_bones=False,export_yup=True,export_extras=True,export_materials='EXPORT',export_cameras=False,export_lights=False,
     export_all_influences=False,export_image_format='JPEG',export_jpeg_quality=95,export_image_quality=95,export_current_frame=False))
  supported_call(bpy.ops.export_scene.fbx,dict(filepath=str(fbx),use_selection=True,object_types={'EMPTY','MESH','ARMATURE'},
     axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',add_leaf_bones=False,
     use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,
     bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=True))
  report['files']={'blend':str(blend),'glb':str(glb),'fbx':str(fbx)}
  report['glb_texture_encoding']={'format':'JPEG','quality':95,'size':[2048,2048],
    'authoring_texture':'packed 2048 PNG retained in BLEND and FBX','jpeg_glb_bytes':glb.stat().st_size}
  REPORT['characters'].append(report)
  (OUT/'角色整合报告_v01_20261111.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
  print('CHARACTER_BUILT',cid,report['vertices'],report['triangles'],report['bone_count'],flush=True)
 except Exception:
  REPORT['characters'].append({'character_id':cid,'error':traceback.format_exc()})
  (OUT/'角色整合报告_v01_20261111.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
  print(traceback.format_exc(),flush=True)
print('BUILD_FINISHED',flush=True)
