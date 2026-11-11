"""Assemble reviewed character and prop deliveries into a copy of scene v05.

This is an art demonstration, not a saved gameplay state or Unity scene.
Usage: blender --background --factory-startup --python build_assembly.py
       Optional -- --render, or -- --render-only after an existing build.
"""
from pathlib import Path
import bpy, json, math, sys, hashlib
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEV = ROOT / '01_游戏开发'
OUT = DEV / 'Models/首关整合_v01_20261111'
OUT.mkdir(parents=True, exist_ok=True)
BASE = DEV / 'Models/首关场景_v05_20261111/首关_开张第一单_v05_20261111.blend'
CHAR = DEV / 'Models/首批角色_v01_20261111'
PROP = DEV / 'Models/首关道具_v01_20261111'
BLEND = OUT / '首关_角色道具整合_v01_20261111.blend'
CONFIG = HERE / 'assembly_config.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def descendants(root):
    result=[root]
    for child in root.children: result.extend(descendants(child))
    return result
def active_action(rig, action):
    rig.animation_data_create()
    rig.animation_data.action=action
    if len(action.slots): rig.animation_data.action_slot=action.slots[0]
def aim(ob, target):
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def matrix_values(ob):
    return [round(float(x),7) for row in ob.matrix_world for x in row]
def camera(name, position, target, ortho):
    data=bpy.data.cameras.new(name); data.type='ORTHO';data.ortho_scale=ortho
    ob=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(ob)
    ob.location=position;aim(ob,target);return ob
def find_file(folder, pattern):
    found=list(folder.glob(pattern))
    if len(found)!=1: raise RuntimeError(f'Expected one {pattern}, found {found}')
    return found[0]

def deduplicate_packed_images():
    """Independent GLBs embed shared textures; reuse only byte-identical images."""
    seen={};remapped=[];before=len(bpy.data.images)
    for im in list(bpy.data.images):
        if im.source!='FILE' or not im.packed_file: continue
        key=(hashlib.sha256(im.packed_file.data).hexdigest(),tuple(im.size),
             im.colorspace_settings.name,im.alpha_mode)
        if key in seen:
            canonical=seen[key]
            remapped.append({'duplicate':im.name,'retained':canonical.name,'sha256':key[0]})
            im.user_remap(canonical)
            bpy.data.images.remove(im)
        else: seen[key]=im
    return {'before':before,'after':len(bpy.data.images),'byte_identical_remaps':remapped}

def import_prop(asset_id, instance_name):
    path=find_file(PROP, '**/'+asset_id+'.glb')
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    added=set(bpy.data.objects)-before
    roots=[o for o in added if o.parent not in added]
    if len(roots)!=1:
        root=bpy.data.objects.new(instance_name,None)
        bpy.context.scene.collection.objects.link(root)
        for o in roots: o.parent=root
    else: root=roots[0]
    for o in added:
        o.name=instance_name+'__'+o.name
        for col in list(o.users_collection): col.objects.unlink(o)
        prop_collection.objects.link(o)
    if root not in added:
        for col in list(root.users_collection): col.objects.unlink(root)
        prop_collection.objects.link(root)
    root.name=instance_name
    root['asset_id']=asset_id;root['art_demonstration']=True
    root['not_gameplay_initial_state']=True
    return root, path

