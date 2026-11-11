"""Check this batch's file sizes, source links and Git index; no mutation of Git."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OUT=ROOT/'01_游戏开发/Models/首关整合_v02_20261111'
PREFIXES=[
    '01_游戏开发/Art/角色/服装贴图修正参考_v01_20261111/',
    '01_游戏开发/Models/首批角色_v02_20261111/',
    '01_游戏开发/Models/首关整合_v02_20261111/',
    '01_游戏开发/Models/首关工位适配_v01_20261111/',
    '01_游戏开发/Models/角色贴图修正_v01_20261111/',
    '01_游戏开发/Scripts/Blender/角色整合_v02_20261111/',
    '01_游戏开发/Scripts/Blender/首关整合_v02_20261111/',
    '01_游戏开发/Scripts/Blender/首关工位适配_v01_20261111/',
    '01_游戏开发/Scripts/Blender/角色贴图修正_v01_20261111/',
    '01_游戏开发/Scripts/Blender/触台比例核验_v01_20261111/',
    '01_游戏开发/Docs/首关触台比例与角色材质修正_v01_20261111.md',
    'README.md']
def git_paths(*args):
    result=subprocess.run(['git','-C',str(ROOT),*args,'-z'],capture_output=True,check=True)
    return set(p.decode('utf-8') for p in result.stdout.split(b'\0') if p)
tracked=git_paths('ls-files');untracked=git_paths('ls-files','--others','--exclude-standard')
owned=sorted(p for p in tracked|untracked if any(p.startswith(prefix) for prefix in PREFIXES))
manifest='01_游戏开发/Models/首关整合_v02_20261111/批次文件与索引核对_v01_20261111.json'
owned=[p for p in owned if p!=manifest]
records=[]
for rel in owned:
    path=ROOT/rel
    if not path.is_file():continue
    records.append({'path':rel,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
links=[]
for rel in owned:
    path=ROOT/rel
    if path.suffix.lower()!='.md':continue
    text=path.read_text(encoding='utf-8-sig')
    urls=re.findall(r'\]\(([^)]+)\)',text)+re.findall(r'\bsrc="([^"]+)"',text)
    for url in urls:
        if url.startswith(('http:','https:','#','mailto:')):continue
        target=unquote(url.split('#')[0].split(' "')[0]).strip('<>')
        if not target:continue
        absolute=(path.parent/target).resolve()
        try:
            target_rel=absolute.relative_to(ROOT).as_posix()
            in_index=(target_rel in tracked or (absolute.is_dir() and any(p.startswith(target_rel.rstrip('/')+'/') for p in tracked)))
        except ValueError:
            target_rel=None;in_index=False
        links.append({'from':rel,'target':target,'exists':absolute.exists(),'git_target':target_rel,'in_index':in_index})
checks=[{'name':'no_file_reaches_95_MiB','pass':all(r['bytes']<95*1024*1024 for r in records)},
        {'name':'all_local_markdown_targets_exist','pass':all(x['exists'] for x in links)},
        {'name':'no_cache_or_log_in_batch','pass':not any('/work/' in p or '__pycache__' in p or p.endswith(('.pyc','.log','.blend1','.blend2')) for p in owned)}]
if '--index' in sys.argv:
    checks.append({'name':'all_batch_files_in_git_index','pass':all(r['path'] in tracked for r in records)})
    checks.append({'name':'all_local_link_targets_in_git_index','pass':all(x['in_index'] for x in links)})
report={'version':'v01_20261111','scope':'Explicit current contact/garment/hand batch only; unrelated opening-book work excluded.',
        'file_count':len(records),'bytes':sum(r['bytes'] for r in records),'link_count':len(links),
        'checks':checks,'all_passed':all(c['pass'] for c in checks),'files':records,'links':links}
(ROOT/manifest).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'files':len(records),'links':len(links),'MiB':round(report['bytes']/1024**2,2),
    'pass':report['all_passed'],'failed_links':[x for x in links if not x['exists'] or ('--index' in sys.argv and not x['in_index'])],
    'failed_checks':[c for c in checks if not c['pass']]},ensure_ascii=False))
if not report['all_passed']:raise SystemExit(1)
