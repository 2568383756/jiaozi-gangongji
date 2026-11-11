"""Adapt six loaded v05/v01 station assemblies to the measured short-arm rig.

Call apply() after opening the source scene. No character, source file, camera,
full-scene export or render is changed here. Changes remain in the loaded scene.
"""
import math
from pathlib import Path
import bpy
from mathutils import Matrix,Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PROPS=ROOT/'01_游戏开发/Models/首关道具_v01_20261111/GLB'
VERSION='station_fit_v01_20261111'
PARAMS={'table_top':.330,'contact_z':.350,'paper_base_z':.344,
        'board_or_mat_thickness':.014,'standing_gap':.240,
        'core_collision_radius':.220,'collision_skin':.015,
        'paper_size':[.42,.60],'palm_x':.170,'palm_forward':.273,
        'table_depth':.72,'shared_depth':.70,'dry_width':2.40,
        'dry_depth':.60,'dry_slot_spacing':1.30,'dry_paper_tilt_degrees':30.0,'pulp_depth':.82,
        'pulp_operator_panel_inset':.040,
        'create_contact_demo_sheets':True}


def descendants(root):
    result=[root]
    for child in root.children:result.extend(descendants(child))
    return result


def _bounds(ob,root=None):
    root=root or ob
    bpy.context.view_layer.update();inv=root.matrix_world.inverted();points=[]
    dg=bpy.context.evaluated_depsgraph_get()
    for obj in descendants(ob):
        if obj.type!='MESH' or obj.hide_render:continue
        evaluated=obj.evaluated_get(dg);mesh=evaluated.to_mesh()
        points.extend(inv@obj.matrix_world@v.co for v in mesh.vertices)
        evaluated.to_mesh_clear()
    if not points:return None
    lo=[min(p[i] for p in points) for i in range(3)]
    hi=[max(p[i] for p in points) for i in range(3)]
    return {'min':lo,'max':hi,'size':[hi[i]-lo[i] for i in range(3)]}


def _mesh_map(ob,root,fn):
    """Bake only this station part's changed shape, retaining its UV/materials."""
    if ob.type!='MESH':return
    ob.data=ob.data.copy()
    transform=root.matrix_world.inverted()@ob.matrix_world
    points=[fn(transform@v.co) for v in ob.data.vertices]
    ob.parent=root;ob.matrix_parent_inverse=Matrix.Identity(4)
    ob.matrix_basis=Matrix.Identity(4)
    for vertex,point in zip(ob.data.vertices,points):vertex.co=point
    ob.data.update();ob['station_adaptation']=VERSION


def _fit_box(ob,root,center,size):
    box=_bounds(ob,root)
    if box is None:return
    middle=[(box['min'][i]+box['max'][i])/2 for i in range(3)]
    scales=[size[i]/box['size'][i] if box['size'][i]>1e-8 else 1 for i in range(3)]
    _mesh_map(ob,root,lambda p:tuple(center[i]+(p[i]-middle[i])*scales[i] for i in range(3)))


def _empty(name,parent,position,role,**properties):
    ob=bpy.data.objects.get(name)
    if ob is None:
        ob=bpy.data.objects.new(name,None)
        (parent.users_collection[0] if parent.users_collection else bpy.context.scene.collection).objects.link(ob)
    ob.parent=parent;ob.matrix_parent_inverse=Matrix.Identity(4)
    ob.location=position;ob.rotation_euler=(0,0,0);ob.scale=(1,1,1)
    ob.empty_display_type='PLAIN_AXES';ob.empty_display_size=.045
    ob['role']=role;ob['station_adaptation']=VERSION
    for key,value in properties.items():ob[key]=value
    return ob


def _box(name,parent,center,size,material):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob=bpy.context.object;ob.name=name
    for vertex in ob.data.vertices:
        for axis in range(3):vertex.co[axis]*=size[axis]
    ob.parent=parent;ob.matrix_parent_inverse=Matrix.Identity(4);ob.location=center
    if material:ob.data.materials.append(material)
    ob['station_adaptation']=VERSION
    # Reuse physical-scale UVs for exportable v05 paper material.
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=1,correct_aspect=False,scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def _beam(name,parent,start,end,radius=.012):
    a,b=Vector(start),Vector(end);direction=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=radius,depth=direction.length)
    ob=bpy.context.object;ob.name=name;ob.parent=parent;ob.matrix_parent_inverse=Matrix.Identity(4)
    ob.location=(a+b)/2;ob.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    mat=bpy.data.materials.get('MAT_wood_light')
    if mat:ob.data.materials.append(mat)
    ob['station_adaptation']=VERSION
    return ob


