"""Measure custom-normal re-encoding on in-memory copies; never save models."""
import bpy, hashlib, json, math
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
report = {'method': 'Read native v01. Copy mesh in memory, set identical corner normals, then read the stored normals. Do not save any Blender asset.',
          'characters': {}}
def delta(a, b):
    a, b = Vector(a), Vector(b)
    chord = (a-b).length
    angle = math.degrees(2*math.asin(min(1.0, (a.normalized()-b.normalized()).length/2)))
    return chord, angle

for cid, label in [('zhituan', '纸团'), ('yintao', '印桃')]:
    path = ROOT / f'01_游戏开发/Models/首批角色_v01_20261111/角色_{label}_整合_v01_20261111.blend'
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    source = bpy.data.objects['mesh_'+cid].data
    before = [tuple(n.vector) for n in source.corner_normals]
    copied = source.copy()
    copied.normals_split_custom_set(before)
    errors = [delta(a, b.vector) for a, b in zip(before, copied.corner_normals)]
    report['characters'][cid] = {'source': str(path.relative_to(ROOT)), 'source_sha256': sha,
        'source_unchanged': sha == hashlib.sha256(path.read_bytes()).hexdigest(),
        'loops': len(before), 'identical_input_roundtrip_max_chord_delta': max(e[0] for e in errors),
        'identical_input_roundtrip_max_angle_deg': max(e[1] for e in errors)}

(HERE/'自定义法线同值回存核验_v01_20261111.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
