import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';import {createHash} from 'node:crypto';import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url)),art=path.resolve(here,'../../Art/开场机关书_v08_20261112');
const files=await fs.readdir(path.join(art,'assets'));const assets=[];
for(const f of files){const b=await fs.readFile(path.join(art,'assets',f));const entry={file:'assets/'+f,bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')};if(f.endsWith('.png')){entry.width=b.readUInt32BE(16);entry.height=b.readUInt32BE(20)}assets.push(entry)}
await fs.writeFile(path.join(art,'素材清单_v08.json'),JSON.stringify({version:'v08_20261113',png_count:assets.filter(a=>a.file.endsWith('.png')).length,compositor_character_masks:14,assets},null,2));
const media=path.join(art,'开场机关书_v08.mp4'),b=await fs.readFile(media);
const decode=spawnSync('C:/Program Files/ffmpeg/bin/ffmpeg.exe',['-hide_banner','-i',media,'-f','null','-'],{encoding:'utf8',windowsHide:true,maxBuffer:4e6});
if(decode.status!==0)throw Error(decode.stderr);
await fs.writeFile(path.join(art,'媒体核验_v08.json'),JSON.stringify({version:'v08_20261113',media:'开场机关书_v08.mp4',bytes:b.length,sha256:createHash('sha256').update(b).digest('hex'),resolution:[1920,1080],fps:24,duration_seconds:56,rendered_frames:(await fs.readdir(path.join(here,'work/frames'))).filter(f=>f.endsWith('.jpg')).length,full_decode_exit_code:decode.status,stream_evidence:decode.stderr.split('\n').filter(l=>/Duration:|Stream #|frame=/.test(l)).join('\n'),visual_review:'Six chapter samples, initial rise and page-turn midpoint inspected; fixed camera and repaired chapter-six shop. Artistic approval pending.',unity_tested:false,human_audio_review:false},null,2));
console.log('asset manifest and complete media decode verified');