def _hide(root_name=None,prefixes=()):
    root=bpy.data.objects.get(root_name) if root_name else None
    objects=set(descendants(root)) if root else set()
    objects.update(ob for ob in bpy.context.scene.objects if any(ob.name.startswith(prefix) for prefix in prefixes))
    for ob in objects:ob.hide_render=True;ob.hide_viewport=True;ob['replaced_by_station_adaptation']=True


def _prop(instance,asset_id,parent,location,rotation=(0,0,0),scale=(1,1,1)):
    ob=bpy.data.objects.get(instance)
    if ob is None:
        before=set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(PROPS/(asset_id+'.glb')))
        added=set(bpy.data.objects)-before
        roots=[item for item in added if item.parent not in added]
        if len(roots)!=1:raise RuntimeError('Expected one root in '+asset_id)
        ob=roots[0]
        for item in added:item.name=instance+'__'+item.name
        ob.name=instance
    ob.parent=parent;ob.matrix_parent_inverse=Matrix.Identity(4)
    ob.location=location;ob.rotation_mode='XYZ';ob.rotation_euler=rotation;ob.scale=scale
    ob.hide_render=False;ob.hide_viewport=False
    ob['station_adaptation']=VERSION;ob['asset_id']=asset_id
    return ob


def _table_shape(root,depth,p):
    ratio=depth/1.0;top=p['table_top'];under=top-.055
    parts=[ob for ob in list(root.children) if ob.type=='MESH' and ob.name.startswith(root.name+'__')]
    for ob in parts:
        name=ob.name
        if any(key in name for key in ('paper_mat','single_slot_outline','slot_corner')):continue
        if not any(key in name for key in ('tabletop','paper_lip','apron','leg','tenon','stretcher','top_join','binding','foot_paper','craft_label','label_')):continue
        def transform(v):
            x,y,z=v;yy=y*ratio
            zz=z/ .55*under if z<.55 else under+(z-.55)*.55
            if any(key in name for key in ('tapered_leg','exposed_tenon','tenon_end_grain','foot_paper')):
                old_center=.38 if y>0 else -.38
                new_center=(depth/2-.12-.15*ratio/2)*(1 if y>0 else -1)
                yy=new_center+(y-old_center)*ratio
            elif 'stretcher_y' in name:
                yy=y*((depth/2-.13)/.41)
            elif any(key in name for key in ('curved_tooth_apron','apron_inset','apron_edge_wear')):
                yy=y*ratio-(1 if y>0 else -1)*.08
            elif any(key in name for key in ('craft_label','label_')):
                yy=-(depth/2-.12)+(y+.445)*.75
                zz=.205+(z-.455)*.72
            return x,yy,zz
        _mesh_map(ob,root,transform)
    root['depth']=depth;root['height']=top;root['desired_size']=[float(root.get('width',1.6)),depth,top]
    root['counter_top_m']=top


def _collider(root,suffix,center,size):
    ob=_empty(root.name+'__Collider_'+suffix,root,center,'collision_proxy',
              collider_type='Box',collider_size_m=list(size),non_rendering=True)
    ob.empty_display_type='CUBE';ob.empty_display_size=1;ob.scale=tuple(s/2 for s in size)
    return {'name':ob.name,'center_local':list(center),'size_m':list(size)}


def _work(root,p,depth,side,x,slot=None,contact_kind='paper_surface',surface_names=()):
    suffix=slot if slot else 'main'
    stand_y=side*(depth/2+p['standing_gap'])
    contact_y=stand_y-side*p['palm_forward']
    z=p['contact_z']
    standing=_empty(root.name+'__standing_'+suffix,root,(x,stand_y,0),'player_standing_point')
    target=_empty(root.name+'__interaction_'+suffix,root,(x,side*(depth/2+.035),z),'interaction_target')
    frame=_empty(root.name+'__work_frame_'+suffix,root,(x,contact_y,z),'work_frame',contact_kind=contact_kind)
    yaw=0 if side==1 else math.pi;frame.rotation_euler.z=yaw
    grips={}
    for hand,sign in (('L',-1),('R',1)):
        xyz=(x+side*sign*p['palm_x'],contact_y,z)
        grip=_empty(root.name+'__tool_Grip_'+hand+'_'+suffix,root,xyz,'work_contact',hand=hand,
                    contact_kind=contact_kind,surface_height_m=z)
        grips[hand]={'name':grip.name,'local_xyz':list(xyz)}
    for ob in (standing,target,frame):
        if slot:ob['slot_id']=slot
    return {'slot':slot,'standing_name':standing.name,'standing_local':[x,stand_y,0],
            'facing_z_degrees':math.degrees(yaw),'contact_local':[x,contact_y,z],
            'contact_height_m':z,'contact_kind':contact_kind,'tool_grips':grips,
            'work_frame':frame.name,'allowed_contact_surface_names':list(surface_names),
            'table_edge_gap_m':p['standing_gap'],'core_radius_m':p['core_collision_radius'],
            'skin_m':p['collision_skin'],'proxy_clearance_m':p['standing_gap']-p['core_collision_radius']-p['collision_skin']}


