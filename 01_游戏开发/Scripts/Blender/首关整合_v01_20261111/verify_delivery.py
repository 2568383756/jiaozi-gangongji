"""Check the finished batch's reports, hashes, and local documentation links."""
from pathlib import Path
import hashlib, json, re
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[4]
DEV=ROOT/'01_游戏开发'
OUT=DEV/'Models/首关整合_v01_20261111'
docs=[ROOT/'README.md',DEV/'Docs/首关角色与道具整合_v01_20261111.md',
      DEV/'Imports/角色源仓_20261111/README.md']
for folder in ['首批角色_v01_20261111','首关道具_v01_20261111','首关整合_v01_20261111']:
    docs.extend((DEV/'Models'/folder).glob('*.md'))
links=[];missing=[]
for doc in docs:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text(encoding='utf-8-sig')):
        if target.startswith(('https:','http:','#','mailto:')):continue
        target=unquote(target.split('#')[0].strip('<>'))
        if not target:continue
        p=(doc.parent/target).resolve()
        rec={'document':str(doc.relative_to(ROOT)),'target':target,'exists':p.exists()}
        links.append(rec)
        if not p.exists():missing.append(rec)

reports={
 'characters':DEV/'Models/首批角色_v01_20261111/角色复导核验_v01_20261111.json',
 'props':DEV/'Models/首关道具_v01_20261111/道具实测验证_v01_20261111.json',
 'assembly':OUT/'整合核验_v01_20261111.json'}
states={}
for key,p in reports.items():
    data=json.loads(p.read_text(encoding='utf-8-sig'))
    checks=data.get('checks',[])
    # Individual report formats use pass/passed/ok; the aggregate flag is authoritative.
    states[key]={'file':str(p.relative_to(ROOT)),'total':data.get('check_count',data.get('total',len(checks))),
                 'all_passed':data.get('all_passed',data.get('all_checks_passed',False))}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assembly=json.loads(reports['assembly'].read_text(encoding='utf-8'))
hash_checks=[{'file':str(OUT/'首关_角色道具整合_v01_20261111.blend'),'matches':sha(OUT/'首关_角色道具整合_v01_20261111.blend')==assembly['blend_sha256']}]
hash_checks.append({'file':assembly['source_scene'],'matches':sha(ROOT/assembly['source_scene'])==assembly['source_scene_sha256']})
for c in assembly['characters']:
    hash_checks.append({'file':c['source'],'matches':sha(ROOT/c['source'])==c['source_sha256']})
for item in assembly['station_prop_instances']:
    hash_checks.append({'file':item['source'],'matches':sha(ROOT/item['source'])==item['source_sha256']})
for im in assembly['previews']:
    hash_checks.append({'file':im['file'],'matches':sha(OUT/im['file'])==im['sha256']})
preview_paths=[]
for folder in ['首批角色_v01_20261111','首关道具_v01_20261111','首关整合_v01_20261111']:
    preview_paths.extend((DEV/'Models'/folder).glob('预览_*.png'))
summary={'version':'v01_20261111','reports':states,'local_link_count':len(links),'missing_links':missing,
         'hash_checks':hash_checks,'preview_count':len(preview_paths),
         'asset_check_total':sum(s['total'] for s in states.values()),'unity_tested':False}
summary['all_passed']=not missing and all(v['all_passed'] for v in states.values()) and all(c['matches'] for c in hash_checks) and len(preview_paths)==9
(OUT/'交付文件核对_v01_20261111.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:summary[k] for k in ['reports','local_link_count','missing_links','preview_count','asset_check_total','all_passed']},ensure_ascii=False,indent=2))
if not summary['all_passed']:raise SystemExit(1)
