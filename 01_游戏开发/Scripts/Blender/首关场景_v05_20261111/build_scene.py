"""Build editable first-level art in Blender. Run in a new background process."""
from pathlib import Path
import sys, json, math, collections
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scene_helpers import SceneAPI, rgba
from architecture import build_architecture
from stations import build_stations
from decoration import build_decoration
from paper_materials import enhance_materials
from exterior_hardscape import build_exterior_hardscape
from exterior_vegetation import build_exterior_vegetation
from exterior_garden_beds import build_garden_beds

ROOT = HERE.parents[3]
SPEC = ROOT / '01_游戏开发/Art/场景关卡/首关三视图_v02_20261110/尺寸与布局_v02_20261110.json'
OUT = ROOT / '01_游戏开发/Models/首关场景_v05_20261111'
OUT.mkdir(parents=True, exist_ok=True)
spec = json.loads(SPEC.read_text(encoding='utf-8-sig'))

def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()

def camera(name, location, target, ortho):
    data = bpy.data.cameras.new(name); data.type = 'ORTHO'; data.ortho_scale = ortho
    ob = bpy.data.objects.new(name, data); stage.objects.link(ob)
    ob.location = location; aim(ob, target)
    return ob

def descendants(root):
    result = []
    for child in root.children:
        result.append(child); result.extend(descendants(child))
    return result

def bounds(root):
    points = []
    for ob in descendants(root):
        if ob.type == 'MESH' and not ob.hide_render:
            points.extend(ob.matrix_world @ Vector(p) for p in ob.bound_box)
    return [[round(min(p[a] for p in points),4),round(max(p[a] for p in points),4)] for a in range(3)] if points else None

