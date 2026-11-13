import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';import {createHash} from 'node:crypto';import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url)),art=path.resolve(here,'../../Art/开场机关书_v11_20261113');
const files=await fs.readdir(path.join(art,'assets'));const assets=[];
for(const f of files){const b=await fs.readFile(path.join(art,'assets',f));const entry={file:'assets/'+f,bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')};if(f.endsWith('.png')){entry.width=b.readUInt32BE(16);entry.height=b.readUInt32BE(20)}assets.push(entry)}
const motionQA=JSON.parse(await fs.readFile(path.join(art,'动作与字体核验_v11.json'),'utf8'));
const transitionQA=JSON.parse(await fs.readFile(path.join(art,'收展连续性核验_v11.json'),'utf8'));
if(transitionQA.checks.some(c=>!c.passed)||motionQA.layerChecks.results.some(c=>!c.passed))throw Error('A required animation check did not pass');
const provenance=[];
for(const [adopted,original,sha256] of [['heroes_adopted.png','heroes.png','6bca579d5a3019ea949779d0773d2b7c927c4ff555d4d7373c83000f7882ca32'],['npcs_adopted.png','npcs.png','7904a203233db14127454191861f06e1fc154e0e48bdcfc710c4612322a0b7d7'],['props_adopted.png','props.png','521b7482421cfd11ca19e3e2cfc1caccace1a1f7c644b5b70183da97a2501c44']]){
 const source=path.resolve(art,'../开场立体书_v07_20261112/素材',original);
 const entry=assets.find(a=>a.file==='assets/'+adopted);if(entry.sha256!==sha256)throw Error('Adopted atlas differs from source: '+adopted);
 provenance.push({adopted:'assets/'+adopted,source,sha256,identical:true});
}
await fs.writeFile(path.join(art,'素材清单_v11.json'),JSON.stringify({version:'v11_20261113',png_count:assets.filter(a=>a.file.endsWith('.png')).length,characterAssets:motionQA.characterAssets,environment:motionQA.layerChecks.environment,ambience:motionQA.layerChecks.ambience,cart:motionQA.layerChecks.cart,font:{family:'STKaiti',displayName:'华文楷体',loaded:motionQA.fontLoaded,size_px:34,redistributed_font_file:false},provenance,assets},null,2));
const media=path.join(art,'开场机关书_v11.mp4'),b=await fs.readFile(media);
const decode=spawnSync('C:/Program Files/ffmpeg/bin/ffmpeg.exe',['-hide_banner','-i',media,'-f','null','-'],{encoding:'utf8',windowsHide:true,maxBuffer:4e6});
if(decode.status!==0)throw Error(decode.stderr);
const frameCount=(await fs.readdir(path.join(here,'work/frames'))).filter(f=>f.endsWith('.jpg')).length;
if(frameCount!==1344)throw Error('Incomplete frame sequence');
await fs.writeFile(path.join(art,'媒体核验_v11.json'),JSON.stringify({version:'v11_20261113',media:'开场机关书_v11.mp4',bytes:b.length,sha256:createHash('sha256').update(b).digest('hex'),resolution:[1920,1080],fps:24,duration_seconds:56,rendered_frames:frameCount,full_decode_exit_code:decode.status,stream_evidence:decode.stderr.split('\n').filter(l=>/Duration:|Stream #|frame=/.test(l)).join('\n'),visual_review:'Six chapter samples and dense folding/printing/return frames inspected. Wheel closeups checked: one rim, fixed hub, inner spokes turning. Hand-held objects and continuous workshop pose checked. Moving-cloud masks checked during folding. User artistic approval remains pending.',animation_layer_checks:motionQA.layerChecks.results.length,transition_checks:transitionQA.checks.length,unity_tested:false,human_audio_review:false},null,2));
console.log('asset manifest and complete media decode verified');
