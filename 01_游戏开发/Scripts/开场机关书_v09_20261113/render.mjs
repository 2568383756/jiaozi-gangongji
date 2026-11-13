import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),art=path.resolve(here,'../../Art/开场机关书_v09_20261113'),work=path.join(here,'work');
await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
class CDP{
 constructor(ws){this.ws=ws;this.n=1;this.p=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=this.p.get(m.id);if(!p)return;this.p.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}}}
 static async open(url){const ws=new WebSocket(url);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});return new CDP(ws)}
 send(method,params={}){const id=this.n++;return new Promise((resolve,reject)=>{this.p.set(id,{resolve,reject});this.ws.send(JSON.stringify({id,method,params}))})}
 async eval(expression){const r=await this.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value}
}
const profile=path.join(work,'profile-'+Date.now());
const proc=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--remote-debugging-port=0','--allow-file-access-from-files','--autoplay-policy=no-user-gesture-required','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-extensions','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
let browser,page;
try{
 let port;
 for(let n=0;n<100;n++){try{port=(await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).trim().split(/\r?\n/);break}catch{await delay(100)}}
 if(!port)throw Error('Chrome did not launch');
 browser=await CDP.open('ws://127.0.0.1:'+port[0]+port[1]);
 const {targetId}=await browser.send('Target.createTarget',{url:'about:blank'});
 const targets=await(await fetch('http://127.0.0.1:'+port[0]+'/json/list')).json();
 page=await CDP.open(targets.find(t=>t.id===targetId).webSocketDebuggerUrl);
 await page.send('Page.enable');
 await page.send('Page.navigate',{url:pathToFileURL(path.join(art,'分层动画源.html')).href});
 for(let n=0;n<150;n++){if(await page.eval('window.loaded===true'))break;await delay(100)}
 if(!await page.eval('window.loaded===true'))throw Error('Assets not loaded');
 await page.eval('document.fonts.ready');
 const shot=async(t,file)=>{const data=await page.eval('renderFrame('+t+');document.querySelector("canvas").toDataURL("image/jpeg",.96).split(",")[1]');await fs.writeFile(file,Buffer.from(data,'base64'))};
 if(process.argv.includes('--preview')){
  for(const t of [0.4,1.5,3,4.5,6.3,6.8,7.2,7.6,7.98,8.02,8.5,11,12.5,19,20.5,27,28.5,34,36,38,40,42,44,47.5,49,51,53.5,55.9])await shot(t,path.join(work,'preview_'+t+'.jpg'));
  console.log('Preview frames saved',work);
 }else if(process.argv.includes('--motion-qa')){
  const result=await page.eval(`(()=>{
   const canvas=document.querySelector('canvas'),g=canvas.getContext('2d');
   const regions=[[430,350,970,480],[540,320,700,500],[470,390,620,450],[540,370,870,450],[400,350,720,490],[840,320,770,540]];
   const checks=regions.map((r,i)=>{
    const x=Math.round(60+r[0]*1800/1672),y=Math.round(12+r[1]*1800/1672),w=Math.round(r[2]*1800/1672),h=Math.round(r[3]*1800/1672);
    renderFrame(INTRO.starts[i]+2);const a=g.getImageData(x,y,w,h).data;
    renderFrame(INTRO.starts[i]+4.5);const b=g.getImageData(x,y,w,h).data;let changed=0,magenta=0;
    for(let k=0;k<a.length;k+=4){if(Math.abs(a[k]-b[k])+Math.abs(a[k+1]-b[k+1])+Math.abs(a[k+2]-b[k+2])>45)changed++;if(b[k]>170&&b[k+2]>170&&b[k+1]<65)magenta++}
    return {chapter:i+1,changedPixels:changed,changedFraction:changed/(w*h),magentaPixels:magenta,passed:changed/(w*h)>.003&&magenta===0};
   });
   let spineError=0,minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
   for(let f=0;f<=100;f++){
    const rows=PageTurn.surface(f/100);
    rows.forEach((row,j)=>{spineError=Math.max(spineError,Math.abs(row[0].x-827),Math.abs(row[0].y-(468+393*j/(rows.length-1))));row.forEach(p=>{minX=Math.min(minX,p.x);maxX=Math.max(maxX,p.x);minY=Math.min(minY,p.y);maxY=Math.max(maxY,p.y)})});
   }
   const pageGeometry={samples:101,spineError,minX,maxX,minY,maxY,passed:spineError<.01&&minX>=0&&maxX<=1672&&minY>=0&&maxY<=941};
   return {version:'v09_20261113',fontLoaded:window.introFontLoaded===true,fontCheck:document.fonts.check('34px IntroKai'),characterAssets:CharacterMotion.meta,pageGeometry,checks};
  })()`);
  await fs.writeFile(path.join(art,'动作与字体核验_v09.json'),JSON.stringify(result,null,2));
  if(!result.fontLoaded||!result.fontCheck||!result.pageGeometry.passed||result.checks.some(c=>!c.passed))throw Error(JSON.stringify(result));
  console.log(result);
 }else if(process.argv.includes('--qa')){
  await page.send('Page.navigate',{url:pathToFileURL(path.join(art,'播放开场.html')).href});
  await delay(1200);
  const checks=[];
  const check=async(name,exp)=>{const value=await page.eval(exp);checks.push({name,value,passed:!!value});if(!value)throw Error(name)};
  await check('video_metadata','v.readyState>=1 && v.videoWidth===1920 && v.videoHeight===1080 && Math.abs(v.duration-56)<.1');
  await page.eval('window.events=[];window.addEventListener("intro-finished",e=>events.push(e.detail));start()');
  await delay(1200);await check('playback_advances','v.currentTime>.5 && !v.paused');
  await page.eval('v.pause();window.pt=v.currentTime');await delay(500);await check('pause_freezes','Math.abs(v.currentTime-pt)<.03');
  await page.eval('finish("skipped");finish("skipped")');await check('skip_fires_once','events.length===1 && events[0].reason==="skipped"');
  await page.eval('start();v.currentTime=55.6');await delay(1400);
  await check('natural_end_after_replay','events.length===2 && events[1].reason==="ended"');
  await check('ended_stops_playback','v.ended && v.paused');
  await fs.writeFile(path.join(art,'播放器核验_v09.json'),JSON.stringify({version:'v09_20261113',checks,unity_integration_tested:false,audio_listened:false},null,2));
  console.log(checks);
 }else{
  const frames=path.join(work,'frames');await fs.mkdir(frames,{recursive:true});
  for(let i=0;i<56*24;i++){await shot(i/24,path.join(frames,String(i).padStart(5,'0')+'.jpg'));if(i%120===0)console.log('rendered',i,'/ 1344')}
  console.log('All 1344 frames rendered');
 }
}finally{page?.ws.close();try{await browser?.send('Browser.close')}catch{}browser?.ws.close();proc.kill()}
