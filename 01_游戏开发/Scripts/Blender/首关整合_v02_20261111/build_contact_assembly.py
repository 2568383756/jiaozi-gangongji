"""Rebuild the reviewed first-level scene with reachable work surfaces.

Uses immutable v01 assembly, v02 characters and explicit station adaptation.
Blender 5.3 CLI. --render-only renders the saved result; --render builds too.
"""
from pathlib import Path
import bpy, hashlib, importlib.util, json, math, sys
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEV = ROOT / '01_游戏开发'
OUT = DEV / 'Models/首关整合_v02_20261111'
OUT.mkdir(parents=True, exist_ok=True)
BASE = DEV / 'Models/首关整合_v01_20261111/首关_角色道具整合_v01_20261111.blend'
CHAR = DEV / 'Models/首批角色_v02_20261111'
BLEND = OUT / '首关_触台比例整合_v02_20261111.blend'
REPORT = OUT / '触台整合核验_v02_20261111.json'
STATIONS = ['pulp', 'dry', 'print', 'stamp', 'delivery', 'shared']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

shared = load_module('assembly_v01_helpers', DEV / 'Scripts/Blender/首关整合_v01_20261111/build_assembly.py')
descendants = shared.descendants
active_action = shared.active_action
camera = shared.camera

def replace_characters():
    scene = bpy.context.scene
    for cid in ['zhituan', 'yintao']:
        old_root = bpy.data.objects.get('character_' + cid)
        if old_root:
            for ob in reversed(descendants(old_root)):
                bpy.data.objects.remove(ob, do_unlink=True)
        old_col = bpy.data.collections.get('CHAR_' + cid)
        if old_col: bpy.data.collections.remove(old_col)
        for action in list(bpy.data.actions):
            if action.name.startswith(cid + '_'): bpy.data.actions.remove(action)
    results = []
    for cid, label in [('zhituan', '纸团'), ('yintao', '印桃')]:
        path = CHAR / ('角色_' + label + '_整合_v02_20261111.blend')
        with bpy.data.libraries.load(str(path), link=False) as (source, dest):
            dest.collections = ['CHAR_' + cid]
            dest.actions = [n for n in source.actions if n.startswith(cid + '_')]
        scene.collection.children.link(dest.collections[0])
        for action in dest.actions: action.use_fake_user = True
        results.append({'id':cid, 'source':str(path.relative_to(ROOT)), 'sha256':sha(path)})
    return results

def visible_content_objects():
    result=[]
    for ob in bpy.context.scene.objects:
        if ob.type not in {'MESH', 'EMPTY'}: continue
        if ob.hide_render or ob.hide_viewport: continue
        if any(c.name.startswith(('90_', '99_', 'CHAR_')) for c in ob.users_collection): continue
        if ob.get('purpose') == 'Blender bone-head adapter, no extra gameplay socket': continue
        result.append(ob)
    return result

def export_objects(objects, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects: ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(filepath), export_format='GLB',
        use_selection=True, export_apply=True, export_extras=True,
        export_yup=True, export_animations=False)
    return {'file':str(filepath.relative_to(ROOT)), 'sha256':sha(filepath),
            'bytes':filepath.stat().st_size,
            'mesh_count':sum(ob.type=='MESH' for ob in objects)}

def export_static_assets():
    exports=[]
    exports.append(export_objects(visible_content_objects(), OUT / '首关_触台比例环境_v02_20261111.glb'))
    folder=OUT/'工位GLB';folder.mkdir(exist_ok=True)
    for sid in STATIONS:
        root=bpy.data.objects['station_'+sid]
        original=root.matrix_world.copy()
        root.matrix_world=Matrix.Identity(4)
        bpy.context.view_layer.update()
        objects=[o for o in descendants(root) if o.type in {'MESH','EMPTY'} and not o.hide_render and not o.hide_viewport]
        exports.append(export_objects(objects,folder/(root.name+'.glb')))
        root.matrix_world=original
        bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    return exports

def pose_at_station(cid, sid, action='Work', slot=None):
    root=bpy.data.objects['character_'+cid]
    rig=bpy.data.objects['rig_'+cid]
    station=bpy.data.objects['station_'+sid]
    standing=next(o for o in descendants(station) if o.get('role')=='player_standing_point' and (slot is None or o.get('slot_id')==slot))
    root.location=standing.matrix_world.translation
    # Characters face -Y; northern operating sides use zero rotation.
    root.rotation_euler=(0,0,math.pi if root.location.y < station.location.y else 0)
    active_action(rig,bpy.data.actions[cid+'_'+action])
    bpy.context.view_layer.update()

def arrange_review():
    pose_at_station('zhituan','print')
    pose_at_station('yintao','stamp')
    scene=bpy.context.scene
    scene.frame_start=1;scene.frame_end=31;scene.render.fps=30;scene.frame_set(1)
    bpy.context.view_layer.update()

