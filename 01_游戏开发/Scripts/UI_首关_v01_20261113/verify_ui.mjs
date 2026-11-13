/** Isolated local Chromium/CDP UI checks. No user browser profile or Unity is touched. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../../..');
const art=path.join(root,'01_游戏开发/Art/UI_首关_v01_20261113'),work=path.join(here,'work'),previews=path.join(art,'previews');
const report={version:'v01_20261113',test:'isolated_local_browser_ui_preview',started_at:new Date().toISOString(),unity_tested:false,checks:[],screenshots:[],limitations:['This checks a UI state simulator, not 3D movement or Unity integration.','Audio is checked for browser playback and volume state, not human listening.','Browser fullscreen and preview canvas resolution do not validate Unity window resolution.']};
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function exists(p){try{await fs.access(p);return true}catch{return false}}
async function until(fn,label,ms=15000){const t=Date.now();while(Date.now()-t<ms){if(await fn())return;await delay(80)}throw Error('Timed out '+label)}
function check(name,pass,evidence=null){report.checks.push({name,pass:Boolean(pass),evidence});console.log(name,pass?'PASS':'FAIL')}
class CDP{
 constructor(ws){this.ws=ws;this.next=1;this.pending=new Map();this.handlers=new Map();ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=this.pending.get(m.id);if(!p)return;clearTimeout(p.timer);this.pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result||{});}else for(const cb of this.handlers.get(m.method)||[])cb(m.params);});}
 static async connect(url){const ws=new WebSocket(url);await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true})});return new CDP(ws)}
 on(name,cb){const list=this.handlers.get(name)||[];list.push(cb);this.handlers.set(name,list)}
 send(method,params={}){const id=this.next++;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{this.pending.delete(id);reject(Error('CDP timeout '+method))},15000);this.pending.set(id,{resolve,reject,timer});this.ws.send(JSON.stringify({id,method,params}));})}
 async evaluate(expression){const r=await this.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result?.value}
 close(){this.ws.close()}
}
let browser,bc,page,exited=false,log='';const errors=[];
try{
 await fs.mkdir(work,{recursive:true});await fs.mkdir(previews,{recursive:true});
 for(const name of ['index.html','style.css','app.js'])report[name+'_sha256']=crypto.createHash('sha256').update(await fs.readFile(path.join(art,name))).digest('hex');
 const candidates=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'];let exe;for(const p of candidates)if(await exists(p)){exe=p;break}if(!exe)throw Error('No installed browser');
 const profile=path.join(work,`qa-profile-${Date.now()}`);await fs.mkdir(profile,{recursive:true});
 browser=spawn(exe,['--headless=new','--remote-debugging-port=0',`--user-data-dir=${profile}`,`--disk-cache-dir=${profile}/Cache`,`--crash-dumps-dir=${profile}/CrashDumps`,'--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-sync','--disable-extensions','--metrics-recording-only','--window-size=1920,1080','about:blank'],{windowsHide:true,cwd:here,stdio:['ignore','pipe','pipe']});
 browser.stdout.on('data',b=>log=(log+b.toString()).slice(-30000));browser.stderr.on('data',b=>log=(log+b.toString()).slice(-30000));browser.on('exit',()=>exited=true);
 const portFile=path.join(profile,'DevToolsActivePort');await until(()=>exists(portFile),'browser start');const lines=(await fs.readFile(portFile,'utf8')).trim().split(/\r?\n/),port=Number(lines[0]);
 bc=await CDP.connect(`ws://127.0.0.1:${port}${lines[1]}`);report.browser=await bc.send('Browser.getVersion');
 const {targetId}=await bc.send('Target.createTarget',{url:'about:blank'});const targets=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();page=await CDP.connect(targets.find(t=>t.id===targetId).webSocketDebuggerUrl);
 await page.send('Page.enable');await page.send('Runtime.enable');await page.send('Page.bringToFront');page.on('Runtime.exceptionThrown',e=>errors.push(e.exceptionDetails.exception?.description||e.exceptionDetails.text));
 await page.send('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
 await page.send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__events=[];window.addEventListener('jiaozi-ui',e=>__events.push(e.detail));`});
 const url=pathToFileURL(path.join(art,'index.html')).href;await page.send('Page.navigate',{url});
 await until(()=>page.evaluate(`document.readyState==='complete'&&!!window.uiPreview`),'UI ready');
 const state=()=>page.evaluate('uiPreview.getState()'), saved=()=>page.evaluate('uiPreview.getSaved()');
 async function waitImages(){await until(()=>page.evaluate(`[...document.images].every(i=>i.complete)`),'images');await delay(350)}
 async function click(selector){const p=await page.evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing '+${JSON.stringify(selector)});e.scrollIntoView({block:'center',inline:'center'});const r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);await page.send('Input.dispatchMouseEvent',{type:'mouseMoved',...p});await page.send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...p});await page.send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...p});await delay(70)}
 async function key(key,code,modifiers=0){await page.send('Input.dispatchKeyEvent',{type:'keyDown',key,code,modifiers,windowsVirtualKeyCode:({Enter:13,Escape:27,Tab:9,ArrowRight:39,ArrowLeft:37,F:70,f:70,'/':191})[key]||0});await page.send('Input.dispatchKeyEvent',{type:'keyUp',key,code,modifiers});await delay(60)}
 async function shot(name){await waitImages();await until(()=>page.evaluate(`!document.querySelector('#toast').classList.contains('visible')`),'transient toast clears for presentation');await delay(180);await page.evaluate('window.scrollTo(0,0)');const d=await page.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});const p=path.join(previews,name+'.png');await fs.writeFile(p,Buffer.from(d.data,'base64'));report.screenshots.push({file:'previews/'+name+'.png',sha256:crypto.createHash('sha256').update(Buffer.from(d.data,'base64')).digest('hex')});}
 async function screen(name){await page.evaluate(`uiPreview.navigate(${JSON.stringify(name)})`);await waitImages();}
 await shot('01_标题_1920x1080');
 check('initial_title_and_local_assets',await page.evaluate(`uiPreview.getState().screen==='title'&&[...document.images].every(i=>i.naturalWidth>0)`));
 await click('[data-action="level"]');check('title_to_level', (await state()).screen==='level');await shot('02_关卡_1920x1080');
 await click('[data-action="select"]');check('selection_start_requires_both',await page.evaluate(`document.querySelector('[data-action="start"]').disabled`));
 await key('ArrowLeft','ArrowLeft');await key('f','KeyF');await key('/','Slash');check('conflict_blocks_confirm_and_start',(await state()).ready.every(v=>!v)&&await page.evaluate(`document.querySelector('[data-action="start"]').disabled`),await state());
 await key('ArrowRight','ArrowRight');await key('f','KeyF');await key('/','Slash');check('independent_keyboard_confirm', (await state()).ready.every(Boolean));
 await shot('03_双人选角_1920x1080');await click('[data-action="start"]');
 let s=await state();await delay(350);check('tutorial_stops_clock_and_no_collection',s.screen==='game'&&s.tutorial&&(await state()).time===180&&!(await saved()).unlocked);
 await page.evaluate(`uiPreview.setCarry(0,'red');uiPreview.setDrySlot(0,1)`);await key('Enter','Enter');s=await state();check('skip_tutorial_clears_transient',!s.tutorial&&s.time>179&&s.score===0&&s.carry.every(x=>x==='empty')&&s.dry.every(x=>x===null),s);
 await page.evaluate(`uiPreview.setRemaining(138);uiPreview.setCarry(0,'dry');uiPreview.setCarry(1,'black');uiPreview.setDrySlot(0,1.7);uiPreview.setDrySlot(1,2.6)`);await shot('04_局内HUD_1920x1080');
 check('hud_player_panels_at_bottom_corners',await page.evaluate(`(()=>{const a=[...document.querySelectorAll('.player-hud')].map(e=>e.getBoundingClientRect());return a.length===2&&a.every(r=>r.top>innerHeight*.7)&&a[0].left<innerWidth*.1&&a[1].right>innerWidth*.9})()`));
 check('navigation_clears_previous_screen_feedback',await page.evaluate(`!document.querySelector('#toast').classList.contains('visible')`));
 await key('Escape','Escape');const frozen=await state();await delay(450);s=await state();check('pause_freezes_round_and_both_dry_slots',s.modal==='pause'&&s.time===frozen.time&&JSON.stringify(s.dry)===JSON.stringify(frozen.dry),{before:frozen,after:s});await shot('05_暂停_1920x1080');
 const focusItems=await page.evaluate(`[...document.querySelectorAll('#overlay button')].map(x=>x.dataset.action)`);await key('Tab','Tab',8);check('modal_focus_wraps_backward',await page.evaluate(`document.activeElement.dataset.action==='ask-exit'`),focusItems);await key('Tab','Tab');check('modal_focus_wraps_forward',await page.evaluate(`document.activeElement.dataset.action==='resume'`));
 await click('#overlay [data-action="settings"]');await shot('06_设置_1920x1080');const oldSetting=(await saved()).settings.master;
 await page.evaluate(`(()=>{const e=document.querySelector('#setting-master');e.value=23;e.dispatchEvent(new Event('input',{bubbles:true}));})()`);await click('[data-action="cancel-settings"]');check('settings_cancel_restores_saved_and_returns_pause',(await saved()).settings.master===oldSetting&&(await state()).modal==='pause');
 await click('#overlay [data-action="settings"]');await page.evaluate(`(()=>{const e=document.querySelector('#setting-master');e.value=64;e.dispatchEvent(new Event('input',{bubbles:true}));})()`);await click('[data-action="save-settings"]');check('settings_save_persists',(await saved()).settings.master===64&&(await state()).modal==='pause');
 await click('#overlay [data-action="settings"]');await click('[data-action="help"]');check('settings_help_returns_to_settings',(await state()).modal==='help');await click('[data-action="close-help"]');check('help_back_preserves_settings_page',(await state()).modal==='settings');
 await click('[data-action="listen"]');await delay(350);const audio=await page.evaluate(`(()=>{const a=document.querySelector('#music');return {paused:a.paused,volume:a.volume,ready:a.readyState,time:a.currentTime,error:a.error?.code}})()`);check('audio_preview_plays',!audio.paused&&audio.time>0&&audio.volume>0,audio);await click('[data-action="listen"]');
 await click('[data-action="fullscreen"]');await delay(250);const fullscreen=await page.evaluate('!!document.fullscreenElement');check('browser_fullscreen_enters',fullscreen);if(fullscreen){await click('[data-action="fullscreen"]');await delay(200)}
 await click('[data-action="cancel-settings"]');await click('[data-action="resume"]');await delay(150);check('resume_advances_time_and_drying',(await state()).time<frozen.time);
 await page.evaluate('uiPreview.begin(false)');for(let i=0;i<3;i++)await page.evaluate('uiPreview.deliver()');s=await state();check('three_sheets_two_orders_50',s.delivered===3&&s.orders===2&&s.score===50&&s.target===2&&s.received===1,s);await page.evaluate('uiPreview.deliver()');s=await state();check('single_order_1_1_2_four_sheets_70',s.delivered===4&&s.orders===3&&s.score===70&&s.target===1&&s.received===0,s);
 const rejected=await page.evaluate(`(()=>{uiPreview.setRemaining(0);const before=uiPreview.getState().score;const accepted=uiPreview.deliver();return {accepted,before,after:uiPreview.getState().score}})()`);check('time_zero_blocks_new_delivery',rejected.accepted===false&&rejected.after===rejected.before,rejected);
 await page.evaluate('uiPreview.setRemaining(.1)');await delay(300);s=await state();check('time_zero_settles_once',s.screen==='result'&&s.settlementCount===1&&s.ended,s);await page.evaluate('uiPreview.settle();uiPreview.settle()');check('settle_guard_is_idempotent',(await state()).settlementCount===1);
 check('formal_delivery_unlocks_and_records',(await saved()).unlocked&&(await saved()).bestScore===70&&(await saved()).bestStars===1,await saved());await shot('07_结算_1920x1080');
 await click('[data-action="collection"]');await shot('08_交子收藏_1920x1080');check('collection_has_one_unordered_pair',await page.evaluate(`document.querySelector('.section-head').textContent.includes('1 / 1')`));
 await page.send('Page.reload');await until(()=>page.evaluate(`document.readyState==='complete'&&!!window.uiPreview`),'reload');check('reload_restores_saved',(await saved()).unlocked&&(await saved()).bestScore===70&&(await saved()).settings.master===64,await saved());
 await page.evaluate(`uiPreview.begin(false);uiPreview.setCarry(0,'red');uiPreview.setDrySlot(0,1);uiPreview.deliver()`);await key('Escape','Escape');await click('[data-action="ask-restart"]');await click('[data-action="confirm"]');s=await state();check('restart_clears_transient_keeps_saved',s.score===0&&s.orders===0&&s.carry.every(x=>x==='empty')&&s.dry.every(x=>x===null)&&(await saved()).bestScore===70&&(await saved()).unlocked,s);
 // Reset only the isolated test profile, then prove tutorial and aborted rounds do not unlock.
 await page.evaluate(`localStorage.removeItem('jiaozi-ui-v01')`);await page.send('Page.reload');await until(()=>page.evaluate(`document.readyState==='complete'&&!!window.uiPreview`),'clean reload');await page.evaluate('uiPreview.begin(true);uiPreview.deliver()');check('tutorial_delivery_not_collected',(await state()).score===0&&!(await saved()).unlocked);
 await page.evaluate('uiPreview.deliver()');await key('Escape','Escape');await click('[data-action="ask-exit"]');await click('[data-action="confirm"]');check('abort_after_delivery_not_collected',(await state()).screen==='level'&&!(await saved()).unlocked);
 await page.evaluate('uiPreview.begin(false);uiPreview.deliver();uiPreview.settle()');check('zero_star_delivery_still_collects',(await saved()).unlocked&&(await saved()).bestStars===0,await saved());
 await page.evaluate(`uiPreview.begin(false);for(let i=0;i<8;i++)uiPreview.deliver();uiPreview.settle()`);check('six_orders_awards_three_stars',(await state()).orders===6&&(await saved()).bestStars===3,await saved());
 await page.evaluate(`Storage.prototype.__qaOriginalSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new DOMException('Quota','QuotaExceededError')};uiPreview.begin(false);uiPreview.deliver();uiPreview.settle();Storage.prototype.setItem=Storage.prototype.__qaOriginalSetItem;delete Storage.prototype.__qaOriginalSetItem;`);
 check('storage_failure_is_visible_and_keeps_session',await page.evaluate(`document.querySelector('#toast').textContent.includes('保存失败')&&document.querySelector('#toast').classList.contains('visible')&&uiPreview.getState().score===20`));
 for(const [width,height] of [[1920,1080],[1280,720],[1280,800],[390,844]]){
  await page.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
  for(const name of ['title','level','select','game','result','collection']){
   await screen(name);const layout=await page.evaluate(`(()=>{const bad=[...document.images].filter(i=>!i.naturalWidth).map(i=>i.getAttribute('src'));return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,bodyWidth:document.body.scrollWidth,brokenImages:bad,buttons:[...document.querySelectorAll('#stage button')].map(e=>{const r=e.getBoundingClientRect();return {label:e.textContent.trim()||e.getAttribute('aria-label'),x:r.x,y:r.y,w:r.width,h:r.height}})}})()`);
   check(`${width}x${height}/${name}/no_horizontal_overflow`,layout.scrollWidth<=width+1&&layout.bodyWidth<=width+1,layout);check(`${width}x${height}/${name}/no_broken_images`,layout.brokenImages.length===0,layout.brokenImages);
   if(width>=1280)check(`${width}x${height}/${name}/controls_in_screen`,layout.buttons.every(b=>b.x>=-1&&b.x+b.w<=width+1&&b.y>=-1&&b.y+b.h<=height+1),layout.buttons);
   if(width===390&&(name==='title'||name==='game'))await shot(`移动预览_${name}_390x844`);
  }
 }
 await page.send('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});await screen('title');
 check('no_uncaught_runtime_errors',errors.length===0,errors);
 // Snapshot evidence must correspond to the exact final frontend inputs.
 for(const name of ['index.html','style.css','app.js']){const hash=crypto.createHash('sha256').update(await fs.readFile(path.join(art,name))).digest('hex');check(name+'_unchanged_during_run',hash===report[name+'_sha256'],hash)}
 report.status=report.checks.every(c=>c.pass)?'passed':'failed';
}catch(e){report.status='failed';report.error=e.stack||e.message;console.log(report.error);if(page){try{const d=await page.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await fs.writeFile(path.join(work,'failed.png'),Buffer.from(d.data,'base64'));}catch{}}process.exitCode=1;}
finally{if(bc)try{await bc.send('Browser.close')}catch{}for(let i=0;browser&&!exited&&i<20;i++)await delay(100);if(browser&&!exited)browser.kill();page?.close();bc?.close();report.finished_at=new Date().toISOString();report.passed=report.checks.filter(c=>c.pass).length;report.total=report.checks.length;report.runtime_errors=errors;await fs.writeFile(path.join(work,'browser.log'),log);await fs.writeFile(path.join(art,'核验报告_v01_20261113.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({status:report.status,passed:report.passed,total:report.total,failed:report.checks.filter(c=>!c.pass).map(c=>c.name)}));if(report.status!=='passed')process.exitCode=1;}