def static_navigation(spec, decor):
    # Nominal art footprints, inflated by character radius + .05m clearance.
    obstacles = []
    for s in spec['stations']:
        x,y=s['center_xz']; w,d,h=s['dimensions']
        obstacles.append((x-w/2,y-d/2,x+w/2,y+d/2))
    for root in decor:
        if 'footprint' in root:
            box=bounds(root)
            obstacles.append((box[0][0],box[1][0],box[0][1],box[1][1]))
    radius=.375; step=.1
    def free(x,y):
        if not (.475 <= x <= 11.525 and .475 <= y <= 7.525): return False
        return not any(a-radius < x < c+radius and b-radius < y < d+radius for a,b,c,d in obstacles)
    start=(60,40); seen={start}; queue=collections.deque([start])
    while queue:
        ix,iy=queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            p=(ix+dx,iy+dy)
            if p not in seen and free(p[0]*step,p[1]*step):
                seen.add(p);queue.append(p)
    targets={}
    for s in spec['stations']:
        x,y=s['center_xz'];w,d,h=s['dimensions']
        side=1 if s['id'] in ('station_pulp','station_stamp','station_shared') else -1
        y+=side*(d/2+.425)
        xs=[x-.5,x+.5] if s['id']=='station_dry' else [x]
        for i,tx in enumerate(xs):
            key=s['id']+('_AB'[i+1] if len(xs)>1 else '')
            p=(round(tx/step),round(y/step))
            targets[key]={'xy':[round(tx,3),round(y,3)],'reachable':p in seen}
    return {'method':'0.1m 4-neighbor flood fill on nominal station and actual decoration AABBs, radius .325 + .05 clearance',
            'targets':targets,'all_reachable':all(t['reachable'] for t in targets.values()),
            'limitation':'Not Unity physics, no player-player simulation; wall perimeter simplified.'}

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
    scene['project']='交子赶工记';scene['level_id']='level_01';scene['version']='v05_20261111'
    scene['status']='Editable scene art; Unity integration not tested'
    scene['coordinate_mapping']='Blender(X,Y,Z) -> glTF(X,Z,-Y); Unity import orientation untested'
    scene['play_area']='12 x 8 m; existing production area'
    scene['exterior_area']='20 x 15 m; non-interactive scenery, not expanded gameplay'
    api=SceneAPI()
    # Floors stay quieter than the light worktops and teal/red operation accents.
    for key,hex_color in [('floor_workshop','C9A66C'),('floor_courtyard','DBC79E'),
                          ('garden_soil','D6BE8C'),('garden_edge','B39A6D'),
                          ('paving','C7B795'),('paving_light','E0D1B3'),
                          ('moss','527C38'),('grass','6F973F'),('sage','A3BE54'),
                          ('ginkgo_gold','F3BD16'),('ginkgo_light','FFDA43'),
                          ('ginkgo_ochre','D99614'),('bark','985923')]:
        material=bpy.data.materials.new('MAT_'+key);material.use_nodes=True
        material.diffuse_color=rgba(hex_color)
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgba(hex_color)
        api.materials[key]=material
    enhance_materials(api)
    print('BUILD_STAGE materials',flush=True)
    arch=build_architecture(api,spec)
    roots=build_stations(api,spec)
    decor=build_decoration(api,spec)
    exterior=build_exterior_hardscape(api,spec)+build_exterior_vegetation(api,spec)+build_garden_beds(api,spec)
    print('BUILD_STAGE geometry',len(scene.objects),flush=True)
    # Exportable folded-paper linework: convert relief curves to editable meshes.
    bpy.ops.object.select_all(action='DESELECT')
    curves=[o for o in scene.objects if o.type=='CURVE']
    for ob in curves: ob.select_set(True)
    if curves:
        bpy.context.view_layer.objects.active=curves[0]
        bpy.ops.object.convert(target='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.update()
    # Real UVs carry the packed paper base-color and normal maps into GLB.
    import hashlib
    for ob in list(scene.objects):
        if ob.type!='MESH': continue
        bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.cube_project(cube_size=1.0,correct_aspect=False,scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        seed=int(hashlib.sha256(ob.name.encode('utf-8')).hexdigest()[:8],16)
        offset=((seed%997)/997,((seed//997)%991)/991)
        for loop in ob.data.uv_layers.active.data:
            loop.uv.x+=offset[0];loop.uv.y+=offset[1]
        ob.select_set(False)
    print('BUILD_STAGE uv_projection',flush=True)
    # Dedicated reference helpers are kept separate from visible geometry/export.
    guides=api.collection('90_GUIDES_not_gameplay')
    guides.hide_render=True
    for s in spec['stations']:
        x,y=s['center_xz'];w,d,h=s['dimensions']
        ob=api.box('COLLIDER_REF_'+s['id'],(x,y,h/2),(w,d,h),'teal',bevel=0)
        ob.display_type='WIRE';ob.hide_render=True;ob['role']='nominal_collider_reference'
    for y in (3.3,5.7):
        ob=api.line('ClearLane_'+str(y),[(.3,y,.02),(11.7,y,.02)],'teal',.012)
        ob.hide_render=True
    for name,xy in [('P1_spawn',(4.4,4.2)),('P2_spawn',(6,4.2))]:
        ob=api.empty(name,(*xy,0),size=.25);ob['role']='spawn_reference'
        api.line(name+'_height',[(xy[0],xy[1],0),(xy[0],xy[1],1.2)],'red',.012).hide_render=True
    guides.hide_viewport=True

    global stage
    stage=api.collection('99_PRESENTATION_not_exported')
    backdrop=bpy.data.materials.new('MAT_Studio_plain');backdrop.use_nodes=True
    backdrop.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=api.materials['paper'].diffuse_color
    backdrop.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9
    ground=api.box('Studio_ground',(6,4,-.55),(200,200,.12),backdrop,bevel=0)
    world=bpy.data.worlds.new('Warm daylight');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.75,.85,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.28
    scene.world=world
    for name,loc,power,size in [('Key_soft',(-3,-4,12),1700,4.5),('Fill',(13,-1,9),550,8),('Rim',(5,11,12),700,6)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        data.color=(1.0,.95,.86) if name=='Key_soft' else ((.90,.95,1.0) if name=='Fill' else (1.0,.96,.88))
        ob=bpy.data.objects.new(name,data);stage.objects.link(ob);ob.location=loc;aim(ob,(6,4,0))
    gameplay=camera('CAM_Gameplay_Orthographic',(6.3,-13,18.3),(6,4,.5),14.4)
    overview=camera('CAM_Exterior_Overview',(6.3,-15.5,22),(6,4.0,.6),22.3)
    top=camera('CAM_Top_Orthographic',(6,4,28),(6,4,0),21.5)
    top.rotation_euler=(0,0,0)
    detail=camera('CAM_Paper_Detail',(7.4,2.1,4.9),(8.2,6.25,.65),3.6)
    garden_detail=camera('CAM_Ginkgo_Detail',(-8.4,1.0,7.2),(-2.1,6.45,1.3),6.2)
    grass_detail=camera('CAM_Paper_Grass_Detail',(-3.2,-3.5,2.8),(-.25,-.2,.2),2.55)
    art_review=camera('CAM_Craft_ArtReview',(14,-16,20),(6,4,.65),17.7)
    scene.camera=art_review
    scene.render.engine='CYCLES'
    scene.cycles.samples=40;scene.cycles.use_denoising=True
    scene.cycles.denoiser='OPENIMAGEDENOISE'
    scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3
    scene.cycles.device='CPU'
    try:
        cycles_prefs=bpy.context.preferences.addons['cycles'].preferences
        cycles_prefs.compute_device_type='CUDA';cycles_prefs.get_devices()
        available=False
        for device in cycles_prefs.devices:
            device.use=device.type=='CUDA'
            available=available or device.use
        if available:scene.cycles.device='GPU'
    except Exception as exc:print('CPU_RENDER_FALLBACK',str(exc),flush=True)
    scene.render.resolution_x=1920;scene.render.resolution_y=1440;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None'
    scene.view_settings.exposure=0
    scene.render.image_settings.color_mode='RGB'
    # Add an in-file handoff note and the exact build input for inspection.
    txt=bpy.data.texts.new('READ_ME_首关场景')
    txt.write('交子赶工记 / 开张第一单\n单位米，Blender Z向上；脚底z=0。\n建筑/六工位/工具/锚点独立可编辑。\n90_GUIDES用于尺寸及出生点参考，99_PRESENTATION为摄影灯光。\n当前为场景美术，不包含Unity交互或玩家控制。\n场景按20261110三视图尺寸清单建立。\n')
    txt=bpy.data.texts.new('Dimensions_source.json');txt.write(json.dumps(spec,ensure_ascii=False,indent=2))
    txt=bpy.data.texts.new('READ_ME_鲜明纸艺植被_v05')
    txt.write('v05：恢复金黄、蓝瓦、暖木与绿色色块；重做弯曲树干和层叠银杏扇叶。\n纸草减量，集中墙脚、转角和树根旁；保留低矮宽圆薄纸片。\n纸浆与短纤维纹理保持，外围20×15米，内场12×8米。\n所有外围植物、陈设为非交互背景。\n主效果相机仅供美术展示，原游戏相机与工位接口保持。\n贴图已打包；Unity导入和运行交互仍待对接。\n')
    bpy.context.view_layer.update()
    report={'version':'v05_20261111','blender':bpy.app.version_string,
            'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),
            'station_roots':[r.name for r in roots],
            'station_geometry_bounds':{r.name:bounds(r) for r in roots},
            'anchors':[{'name':o.name,'parent':o.parent.name if o.parent else None,'local':list(o.location),'role':o.get('role','')} for o in bpy.data.objects if o.type=='EMPTY' and o.parent],
            'static_navigation':static_navigation(spec,decor),
            'decoration_roots':[o.name for o in decor],
            'decoration_geometry_bounds':{r.name:bounds(r) for r in decor},
            'exterior_roots':[o.name for o in exterior],
            'exterior_inventory':[{'name':o.name,'asset_id':o.get('asset_id',''),'role':o.get('role',''),
                'bounds':bounds(o),'foliage_style':o.get('foliage_style',''),
                'placement':o.get('placement',''),'crown_style':o.get('crown_style',''),
                'counts':{k:o[k] for k in o.keys() if k.endswith('_count')}} for o in exterior],
            'play_area_xy':[[0,12],[0,8]],'exterior_ground_xy':[[-4,16],[-3.5,11.5]],
            'packed_material_images':len([i for i in bpy.data.images if i.packed_file]),
            'paper_materials':api.paper_material_report,
            'unity_runtime_tested':False,'export_axis_note':'glTF +Y up. Front/back signs require target-engine inspection.'}
    assert len(roots)==6, 'Six station roots required'
    assert report['static_navigation']['all_reachable'], 'A nominal operating position is unreachable'
    # Only content collections: no studio floor, cameras, lights or collision guides.
    bpy.ops.object.select_all(action='DESELECT')
    export_objects=[]
    for ob in scene.objects:
        if any(c.name.startswith(('90_','99_')) for c in ob.users_collection): continue
        ob.select_set(True);export_objects.append(ob)
    glb=OUT/'首关_开张第一单_v05_20261111.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,
        export_apply=True,export_extras=True,export_yup=True)
    report['glb_bytes']=glb.stat().st_size
    bpy.ops.object.select_all(action='DESELECT')
    # Save a useful opening viewport.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.shading.type='MATERIAL'
                area.spaces.active.overlay.show_overlays=False
    blend=OUT/'首关_开张第一单_v05_20261111.blend'
    for curve in list(bpy.data.curves):
        if curve.users==0: bpy.data.curves.remove(curve)
    # All signs are meshes; remove even deferred orphan font references.
    assert not any(ob.type=='FONT' for ob in scene.objects)
    for font in list(bpy.data.fonts):
        bpy.data.fonts.remove(font, do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    (OUT/'场景核验_v05_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SAVED',str(blend),flush=True)
    if '--draft' in sys.argv:
        draft_dir=HERE/'work';draft_dir.mkdir(exist_ok=True)
        scene.render.resolution_x=1024;scene.render.resolution_y=768
        scene.cycles.samples=16
        for transform in (('Standard','AgX') if '--compare-color' in sys.argv else ('Standard',)):
            scene.view_settings.view_transform=transform
            scene.view_settings.look='None' if transform=='Standard' else 'AgX - Medium High Contrast'
            for cam,label in [(art_review,'主效果'),(garden_detail,'银杏'),(grass_detail,'纸草')]:
                scene.camera=cam;scene.render.filepath=str(draft_dir/(label+'_'+transform+'.png'))
                bpy.ops.render.render(write_still=True)
        print('DRAFT_COMPLETE',flush=True)
        return
    for cam,filename in [(art_review,'预览_纸坊主效果_v05_20261111.png'),(overview,'预览_外景总览_v05_20261111.png'),(gameplay,'预览_游戏机位_v05_20261111.png'),(top,'预览_俯视_v05_20261111.png'),(detail,'预览_纸感细节_v05_20261111.png'),(garden_detail,'预览_银杏庭院_v05_20261111.png'),(grass_detail,'预览_纸片草丛_v05_20261111.png')]:
        scene.camera=cam;scene.render.filepath=str(OUT/filename)
        try:bpy.ops.render.render(write_still=True)
        except RuntimeError:
            if scene.cycles.device!='GPU':raise
            scene.cycles.device='CPU'
            bpy.ops.render.render(write_still=True)
        print('RENDERED',filename,flush=True)
    scene.camera=art_review
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    report['rendering']={'engine':scene.render.engine,'device':scene.cycles.device,
        'samples':scene.cycles.samples,'view_transform':scene.view_settings.view_transform,
        'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,
        'compute_backend':'CUDA' if scene.cycles.device=='GPU' else 'CPU',
        'palette_note':'Restore vivid gold, blue tiles and warm wood using Standard color management; packed albedo colors export with GLB.'}
    (OUT/'场景核验_v05_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('BUILD_COMPLETE',flush=True)

if __name__=='__main__': main()
