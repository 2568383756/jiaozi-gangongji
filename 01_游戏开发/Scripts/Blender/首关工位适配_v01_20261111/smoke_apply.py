"""Read-only source load; execute station adapter and write its report, no scene save."""
import bpy,sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import adapt_stations
ROOT=HERE.parents[3]
OUT=ROOT/'01_游戏开发/Models/首关工位适配_v01_20261111'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'01_游戏开发/Models/首关整合_v01_20261111/首关_角色道具整合_v01_20261111.blend'),load_ui=False)
report=adapt_stations.apply()
(OUT/'工位适配报告_v01_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ADAPT_READY',len(report['stations']),report['checks'],flush=True)