def build():
    bpy.ops.wm.open_mainfile(filepath=str(BASE),load_ui=False)
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene
    scene['version']='contact_integration_v02_20261111'
    scene['unity_tested']=False
    scene['purpose']='Measured art contact sample, not an initial gameplay state'
    characters=replace_characters()
    module=load_module('station_contact_adaptation', DEV/'Scripts/Blender/首关工位适配_v01_20261111/adapt_stations.py')
    adaptation=module.apply()
    bpy.context.view_layer.update()
    arrange_review()
    camera('CAM_Contact_Print',(9.1,7.2,2.0),(7.85,5.8,.5),2.5)
    camera('CAM_Contact_Stamp',(13.1,1.4,2.0),(10.3,3.35,.48),2.4)
    camera('CAM_Contact_Side',(5.0,5.72,.65),(8.0,5.72,.65),1.9)
    camera('CAM_Contact_Dry',(4.2,7.55,3.0),(2.3,6.15,.6),3.6)
    bpy.data.objects['CAM_Contact_Print'].data.clip_start=.6
    bpy.data.objects['CAM_Contact_Dry'].data.clip_start=.6
    exports=export_static_assets()
    scene.camera=bpy.data.objects['CAM_Gameplay_Orthographic']
    bpy.ops.file.pack_all()
    texture_optimization=shared.deduplicate_packed_images()
    note=bpy.data.texts.new('READ_ME_触台比例_v02')
    note.write('角色与工位按真实掌面校准。尺寸与站位以本版本 JSON 为准。\n原 v05 / 整合 v01 保留。工具固定，纸张单件。\n这是一组美术接触样本，未在对方 Unity 工程运行。\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),compress=True)
    report={'version':'v02_20261111','source':str(BASE.relative_to(ROOT)), 'source_sha256':sha(BASE),
            'characters':characters,'station_adaptation':adaptation,'exports':exports,
            'texture_optimization':texture_optimization,'blend_sha256':sha(BLEND),
            'review_cutaway':{'cameras':['CAM_Contact_Print','CAM_Contact_Dry'],
                'temporary_hidden_collections':['ENV_02_Back_Walls','ENV_03_Low_Boundary','ENV_04_Open_Eaves','ENV_05_Decoration'],
                'saved_model_and_gameplay_camera_unaffected':True},
            'unity_runtime_tested':False}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CONTACT_ASSEMBLY_SAVED',BLEND,flush=True)

def render_setup():
    scene=bpy.context.scene
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='CUDA'
    scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=32
    scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
    scene.render.resolution_x=1920;scene.render.resolution_y=1440;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    return scene

def render_baseline():
    bpy.ops.wm.open_mainfile(filepath=str(BASE),load_ui=False)
    for cid in ['zhituan','yintao']:
        ob=bpy.data.objects.get(cid+'_held_single_sheet')
        if ob:
            for child in descendants(ob):child.hide_render=True
    arrange_review()
    scene=render_setup()
    scene.camera=camera('CAM_Baseline_Side',(5.0,5.72,.65),(8.0,5.72,.65),1.9)
    scene.render.filepath=str(OUT/'预览_旧版触台侧面对照_20261111.png')
    bpy.ops.render.render(write_still=True)
    print('BASELINE_RENDER_COMPLETE',flush=True)

def render():
    scene=render_setup()
    def render_one(cam,stem,cutaway=False):
        hidden={}
        if cutaway:
            for name in ['ENV_02_Back_Walls','ENV_03_Low_Boundary','ENV_04_Open_Eaves','ENV_05_Decoration']:
                col=bpy.data.collections.get(name)
                if col:
                    for ob in col.all_objects:
                        if ob is None:continue
                        hidden[ob]=ob.hide_render;ob.hide_render=True
        try:
            scene.camera=bpy.data.objects[cam]
            scene.render.filepath=str(OUT/(stem+'_v02_20261111.png'))
            bpy.ops.render.render(write_still=True)
        finally:
            for ob,value in hidden.items():ob.hide_render=value
    for cam,stem in [('CAM_Gameplay_Orthographic','预览_触台比例全景'),
                     ('CAM_Contact_Print','预览_纸团印台接触'),
                     ('CAM_Contact_Stamp','预览_印桃章台接触'),
                     ('CAM_Contact_Side','预览_台高侧面核对')]:
        render_one(cam,stem,cam=='CAM_Contact_Print')
    pose_at_station('zhituan','dry',slot='A')
    pose_at_station('yintao','dry',slot='B')
    scene.frame_set(1);bpy.context.view_layer.update()
    render_one('CAM_Contact_Dry','预览_双槽低位晾纸',True)
    arrange_review()
    print('CONTACT_RENDER_COMPLETE',flush=True)

if __name__=='__main__':
    if '--baseline' in sys.argv:render_baseline()
    else:
        if '--render-only' in sys.argv:bpy.ops.wm.open_mainfile(filepath=str(BLEND),load_ui=False)
        else:build()
        if '--render' in sys.argv or '--render-only' in sys.argv:render()
