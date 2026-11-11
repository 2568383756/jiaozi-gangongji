"""Render the existing, validated asset pack; does not re-export GLBs."""
import bpy,sys,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from build_props import OUT,aim

bpy.ops.wm.open_mainfile(filepath=str(OUT/'首关纸艺道具包_v01_20261111.blend'))
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='CUDA';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='CUDA'
scene.cycles.device='GPU' if any(d.type=='CUDA' for d in prefs.devices) else 'CPU'
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
bpy.data.objects['presentation_ground'].location.z=-.026
floor=bpy.data.objects['presentation_ground']
backdrop=bpy.data.materials.get('MAT_props_studio_warmgray') or bpy.data.materials.new('MAT_props_studio_warmgray')
backdrop.use_nodes=True
bsdf=next((n for n in backdrop.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) or backdrop.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
output=next((n for n in backdrop.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None) or backdrop.node_tree.nodes.new('ShaderNodeOutputMaterial')
backdrop.node_tree.links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
bsdf.inputs['Base Color'].default_value=(.45,.40,.32,1);bsdf.inputs['Roughness'].default_value=.9
floor.data.materials.clear();floor.data.materials.append(backdrop)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.32
bpy.data.lights['large_key'].energy=240
bpy.data.lights['soft_fill'].energy=126
detail=bpy.data.objects['Camera_Black_Red'];detail.location=(.56,1.05,6);aim(detail,(.56,1.05,0))
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for camera,name,res in ((bpy.data.objects['Camera_Overview'],'预览_首关道具总览_v01_20261111.png',(1800,1250)),
                        (detail,'预览_黑票与朱票分层_v01_20261111.png',(1600,1000))):
    scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=res
    scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
    print('RENDERED',name,flush=True)
scene.camera=bpy.data.objects['Camera_Overview']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'首关纸艺道具包_v01_20261111.blend'),compress=True)
path=OUT/'资产清单_v01_20261111.json'
manifest=json.loads(path.read_text(encoding='utf-8'))
manifest['previews']=['预览_首关道具总览_v01_20261111.png','预览_黑票与朱票分层_v01_20261111.png']
manifest['render']={'engine':'Cycles','device':scene.cycles.device,'samples':48,'view_transform':'Standard',
                    'exposure':0,'key_energy':240,'fill_energy':126,'world_strength':.32,
                    'backdrop_linear_rgb':[.45,.40,.32]}
manifest['primary_artifact_sha256']={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest()
    for name in ['首关纸艺道具包_v01_20261111.blend']+manifest['previews']}
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('PROPS_RENDER_COMPLETE',flush=True)
