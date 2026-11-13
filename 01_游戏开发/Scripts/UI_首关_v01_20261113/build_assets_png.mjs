/** Rasterize this original SVG kit with alpha in an owned headless browser.
 * No user browser/profile or remote service is used. Source bitmaps are copied
 * byte-for-byte by build_assets.py and never modified by this script.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import crypto from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../../..');
const out=path.join(root,'01_游戏开发/Art/UI_首关_v01_20261113/assets');
const work=path.join(here,'build_assets_work');
await fs.mkdir(work,{recursive:true});await fs.writeFile(path.join(work,'.gitignore'),'*\n');
const profile=await fs.mkdtemp(path.join(work,'browser-'));
let executable;
for(const p of ['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Microsoft/Edge/Application/msedge.exe']){
  try{await fs.access(p);executable=p;break}catch{}
}
if(!executable)throw Error('No local Chromium found');
const browser=spawn(executable,['--headless=new','--remote-debugging-port=0','--no-first-run','--no-default-browser-check','--disable-gpu','--disable-extensions',`--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore',windowsHide:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let socket;const pending=new Map();let seq=0;
function cdp(method,params={}){return new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));setTimeout(()=>{if(pending.has(id)){pending.delete(id);reject(Error('Timeout '+method))}},20000).unref()})}
try{
 let port;
 for(let i=0;i<100;i++){try{port=(await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break}catch{await delay(100)}}
 if(!port)throw Error('Browser did not start');
 const tabs=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
 socket=new WebSocket(tabs.find(x=>x.type==='page').webSocketDebuggerUrl);
 socket.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}});
 await new Promise((res,rej)=>{socket.addEventListener('open',res,{once:true});socket.addEventListener('error',rej,{once:true})});
 await cdp('Runtime.enable');
 const manifest=JSON.parse(await fs.readFile(path.join(out,'manifest.json'),'utf8'));
 const checks=[];
 for(const a of manifest.assets){
  const source=await fs.readFile(path.join(out,a.source),'utf8');
  const expression=`(async()=>{const s=${JSON.stringify(source)},w=${a.width},h=${a.height};const im=new Image();im.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(s);await im.decode();const c=document.createElement('canvas');c.width=w;c.height=h;const cx=c.getContext('2d');cx.drawImage(im,0,0,w,h);const rgba=cx.getImageData(0,0,w,h).data;let clear=0,solid=0;for(let i=3;i<rgba.length;i+=4){if(rgba[i]===0)clear++;if(rgba[i]===255)solid++}return {png:c.toDataURL('image/png').split(',')[1],clear,solid,width:w,height:h}})()`;
  const v=await cdp('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
  if(v.exceptionDetails)throw Error(JSON.stringify(v.exceptionDetails));
  const result=v.result.value;await fs.writeFile(path.join(out,a.file),Buffer.from(result.png,'base64'));
  a.sha256=crypto.createHash('sha256').update(await fs.readFile(path.join(out,a.file))).digest('hex');
  a.svg_sha256=crypto.createHash('sha256').update(source).digest('hex');
  a.raster_check={width:result.width,height:result.height,transparent_pixel_count:result.clear,opaque_pixel_count:result.solid};
  checks.push({id:a.id,pass:result.clear>0&&result.solid>0});
 }
 // Portraits are original Blender renders. Read-only alpha inspection.
 let portraits=[];
 try{portraits=JSON.parse(await fs.readFile(path.join(out,'portrait_sources.json'),'utf8'))}catch{}
 for(const p of portraits){
  const bytes=await fs.readFile(path.join(out,p.file));p.sha256=crypto.createHash('sha256').update(bytes).digest('hex');
  const expression=`(async()=>{const im=new Image();im.src='data:image/png;base64,${bytes.toString('base64')}';await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);const d=x.getImageData(0,0,c.width,c.height).data;let clear=0,solid=0;for(let i=3;i<d.length;i+=4){if(d[i]===0)clear++;if(d[i]===255)solid++}return {width:c.width,height:c.height,transparent_pixel_count:clear,opaque_pixel_count:solid}})()`;
  const r=await cdp('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});p.pixel_check=r.result.value;
  checks.push({id:p.file,pass:p.pixel_check.width===768&&p.pixel_check.height===768&&p.pixel_check.transparent_pixel_count>0&&p.pixel_check.opaque_pixel_count>0&&p.source_unmodified});
 }
 manifest.portrait_details=portraits;
 manifest.validation={checks,passed:checks.filter(x=>x.pass).length,total:checks.length,all_passed:checks.every(x=>x.pass),method:'Headless Chromium canvas rasterization and pixel inspection; source SVG and Blender renders unchanged.'};
 manifest.generated_png_count=manifest.assets.length+portraits.length;
 await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({sprites:manifest.assets.length,portraits:portraits.length,checks:manifest.validation.total,pass:manifest.validation.all_passed}));
}finally{if(socket?.readyState===1){try{await cdp('Browser.close')}catch{}socket.close()}browser.kill();}
