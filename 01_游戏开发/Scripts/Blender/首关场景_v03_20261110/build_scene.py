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
OUT = ROOT / '01_游戏开发/Models/首关场景_v03_20261110'
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
    scene['project']='交子赶工记';scene['level_id']='level_01';scene['version']='v03_20261110'
    scene['status']='Editable scene art; Unity integration not tested'
    scene['coordinate_mapping']='Blender(X,Y,Z) -> glTF(X,Z,-Y); Unity import orientation untested'
    scene['play_area']='12 x 8 m; existing production area'
    scene['exterior_area']='20 x 15 m; non-interactive scenery, not expanded gameplay'
    api=SceneAPI()
    # Floors stay quieter than the light worktops and teal/red operation accents.
    for key,hex_color in [('floor_workshop','C5AD86'),('floor_courtyard','DFD3B9'),
                          ('garden_soil','C2B492'),('garden_edge','9C906C'),
                          ('paving','B8B29E'),('paving_light','D1C8AC'),
                          ('moss','789B43'),('grass','63873F'),('sage','A2B456'),
                          ('ginkgo_gold','D9AF45'),('ginkgo_light','EED285'),
                          ('ginkgo_ochre','B78935'),('bark','8C6E48')]:
        material=bpy.data.materials.new('MAT_'+key);material.use_nodes=True
        material.diffuse_color=rgba(hex_color)
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgba(hex_color)
        api.materials[key]=material
    enhance_materials(api)
    arch=build_architecture(api,spec)
    roots=build_stations(api,spec)
    decor=build_decoration(api,spec)
    exterior=build_exterior_hardscape(api,spec)+build_exterior_vegetation(api,spec)+build_garden_beds(api,spec)
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
    world.node_tree.nodes['Background'].inputs[1].default_value=.25
    scene.world=world
    for name,loc,power,size in [('Key_soft',(-1,-3,13),1700,5),('Fill',(14,0,9),450,8),('Rim',(7,11,12),800,7)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        ob=bpy.data.objects.new(name,data);stage.objects.link(ob);ob.location=loc;aim(ob,(6,4,0))
    gameplay=camera('CAM_Gameplay_Orthographic',(6.3,-13,18.3),(6,4,.5),14.4)
    overview=camera('CAM_Exterior_Overview',(6.3,-15.5,22),(6,4.0,.6),22.3)
    top=camera('CAM_Top_Orthographic',(6,4,28),(6,4,0),21.5)
    top.rotation_euler=(0,0,0)
    detail=camera('CAM_Paper_Detail',(7.4,2.1,4.9),(8.2,6.25,.65),3.6)
    garden_detail=camera('CAM_Ginkgo_Detail',(-8.4,1.0,7.2),(-2.1,6.45,1.3),6.2)
    grass_detail=camera('CAM_Paper_Grass_Detail',(-5.2,.4,2.6),(-2.1,2.9,.02),3.7)
    scene.camera=overview
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1920;scene.render.resolution_y=1440;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='Standard'
    scene.view_settings.exposure=0
    scene.render.image_settings.color_mode='RGB'
    # Add an in-file handoff note and the exact build input for inspection.
    txt=bpy.data.texts.new('READ_ME_首关场景')
    txt.write('交子赶工记 / 开张第一单\n单位米，Blender Z向上；脚底z=0。\n建筑/六工位/工具/锚点独立可编辑。\n90_GUIDES用于尺寸及出生点参考，99_PRESENTATION为摄影灯光。\n当前为场景美术，不包含Unity交互或玩家控制。\n场景按20261110三视图尺寸清单建立。\n')
    txt=bpy.data.texts.new('Dimensions_source.json');txt.write(json.dumps(spec,ensure_ascii=False,indent=2))
    txt=bpy.data.texts.new('READ_ME_外景_v03')
    txt.write('v03外围庭院：20×15米，内场仍为12×8米。\n银杏、草丛、落叶、石灯与家具为非交互背景。\n前后铺装接内场地面，不代表Unity已开放室外行走。\nCAM_Exterior_Overview为整体展示；CAM_Gameplay_Orthographic保留原工位镜头。\n所有新景物均可独立编辑，源文件已打包材质贴图。\n')
    bpy.context.view_layer.update()
    report={'version':'v03_20261110','blender':bpy.app.version_string,
            'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),
            'station_roots':[r.name for r in roots],
            'station_geometry_bounds':{r.name:bounds(r) for r in roots},
            'anchors':[{'name':o.name,'parent':o.parent.name if o.parent else None,'local':list(o.location),'role':o.get('role','')} for o in bpy.data.objects if o.type=='EMPTY' and o.parent],
            'static_navigation':static_navigation(spec,decor),
            'decoration_roots':[o.name for o in decor],
            'decoration_geometry_bounds':{r.name:bounds(r) for r in decor},
            'exterior_roots':[o.name for o in exterior],
            'exterior_inventory':[{'name':o.name,'asset_id':o.get('asset_id',''),'role':o.get('role',''),
                'bounds':bounds(o),'counts':{k:o[k] for k in o.keys() if k.endswith('_count')}} for o in exterior],
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
    glb=OUT/'首关_开张第一单_v03_20261110.glb'
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
    blend=OUT/'首关_开张第一单_v03_20261110.blend'
    for curve in list(bpy.data.curves):
        if curve.users==0: bpy.data.curves.remove(curve)
    # All signs are meshes; remove even deferred orphan font references.
    assert not any(ob.type=='FONT' for ob in scene.objects)
    for font in list(bpy.data.fonts):
        bpy.data.fonts.remove(font, do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    (OUT/'场景核验_v03_20261110.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SAVED',str(blend),flush=True)
    for cam,filename in [(overview,'预览_外景总览_v03_20261110.png'),(gameplay,'预览_游戏机位_v03_20261110.png'),(top,'预览_俯视_v03_20261110.png'),(detail,'预览_纸感细节_v03_20261110.png'),(garden_detail,'预览_银杏庭院_v03_20261110.png'),(grass_detail,'预览_纸片草丛_v03_20261110.png')]:
        scene.camera=cam;scene.render.filepath=str(OUT/filename)
        bpy.ops.render.render(write_still=True)
        print('RENDERED',filename,flush=True)
    scene.camera=overview
    print('BUILD_COMPLETE',flush=True)

if __name__=='__main__': main()