def build():
    bpy.ops.wm.open_mainfile(filepath=str(BASE),load_ui=False)
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene
    scene['version']='integration_v01_20261111'
    scene['purpose']='Art assembly with animated characters and replaceable props; not gameplay initial state'
    scene['unity_tested']=False
    cfg=json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    interface_roles={'paper_anchor','interaction_target','player_standing_point'}
    baseline={o.name:matrix_values(o) for o in scene.objects if o.get('role') in interface_roles}
    disabled=[]
    legacy_subtree=set()
    for name in cfg.get('hide_v05_subtrees',[]):
        ob=bpy.data.objects.get(name)
        if ob is not None: legacy_subtree.update(descendants(ob))
    for ob in list(scene.objects):
        if ob in legacy_subtree or any(ob.name.startswith(prefix) for prefix in cfg['hide_v05_prefixes']):
            if ob.get('role') in interface_roles: raise RuntimeError('Cannot disable gameplay interface '+ob.name)
            ob.hide_render=True;ob.hide_viewport=True;ob['replaced_by_v01_props']=True
            disabled.append(ob.name)
    global prop_collection
    prop_collection=bpy.data.collections.new('70_PROP_INSTANCES_v01')
    scene.collection.children.link(prop_collection)
    instances=[]
    for item in cfg['station_props']:
        root,path=import_prop(item['asset_id'],item['instance'])
        parent=bpy.data.objects[item['parent']]
        root.parent=parent;root.matrix_parent_inverse=Matrix.Identity(4)
        root.location=item.get('location',[0,0,0])
        root.rotation_euler=[math.radians(a) for a in item.get('rotation_deg',[0,0,0])]
        root.scale=(1,1,1)
        instances.append(dict(item,source=str(path.relative_to(ROOT)),source_sha256=sha(path)))
    chars=[]
    for item in cfg['characters']:
        cid=item['id'];path=find_file(CHAR,item['blend_pattern'])
        with bpy.data.libraries.load(str(path),link=False) as (src,dst):
            name='CHAR_'+cid
            if name not in src.collections: raise RuntimeError('Missing '+name)
            dst.collections=[name]
            dst.actions=[a for a in src.actions if a.startswith(cid+'_')]
        col=dst.collections[0];scene.collection.children.link(col)
        for act in dst.actions: act.use_fake_user=True
        root=bpy.data.objects['character_'+cid]
        root.location=item['location'];root.rotation_euler=(0,0,math.radians(item.get('rotation_deg',0)))
        rig=bpy.data.objects['rig_'+cid]
        action=bpy.data.actions[cid+'_CarryIdle']
        active_action(rig,action)
        scene.frame_set(1);bpy.context.view_layer.update()
        socket=next((o for o in descendants(root) if o.get('role')=='carry_socket' or o.name.endswith('HoldPoint')),None)
        if socket is None and 'HoldPoint' in rig.pose.bones:
            socket=bpy.data.objects.new(cid+'_HoldPoint_adapter',None)
            col.objects.link(socket)
            socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='HoldPoint'
            socket['role']='carry_socket';socket['purpose']='Blender bone-head adapter, no extra gameplay socket'
            bpy.context.view_layer.update()
            socket.matrix_world=rig.matrix_world @ rig.pose.bones['HoldPoint'].matrix
            bpy.context.view_layer.update()
        if socket is None: raise RuntimeError('Missing carry socket for '+cid)
        carried,prop_path=import_prop(item['carried_asset'],cid+'_held_single_sheet')
        carried.parent=socket;carried.matrix_parent_inverse=Matrix.Identity(4)
        carried.location=(0,0,0);carried.rotation_euler=(0,0,0);carried.scale=(1,1,1)
        root['player_demo']=item['player'];root['art_demonstration']=True
        chars.append(dict(item,source=str(path.relative_to(ROOT)),source_sha256=sha(path),
                          socket=socket.name,action=action.name,carried_root=carried.name))
    scene.render.fps=30;scene.frame_start=1;scene.frame_end=65;scene.frame_set(1)
    bpy.context.view_layer.update()
    after={name:matrix_values(bpy.data.objects[name]) for name in baseline}
    checks=[{'name':'all_21_station_interfaces_unchanged','pass':len(baseline)==21 and baseline==after},
            {'name':'two_character_roots','pass':len(chars)==2},
            {'name':'single_carried_item_each','pass':all(len([c for c in bpy.data.objects[x['socket']].children if c.get('asset_id')])==1 for x in chars)},
            {'name':'six_station_roots_preserved','pass':all(bpy.data.objects.get('station_'+s) for s in ['pulp','dry','print','stamp','delivery','shared'])}]
    close=camera('CAM_Character_Prop_Review',(7.8,-.6,3.1),(5.2,4.2,.55),3.7)
    close['purpose']='Carry pose and single sheet art review'
    scene.camera=bpy.data.objects['CAM_Gameplay_Orthographic']
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.file.pack_all()
    texture_optimization=deduplicate_packed_images()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),compress=True)
    report={'version':'v01_20261111','blender':bpy.app.version_string,'source_scene':str(BASE.relative_to(ROOT)),
            'source_scene_sha256':sha(BASE),'characters':chars,'station_prop_instances':instances,
            'disabled_v05_visual_objects':disabled,'interfaces':after,'build_checks':checks,'checks':checks,
            'all_passed':all(x['pass'] for x in checks),'unity_tested':False,
            'scope':'Art assembly; displayed materials and carried sheets do not encode actual initial inventory.',
            'texture_optimization':texture_optimization,
            'blend':str(BLEND.relative_to(ROOT)),'blend_sha256':sha(BLEND)}
    (OUT/'整合核验_v01_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if not report['all_passed']: raise RuntimeError('Assembly check failed')
    print('ASSEMBLY_READY',BLEND,flush=True)

def render():
    scene=bpy.context.scene
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA';prefs.get_devices()
    for device in prefs.devices: device.use=device.type=='CUDA'
    scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=32
    scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
    scene.render.resolution_x=1920;scene.render.resolution_y=1440;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    for cam,stem in [('CAM_Gameplay_Orthographic','预览_首关双人整合'),
                     ('CAM_Character_Prop_Review','预览_双人单张持物'),
                     ('CAM_Paper_Detail','预览_工位道具整合')]:
        scene.camera=bpy.data.objects[cam]
        scene.render.filepath=str(OUT/(stem+'_v01_20261111.png'))
        bpy.ops.render.render(write_still=True)
    print('ASSEMBLY_RENDER_COMPLETE',flush=True)

if __name__=='__main__':
    if '--render-only' in sys.argv: bpy.ops.wm.open_mainfile(filepath=str(BLEND),load_ui=False)
    else: build()
    if '--render' in sys.argv or '--render-only' in sys.argv: render()
