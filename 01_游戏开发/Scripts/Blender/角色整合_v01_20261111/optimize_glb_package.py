import bpy,json
from pathlib import Path
OUT=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104/01_游戏开发/Models/首批角色_v01_20261111')
report_path=OUT/'角色整合报告_v01_20261111.json'
report=json.loads(report_path.read_text(encoding='utf-8'))
for char in report['characters']:
 bpy.ops.wm.open_mainfile(filepath=char['files']['blend'],load_ui=False)
 path=Path(char['files']['glb']);old_bytes=path.stat().st_size
 bpy.ops.object.select_all(action='DESELECT')
 for o in bpy.data.collections[char['core_collection']].all_objects:o.select_set(True)
 bpy.context.view_layer.objects.active=bpy.data.objects[char['rig']]
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
   export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,
   export_def_bones=False,export_yup=True,export_extras=True,export_materials='EXPORT',export_cameras=False,export_lights=False,
   export_all_influences=False,export_image_format='JPEG',export_jpeg_quality=95,export_image_quality=95,export_current_frame=False)
 char['glb_texture_encoding']={'format':'JPEG','quality':95,'size':[2048,2048],
   'authoring_texture':'packed 2048 PNG retained in BLEND and FBX','previous_png_glb_bytes':old_bytes,
   'jpeg_glb_bytes':path.stat().st_size}
 print('PACKAGE',char['character_id'],old_bytes,path.stat().st_size,flush=True)
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