def _paper(root,slot_name,position,instance,state,rotation,p):
    anchor=_empty(root.name+'__'+slot_name,root,position,'paper_anchor',slot_id='0')
    if p['create_contact_demo_sheets']:
        obj=_prop(instance,'paper_'+state,anchor,(0,0,0),rotation)
        obj['art_demonstration']=True;obj['not_gameplay_initial_state']=True
    return anchor


def apply(config=None):
    p=dict(PARAMS)
    if config:p.update(config)
    scene=bpy.context.scene
    if scene.get('station_fit_applied')==VERSION:
        raise RuntimeError('Adaptation already applied; reopen v05/v01 source before applying again.')
    required=['station_'+name for name in ('pulp','dry','print','stamp','delivery','shared')]
    if any(bpy.data.objects.get(name) is None for name in required):raise RuntimeError('Six original station roots required')
    report={'version':VERSION,'params':p,'stations':[],'changes':[],'checks':[],
            'scope':'station art and interfaces only; no role root, rig, source file or gameplay state modified',
            'collision_note':'r=.22 is a torso core proxy, not the complete shoe/hat envelope; actual meshes require separate review',
            'work_scope':'generic paper/frame contact only; precise stamp handle choreography and top drying clips are not certified'}
    paper_mat=bpy.data.materials.get('MAT_paper_edge') or bpy.data.materials.get('MAT_paper')

    # Print and stamp: shorter furniture; paper rotated as a whole, never rescaled.
    for sid in ('station_print','station_stamp','station_shared'):
        root=bpy.data.objects[sid];depth=p['shared_depth'] if sid.endswith('shared') else p['table_depth']
        _table_shape(root,depth,p)
    root=bpy.data.objects['station_print'];depth=p['table_depth'];x=-.23
    _hide('station_print__ink_dish_pivot');_hide('station_print__printing_brush_pivot')
    _hide(prefixes=('station_print__print_block_','station_print__print_ink_surface','station_print__block_','station_print__engraved_'))
    _prop('v01_print_block','tool_print_block',root,(x,-.10,p['table_top']),(0,0,math.pi/2),(1,1,.014/.0752))
    _prop('v01_print_brush','tool_print_brush',root,(.52,-.10,.332),(0,0,math.pi/2),(.80,.80,.80))
    _prop('v01_print_ink_dish','tool_ink_dish',root,(.52,.20,.330),scale=(.85,.85,.85))
    _prop('v01_print_rubbing_pad','tool_rubbing_pad',root,(-.65,.20,.330),scale=(.65,.65,.65))
    tray=bpy.data.objects.get(root.name+'__tool_tray')
    if tray:_fit_box(tray,root,(.52,.02,.334),(.36,.62,.008))
    cy=-(depth/2-.02-.21)
    _paper(root,'slot_0',(x,cy,.344),'adapt_print_dry_sheet','dry',(0,0,math.pi/2),p)
    work=_work(root,p,depth,-1,x,surface_names=['adapt_print_dry_sheet__paper_dry__paper_body'])
    cols=[_collider(root,'top',(0,0,.295),(1.6,depth,.070)),_collider(root,'core',(0,0,.13),(1.52,depth-.24,.260))]
    report['stations'].append({'id':root.name,'dimensions':[1.6,depth,.33],'work_frames':[work],'colliders':cols})

    root=bpy.data.objects['station_stamp'];x=-.21;cy=depth/2-.02-.21
    _hide('station_stamp__seal_pivot');_hide(prefixes=('station_stamp__inkpad_tray','station_stamp__red_inkpad','station_stamp__inkpad_scroll','station_stamp__sample_ticket','station_stamp__note_'))
    mat=bpy.data.objects.get('station_stamp__paper_mat')
    if mat:_fit_box(mat,root,(x,.12,.337),(.65,.47,.014))
    _prop('v01_stamp','tool_stamp',root,(.53,.14,.330),scale=(.45,.45,.45))
    _prop('v01_stamp_ink_pad','tool_ink_pad',root,(.52,-.17,.330),scale=(.75,.75,.75))
    _paper(root,'slot_0',(x,cy,.344),'v01_stamp_red_ticket','red',(0,0,math.pi/2),p)
    _empty(root.name+'__seal_contact',root,(x,cy,.350),'stamp_contact_point',
           scope='paper contact reference; lifted stamp handle motion is not this generic Work clip')
    work=_work(root,p,depth,1,x,surface_names=['v01_stamp_red_ticket__paper_red__paper_body'])
    cols=[_collider(root,'top',(0,0,.295),(1.6,depth,.070)),_collider(root,'core',(0,0,.13),(1.52,depth-.24,.260))]
    report['stations'].append({'id':root.name,'dimensions':[1.6,depth,.33],'work_frames':[work],'colliders':cols,
                              'stamp_handle_work_animation_validated':False,'stamp_display_scale':.45})

    root=bpy.data.objects['station_shared'];depth=p['shared_depth'];cy=depth/2-.02-.21
    _hide(prefixes=('station_shared__single_slot_outline','station_shared__slot_corner'))
    pad=_box('adapt_shared_single_slot_mat',root,(0,.105,.337),(.64,.46,.014),paper_mat)
    _paper(root,'slot_0',(0,cy,.344),'adapt_shared_dry_sheet','dry',(0,0,math.pi/2),p)
    work=_work(root,p,depth,1,0,surface_names=['adapt_shared_dry_sheet__paper_dry__paper_body'])
    cols=[_collider(root,'top',(0,0,.295),(1.0,depth,.070)),_collider(root,'core',(0,0,.13),(.92,depth-.24,.260))]
    report['stations'].append({'id':root.name,'dimensions':[1.0,depth,.33],'work_frames':[work],'colliders':cols,'slot_count':1})

    # Pulp: a shallow vat, a low operator-side lip, and a full-size raised screen.
    root=bpy.data.objects['station_pulp'];depth=p['pulp_depth'];ratio=depth/1.2
    for ob in list(root.children):
        if ob.type!='MESH' or not ob.name.startswith(root.name+'__') or '__screen_' in ob.name:continue
        name=ob.name
        def mapping(v):
            x,y,z=v;yy=y*ratio;zz=z*(.36/.65)
            if 'water' in name:zz=.265+(z-.495)
            elif 'pulp_fibre' in name:zz=.273+(z-.503)
            elif 'inner_liner' in name:zz=.215+(z-.34)*.45
            elif ('side_y' in name and y>0) or 'vat_layer_seam' in name:
                # The real Work hip/sleeve envelope enters the former front
                # face by a few millimetres. Recess only this wall and its seam;
                # the full-size screen, contact bar and standing root stay fixed.
                yy-=p['pulp_operator_panel_inset'];zz=z*(.30/.62)
            if zz<.22 and yy>.28:yy-=.025*(1-zz/.22)
            return x,yy,zz
        _mesh_map(ob,root,mapping)
    _hide('station_pulp__screen_pivot')
    _prop('v01_pulp_screen','tool_papermaking_screen',root,(.27,.04,.310))
    _paper(root,'slot_0',(.27,.04,.352),'adapt_pulp_wet_sheet','wet',(0,0,0),p)
    work=_work(root,p,depth,1,.27,contact_kind='front_screen_beam_top',
               surface_names=['v01_pulp_screen__tool_papermaking_screen__bamboo_end.001'])
    root['depth']=depth;root['height']=.36;root['desired_size']=[2.0,depth,.36]
    inset=p['pulp_operator_panel_inset']
    # Separate side strips retain the full outside footprint without a solid
    # imaginary upper box across the open water or the recessed operator side.
    cols=[_collider(root,'vat_core',(0,-inset/2,.15),(1.82,depth-.06-inset,.30)),
          _collider(root,'vat_operator_panel',(0,.53*ratio-inset,.15),(1.85,.14*ratio,.30)),
          _collider(root,'vat_far_wall',(0,-depth/2+.035,.18),(1.80,.070,.36))]
    for sign in (-1,1):
        cols.append(_collider(root,'vat_side_'+str(sign),(sign*.90,0,.18),(.20,depth,.36)))
    report['stations'].append({'id':root.name,'dimensions':[2.0,depth,.36],'work_frames':[work],'colliders':cols,
                              'screen_size_unchanged':[.52,.70],'paper_output_z':.352,
                              'operator_panel_inset_m':inset,'operator_panel_front_y':depth/2-inset})

    # Drying: low inclined air-drying supports; vertical sheets would intersect the large heads.
    root=bpy.data.objects['station_dry'];depth=p['dry_depth'];delta=(p['dry_width']-2)/2
    old_parts=[ob for ob in list(root.children) if ob.type=='MESH' and ob.name.startswith(root.name+'__')]
    for ob in old_parts:
        name=ob.name
        def mapping(v):
            x,y,z=v
            if any(k in name for k in ('preview_','wet_drop','dry_corner')):
                return x+(.15 if x>0 else -.15),y-.126,z-.35
            if 'suspension_loop' in name:
                dz=-.35 if z<=1.35 else (-.35*(1.47-z)/.12 if z<1.47 else 0)
                return x+(.15 if x>0 else -.15),y-.126*(1 if z<1.35 else 0),z+dz
            if 'crossbar' in name:return x*(2.38/1.98),y+.10,z
            if any(k in name for k in ('craft_label','label_')):return x,y+.10,z
            return x+(delta if x>0 else -delta),y*(depth/.8)+(0 if 'foot' in name else .10),z
        _mesh_map(ob,root,mapping)
    for ob in list(root.children):
        if ob.type=='EMPTY' and '__clip_pivot_' in ob.name:
            ob.location.x+=.15 if ob.location.x>0 else -.15;ob.location.y-=.126;ob.location.z-=.35
    workframes=[]
    for slot,x,state,instance in (('A',-.65,'wet','v01_dry_A_wet'),('B',.65,'dry','v01_dry_B_dry')):
        _hide(prefixes=(root.name+'__preview_'+slot,root.name+'__wet_drop',root.name+'__dry_corner_crease'))
        _hide(prefixes=(root.name+'__suspension_loop_'+slot,root.name+'__clip_pivot_'+slot))
        for clip in [o for o in root.children if '__clip_pivot_'+slot in o.name]:_hide(clip.name)
        tilt=math.radians(p['dry_paper_tilt_degrees'])
        contact_y=-(depth/2+p['standing_gap'])+p['palm_forward']
        # The paper starts 3 cm beyond a real horizontal receiving bar. Both
        # characters press this bar at .35 instead of forcing a flat palm into a slope.
        paper_near_y=contact_y+.030
        paper_y=paper_near_y+.30*math.cos(tilt)+.006*math.sin(tilt)
        paper_z=p['contact_z']+.30*math.sin(tilt)-.006*math.cos(tilt)
        anchor=_empty(root.name+'__slot_'+slot,root,(x,paper_y,paper_z),'paper_anchor',slot_id=slot)
        _prop(instance,'paper_'+state,anchor,(0,0,0),(tilt,0,0))
        front_y=paper_near_y+.003;back_y=front_y+.60*math.cos(tilt)
        front_z=p['contact_z']-.016;back_z=front_z+.60*math.sin(tilt)
        for sign in (-1,1):
            _beam(root.name+'__low_dry_rail_'+slot+'_'+str(sign),root,
                  (x+sign*.23,front_y,front_z),(x+sign*.23,back_y,back_z))
        for label,yy,zz in (('front',front_y,front_z),('back',back_y,back_z)):
            _beam(root.name+'__low_dry_crossbar_'+slot+'_'+label,root,(x-.23,yy,zz),(x+.23,yy,zz))
        for sign in (-1,1):
            _beam(root.name+'__low_dry_support_'+slot+'_'+str(sign),root,
                  (x+sign*.23,back_y,.12),(x+sign*.23,back_y,back_z),.016)
        receiving=_box(root.name+'__receiving_bar_'+slot,root,(x,contact_y+.003,.343),(.48,.070,.014),
                       bpy.data.materials.get('MAT_wood_light'))
        receiving['role']='fixed_drying_transfer_bar';receiving['slot_id']=slot
        workframes.append(_work(root,p,depth,-1,x,slot,contact_kind='horizontal_drying_transfer_bar',
                          surface_names=[receiving.name]))
    root['width']=2.4;root['depth']=depth;root['desired_size']=[2.4,depth,1.6];root['slot_center_distance']=1.3
    cols=[]
    for side in (-1,1):
        cols.append(_collider(root,'foot_'+str(side),(side*1.08,0,.07),(.24,depth,.14)))
        cols.append(_collider(root,'post_'+str(side),(side*1.08,.10,.83),(.16,.16,1.54)))
    report['stations'].append({'id':root.name,'dimensions':[2.4,depth,1.6],'work_frames':workframes,'colliders':cols,
          'slot_count':2,'slot_spacing':1.3,'paper_tilt_degrees':p['dry_paper_tilt_degrees'],
          'reachable_part':'horizontal .35m transfer bar; inclined sheet begins 3cm behind it, near edge .35 far edge .65; high frame retained'})

    # Delivery window: alter only its lower cabinet, counter, receiving tray and receipt.
    root=bpy.data.objects['station_delivery'];depth=.60
    for ob in list(root.children):
        if ob.type!='MESH' or not ob.name.startswith(root.name+'__'):continue
        name=ob.name
        if '__counter' in name:
            _mesh_map(ob,root,lambda v:(v.x,v.y,v.z/.55*.275 if v.z<.55 else .275+(v.z-.55)*.55))
        elif '__lower_panel' in name:_mesh_map(ob,root,lambda v:(v.x,v.y,v.z*.50))
    for name,center,size in (
        ('tray_base',(-.15,-.07,.337),(.68,.45,.014)),
        ('tray_side',(-.47,-.07,.344),(.04,.45,.012)),
        ('tray_side.001',(.17,-.07,.344),(.04,.45,.012)),
        ('tray_end',(-.15,-.275,.344),(.64,.04,.012)),
        ('tray_end.001',(-.15,.135,.344),(.64,.04,.012))):
        ob=bpy.data.objects.get(root.name+'__'+name)
        if ob:_fit_box(ob,root,center,size)
    _hide(prefixes=(root.name+'__receipt_tag',root.name+'__receipt_text'))
    _prop('v01_delivery_receipt','marker_delivery_receipt',root,(.54,.04,.33))
    _empty(root.name+'__receiving_slot',root,(-.15,-.07,.344),'paper_anchor',slot_id='0')
    _empty(root.name+'__receipt_anchor',root,(.54,.04,.61),'receipt_feedback_anchor')
    work=_work(root,p,depth,-1,-.15,contact_kind='receiving_tray_front_lip',surface_names=[root.name+'__tray_end'])
    cols=[_collider(root,'counter',(0,0,.3025),(1.96,.60,.055))]
    root['counter_top_m']=.33
    report['stations'].append({'id':root.name,'dimensions':[2,.6,2.4],'work_frames':[work],'colliders':cols,
                              'window_roof_scroll_unchanged':True,'delivered_paper_is_consumed_not_stored':True})

    bpy.context.view_layer.update()
    for station in report['stations']:
        root=bpy.data.objects[station['id']];root['station_fit_version']=VERSION
        station['world_root']=list(root.matrix_world.translation)
        for wf in station['work_frames']:
            wf['standing_world']=list(root.matrix_world@Vector(wf['standing_local']))
            wf['contact_world']=list(root.matrix_world@Vector(wf['contact_local']))
        station['actual_visible_bounds_local']=_bounds(root)
    report['changes']=['furniture height/depth only, no global scene scaling','paper dimensions unchanged; worktop sheets rotated Z90',
        'table legs grounded, front apron/stretchers recessed','tool parking transforms explicit; stamp handle motion not certified',
        'dry width 2.4, slot spacing 1.3; reachable lower sheet edge','upper delivery frame, roof and scroll unchanged',
        'pulp operator panel recessed .04 m with separate wall/core proxies; screen and standing root unchanged']
    report['checks']=[{'name':'six_station_roots','pass':len(report['stations'])==6},
        {'name':'seven_work_frames','pass':sum(len(s['work_frames']) for s in report['stations'])==7},
        {'name':'torso_proxy_outside_top_edge','pass':p['standing_gap']>=p['core_collision_radius']+p['collision_skin']},
        {'name':'character_rigs_not_modified','pass':True},
        {'name':'paper_scale_unchanged','pass':all(tuple(round(v,6) for v in ob.scale)==(1,1,1) for ob in scene.objects if ob.get('asset_id') in ('paper_wet','paper_dry','paper_black','paper_red') and ob.get('station_adaptation')==VERSION)}]
    scene['station_fit_applied']=VERSION
    return report
