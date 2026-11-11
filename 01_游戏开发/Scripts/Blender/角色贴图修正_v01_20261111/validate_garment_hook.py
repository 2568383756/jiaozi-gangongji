from pathlib import Path
import sys,json,hashlib
import bpy
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE))
from garment_materials import apply
OUT=ROOT/'01_游戏开发/Models/角色贴图修正_v01_20261111'
report={'scope':'No original atlas pixel edits, no geometry/weight edits; material and UV changes limited to garment faces.', 'characters':{}}
for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
 path=ROOT/f'01_游戏开发/Models/首批角色_v01_20261111/角色_{label}_整合_v01_20261111.blend'
 file_sha=hashlib.sha256(path.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(path));ob=bpy.data.objects['mesh_'+cid];me=ob.data
 uv=np.empty(len(me.loops)*2,dtype=np.float32);me.uv_layers.active.data.foreach_get('uv',uv)
 mats=[p.material_index for p in me.polygons]
 topology=[tuple(p.vertices) for p in me.polygons]
 images={im.name:hashlib.sha256(bytes(im.packed_file.data)).hexdigest() for im in bpy.data.images if im.packed_file}
 data=apply(ob,cid)
 changed={f['face_index'] for f in data['changes']}
 after_uv=np.empty(len(me.loops)*2,dtype=np.float32);me.uv_layers.active.data.foreach_get('uv',after_uv)
 loops=[i for p in me.polygons if p.index not in changed for i in p.loop_indices]
 checks={
  'mesh_vertices_weights_and_topology_unchanged':data['geometry_weights_unchanged'] and topology==[tuple(p.vertices) for p in me.polygons],
  'original_packed_images_byte_identical':all(hashlib.sha256(bytes(bpy.data.images[n].packed_file.data)).hexdigest()==h for n,h in images.items()),
  'unchanged_faces_keep_material':all(p.material_index==mats[p.index] for p in me.polygons if p.index not in changed),
  'unchanged_faces_keep_exact_uvs':all(np.array_equal(uv[2*i:2*i+2],after_uv[2*i:2*i+2]) for i in loops),
  'source_blend_file_unchanged':hashlib.sha256(path.read_bytes()).hexdigest()==file_sha,
  'new_materials_have_direct_basecolor_texture_and_normalmap':all(any(n.type=='NORMAL_MAP' for n in mat.node_tree.nodes) and mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].is_linked for mat in me.materials if mat.name.startswith('MAT_GarmentRepair')),
 }
 report['characters'][cid]={'changed_faces':len(changed),'cloth_faces':data['cloth_faces'],'belt_faces':data['belt_faces'],
  'source_blend_sha256':file_sha,'original_image_sha256':images,'checks':checks,'all_passed':all(checks.values())}
report['all_passed']=all(c['all_passed'] for c in report['characters'].values())
(OUT/'材质修正独立核验_v01_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
