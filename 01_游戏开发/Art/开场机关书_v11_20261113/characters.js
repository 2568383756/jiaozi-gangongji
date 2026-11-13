/* F01 v11: adopted paper puppets. Chroma keying and articulated compositing keep the supplied drawings intact.
   The twelve source poses come from the user's two adopted atlases; no old scene face is used. */
(function(){
 const W=1672,H=941, sprites={},rigs={},props={};let images,base5,occlusionEnabled=true;const contacts=[];
 const C=(w=512,h=512)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c};
 const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x)},lerp=(a,b,t)=>a+(b-a)*t;
 const pulse=(t,a,b,c,d)=>ease((t-a)/(b-a))*(1-ease((t-c)/(d-c)));
 function poly(g,p){g.beginPath();p.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath()}
 function key(source,sx,sy,sw,sh){
  const c=C(sw,sh),g=c.getContext('2d',{willReadFrequently:true});g.drawImage(source,sx,sy,sw,sh,0,0,sw,sh);
  const d=g.getImageData(0,0,sw,sh),p=d.data;
  for(let z=0;z<p.length;z+=4){const spill=Math.min(p[z],p[z+2])-p[z+1];
   if(p[z]>80&&p[z+2]>80&&spill>22){const a=1-clamp((spill-22)/145);p[z+3]=Math.round(a*255);if(a>.05&&a<1){p[z]=Math.max(0,Math.min(255,(p[z]-(1-a)*255)/a));p[z+2]=Math.max(0,Math.min(p[z+1]+12,(p[z+2]-(1-a)*255)/a));}}
  }
  g.putImageData(d,0,0);return c;
 }
 const load=file=>new Promise((resolve,reject)=>{const im=new Image;im.onload=()=>resolve(im);im.onerror=()=>reject(Error('Missing adopted atlas '+file));im.src='assets/'+file});
 function part(source,p){const c=C(),g=c.getContext('2d');poly(g,p);g.clip();g.drawImage(source,0,0);return c}
 const rect=(x,y,w,h)=>[[x,y],[x+w,y],[x+w,y+h],[x,y+h]];
 const armR=[[318,247],[354,251],[383,242],[405,246],[435,258],[440,277],[420,290],[378,294],[376,313],[347,316],[319,302]];
 const armL=[[196,248],[160,253],[140,242],[113,246],[88,256],[84,278],[104,292],[140,293],[145,316],[173,322],[197,304]];
 const configs={
 h0:{head:[105,0,315,258],neck:[275,252],arm:armR,pivot:[335,276]},
 h1:{head:[69,0,370,256],neck:[258,250],arm:armL,pivot:[179,277]},
 h2:{head:[80,0,355,256],neck:[264,252]},
 h3:{head:[70,0,375,244],neck:[254,240]},
 h4:{head:[78,0,350,245],neck:[265,241]},
 h5:{head:[60,0,375,247],neck:[265,243],arm:armR,pivot:[335,276]},
 n0:{head:[105,0,300,263],neck:[281,250]},
 n1:{head:[60,0,350,261],neck:[264,250],arm:[[310,239],[348,243],[365,229],[395,220],[423,228],[438,244],[436,259],[419,272],[363,280],[348,315],[315,310]],pivot:[326,269]},
 n2:{head:[128,0,285,252],neck:[280,249],arm:[[167,247],[130,236],[111,223],[98,228],[103,240],[77,235],[52,245],[50,262],[72,277],[117,280],[126,312],[163,319]],pivot:[164,268]},
 n3:{head:[90,0,350,238],neck:[276,234],arm:[[208,229],[174,228],[158,222],[130,229],[116,242],[116,258],[151,270],[166,300],[190,319],[211,299]],pivot:[206,258]},
 n4:{head:[75,0,320,244],neck:[273,239],arm:[[321,229],[357,231],[384,215],[407,220],[409,229],[433,229],[445,244],[439,263],[407,272],[379,273],[364,301],[334,307]],pivot:[332,253]},
 n5:{head:[125,0,275,249],neck:[276,241],arm:[[172,234],[131,234],[110,223],[92,224],[94,236],[69,237],[48,247],[52,266],[71,277],[117,278],[127,310],[160,318]],pivot:[165,262]}
 };
 const palms={h0:[407,276],h1:[111,276],h5:[378,266],n1:[393,252],n2:[94,258],n3:[149,248],n4:[402,248],n5:[91,250]};
 function bounceOf(s,o={}){return (1-Math.cos((o.phase||0)*2))*.5*3.5*s*clamp(o.walk||0)}
 function handPoint(id,x,y,s,o={}){
  const palm=palms[id],cfg=configs[id],a=o.arm||0,ca=Math.cos(a),sa=Math.sin(a),dx=palm[0]-cfg.pivot[0],dy=palm[1]-cfg.pivot[1];
  let px=(cfg.pivot[0]+dx*ca-dy*sa-256)*s*(o.flip?-1:1),py=(cfg.pivot[1]+dx*sa+dy*ca-490)*s;
  const l=o.lean||0;return {x:x+px*Math.cos(l)-py*Math.sin(l),y:y-bounceOf(s,o)+px*Math.sin(l)+py*Math.cos(l)};
 }
 function carryPoint(a,b,amount,offsetA,offsetB,label){const p={x:lerp(a.x+offsetA[0],b.x+offsetB[0],amount),y:lerp(a.y+offsetA[1],b.y+offsetB[1],amount)};contacts.push({label,amount,sourceHand:a,targetHand:b,object:p,sourceOffset:offsetA,targetOffset:offsetB});return p}
 function rig(id,source){
  const cfg=configs[id],headRect=rect(...cfg.head),head=part(source,headRect),body=C(),bg=body.getContext('2d');bg.drawImage(source,0,0);
  const parts=[{name:'head',shape:headRect,c:head,pivot:cfg.neck}];
  if(cfg.arm){const c=part(source,cfg.arm);parts.push({name:'arm',shape:cfg.arm,c,pivot:cfg.pivot});const hg=head.getContext('2d');hg.globalCompositeOperation='destination-out';poly(hg,cfg.arm);hg.fill();hg.globalCompositeOperation='source-over'}
  // Feet pivot at the ankles. Robes and shorts remain attached to the torso.
  // A per-pose split keeps one shoe wholly inside one part (the old x=270 cut split NPC shoes).
  const feet={h0:[420,274,226,319],h1:[420,255,211,306],h2:[420,250,202,306],h3:[420,270,227,318],h4:[420,274,228,320],h5:[420,253,207,302],n0:[426,280,238,330],n1:[425,248,194,293],n2:[433,238,183,290],n3:[444,300,248,352],n4:[449,250,198,308],n5:[430,245,192,297]};
  const [footY,split,lx,rx]=feet[id];
  for(let s=0;s<2;s++){const shape=rect(s?split:90,footY,s?440-split:split-90,512-footY);parts.push({name:s?'footR':'footL',shape,c:part(source,shape),pivot:[s?rx:lx,footY+4]})}
  bg.globalCompositeOperation='destination-out';for(const p of parts){poly(bg,p.shape);bg.fill()}bg.globalCompositeOperation='source-over';
  rigs[id]={body,parts};sprites[id]=source;
 }
 function paint(g,id,x,y,s,o={}){
  const r=rigs[id],walk=o.walk||0,phase=o.phase||0;
  g.imageSmoothingQuality='high';
  const bounce=bounceOf(s,o);
  g.save();g.translate(x,y-bounce);g.rotate(o.lean||0);g.scale(o.flip?-s:s,s);g.translate(-256,-490);
  // Layer the paper hinges with torso overlaps; no duplicate original arms remain.
  for(const p of r.parts.filter(p=>p.name.startsWith('foot'))){const step=phase+(p.name==='footR'?Math.PI:0),lift=Math.max(0,Math.sin(step))*5*walk;g.save();g.translate(0,bounce/s-lift);g.translate(...p.pivot);g.rotate(Math.sin(step)*walk*.14);g.translate(-p.pivot[0],-p.pivot[1]);g.drawImage(p.c,0,0);g.restore();g.save();g.beginPath();g.arc(p.pivot[0],p.pivot[1],16,0,Math.PI*2);g.clip();g.drawImage(sprites[id],0,0);g.restore()}
  g.drawImage(r.body,0,0);
  for(const p of r.parts.filter(p=>!p.name.startsWith('foot'))){
   let a=p.name==='head'?(o.nod||0):(o.arm||0);
   g.save();g.translate(...p.pivot);g.rotate(a);g.translate(-p.pivot[0],-p.pivot[1]);g.drawImage(p.c,0,0);g.restore();
   if(p.name==='arm'){g.save();g.beginPath();g.arc(p.pivot[0],p.pivot[1],15,0,Math.PI*2);g.clip();g.drawImage(sprites[id],0,0);g.restore()}
  }g.restore();
 }
 function prop(g,id,x,y,w,h,a=0,flip=false){g.save();g.translate(x,y);g.rotate(a);if(flip)g.scale(-1,1);g.drawImage(props[id],-w/2,-h/2,w,h);g.restore()}
 function patch(g,img,x,y,w,h){if(occlusionEnabled)g.drawImage(img,x,y,w,h,x,y,w,h)}
 function sheet(g,x,y,w=100,h=55,angle=0,ink=0,red=0){
  g.save();g.translate(x,y);g.rotate(angle);g.shadowColor='rgba(71,39,16,.18)';g.shadowBlur=3;g.shadowOffsetY=2;
  g.fillStyle='#f7e2b7';g.strokeStyle='#fff3d5';g.lineWidth=2;g.beginPath();g.moveTo(-w/2,-h/2);g.lineTo(w/2,-h/2+1);g.lineTo(w/2-2,h/2);g.lineTo(-w/2+1,h/2-1);g.closePath();g.fill();g.stroke();g.shadowColor='transparent';
  if(ink>0){g.save();g.globalAlpha=ink;g.strokeStyle='#674c32';g.lineWidth=Math.max(1,w/85);g.strokeRect(-w/2+5,-h/2+5,w-10,h-10);g.filter='grayscale(1) sepia(1) brightness(.78)';g.drawImage(sprites.h0,100,20,320,240,-w*.38,-h*.32,w*.34,h*.58);g.drawImage(sprites.h1,70,20,375,240,w*.04,-h*.32,w*.34,h*.58);g.restore()}
  if(red>0){g.globalAlpha=red;g.strokeStyle='#a33321';g.lineWidth=2;g.strokeRect(w*.28,-h*.3,w*.1,w*.1);g.beginPath();g.moveTo(w*.3,-h*.24);g.lineTo(w*.35,-h*.24);g.lineTo(w*.35,-h*.18);g.stroke();g.globalAlpha=1}
  g.restore();
 }
 function shadow(g,x,y,w,a=.13){g.save();g.fillStyle='rgba(90,48,20,'+a+')';g.beginPath();g.ellipse(x,y,w,8,0,0,Math.PI*2);g.fill();g.restore()}
 const meta={spriteCount:12,partCount:68,adoptedPaths:['assets/heroes_adopted.png','assets/npcs_adopted.png','assets/props_adopted.png'],stampTimes:[42],
 chapterActions:['负重行走、扁担与钱筐摆动、推车滚轮','掌柜与商人抬臂递券、点头','官吏递券、商人伸手与点头','包裹交接、买家接物退步','单纸传递、女孩走向印台与盖印台、印章抬起压落','女孩递票、买家接票后退、男孩招手']};
 async function init(args){
  images=args.images;
  const [h,n,p,clean]=await Promise.all([load('heroes_adopted.png'),load('npcs_adopted.png'),load('props_adopted.png'),load('clean05_no_stamp_v01.png')]);
  base5=C(W,H);base5.getContext('2d').drawImage(clean,0,0,W,H);
  for(let i=0;i<6;i++){rig('h'+i,key(h,(i%3)*512,Math.floor(i/3)*512,512,512));rig('n'+i,key(n,(i%3)*512,Math.floor(i/3)*512,512,512))}
  const boxes={cash:[45,75,307,275],cart:[31,405,341,280],parcel:[1114,75,283,280],stamp:[423,729,237,304],brush:[728,723,311,318]};
  for(const [k,b] of Object.entries(boxes))props[k]=key(p,...b);
  // Extract the exact front wheel for a clean rolling layer, not a vector substitute.
  props.wheel=key(p,174,564,104,106);
  window.CharacterMotion.meta.partCount=Object.values(rigs).reduce((n,r)=>n+r.parts.length+1,0);
 }
 function draw(g,i,t,options={}){
  occlusionEnabled=options.occlusion!==false;contacts.length=0;
  if(options.background!==false)g.drawImage(i===4?base5:images['c'+i],0,0);
  if(i===0){
   const travel=108*ease((t-.7)/4.5),walk=pulse(t,.65,1.1,5.0,5.2),phase=travel/7.5,bob=-bounceOf(.72,{walk,phase});
   const x=635+travel,y=755;
   shadow(g,x,y,110);
   // The pole runs behind the raised hands; both baskets follow the same paper hinge.
   g.save();g.translate(travel,bob);g.strokeStyle='#fff0ce';g.lineWidth=17;g.lineCap='round';g.beginPath();g.moveTo(451,599);g.lineTo(830,599);g.stroke();g.strokeStyle='#9b5a23';g.lineWidth=11;g.stroke();
   for(const bx of [465,816]){const sway=Math.sin(t*4+(bx>600?.45:0))*.09*walk;g.save();g.translate(bx,599);g.rotate(sway);g.strokeStyle='#8e5d2f';g.lineWidth=3;g.beginPath();g.moveTo(-7,0);g.lineTo(-40,80);g.moveTo(7,0);g.lineTo(40,80);g.stroke();prop(g,'cash',0,108,115,104);g.restore()}g.restore();
   paint(g,'n0',x,y,.72,{walk,phase,nod:.035*Math.sin(t*2),lean:.012*Math.sin(t*2.5)*walk});
   const tx=1028+travel,ty=747;
   shadow(g,tx,ty,90);paint(g,'n4',tx,ty,.7,{walk,phase:phase+1,nod:-.04,arm:-.12,lean:.025*walk});
   CartMotion.draw(g,1295,625,travel);
  }else if(i===1){
   const reach=pulse(t,1,2.1,4.1,5.3),nod=pulse(t,3.4,3.7,4,4.5);
   const so={arm:reach*.24,nod:-nod*.08,lean:-reach*.018},bo={arm:-reach*.26,nod:nod*.075,lean:reach*.025,walk:pulse(t,1,1.2,1.9,2.1)+pulse(t,4.1,4.3,5.1,5.3),phase:reach*8.7};
   paint(g,'n2',1050-reach*16,786,.84,so);
   patch(g,images.c1,803,601,508,190);patch(g,images.c1,1137,450,140,148);
   paint(g,'n1',658+reach*65,793,.85,bo);
   const take=ease((t-2.6)/1.1),p=carryPoint(handPoint('n2',1050-reach*16,786,.84,so),handPoint('n1',658+reach*65,793,.85,bo),take,[-30,-10],[32,-10],'private_receipt');sheet(g,p.x,p.y,99,47,-.04+reach*.08);
  }else if(i===2){
   const reach=pulse(t,1.1,2.2,3.8,5.2),nod=pulse(t,3.4,3.8,4.15,4.5);
   const so={arm:reach*.21,nod:-nod*.075,lean:-reach*.015},bo={arm:-reach*.25,nod:nod*.08,lean:reach*.025,walk:pulse(t,1.1,1.3,2,2.2)+pulse(t,3.8,4,5,5.2),phase:reach*7.2};
   paint(g,'n3',948-reach*12,787,.79,so);
   patch(g,images.c2,691,667,492,146);
   paint(g,'n1',598+reach*54,819,.76,bo);
   const take=ease((t-2.7)/1),p=carryPoint(handPoint('n3',948-reach*12,787,.79,so),handPoint('n1',598+reach*54,819,.76,bo),take,[-29,18],[27,-14],'official_receipt');sheet(g,p.x,p.y,81,43,-.04+take*.08);
  }else if(i===3){
   const reach=pulse(t,1.1,2.1,3.9,4.7),accept=ease((t-3.1)/1.2),step=68*ease((t-4.2)/1.1);
   paint(g,'n4',1285,634,.43,{arm:-.07+Math.sin(t*2)*.06,nod:.02*Math.sin(t*1.3)});
   patch(g,images.c3,1090,585,408,126);
   const so={flip:true,arm:reach*.17,nod:.03*Math.sin(t*1.4)},bo={arm:reach*.29,nod:-.07*accept,lean:-reach*.025,walk:pulse(t,4.2,4.35,5.1,5.3),phase:step/7};
   paint(g,'n2',675,795,.77,so);
   patch(g,images.c3,301,646,551,166);
   paint(g,'n5',1044+step-reach*18,796,.8,bo);
   const p=carryPoint(handPoint('n2',675,795,.77,so),handPoint('n5',1044+step-reach*18,796,.8,bo),accept,[29,-10],[-26,-11],'cloth_parcel');prop(g,'parcel',p.x,p.y,86,86,-.03+accept*.07);
  }else if(i===4){
   const together=pulse(t,.9,2.2,3.8,5.2),pass=ease((t-2)/2.2);
   const toPrint=ease((t-5.0)/1.6),toSeal=ease((t-8.4)/.8),home=ease((t-11.2)/1.0);
   let gx=lerp(938-together*69,1107,toPrint),gy=lerp(797,514,toPrint),gs=lerp(.78,.48,toPrint);
   gx=lerp(gx,1298,toSeal);gy=lerp(gy,573,toSeal);gx=lerp(gx,935,home);gy=lerp(gy,797,home);gs=lerp(gs,.78,home);
   const moving=pulse(t,5,5.15,6.4,6.6)+pulse(t,8.4,8.5,9.05,9.2)+pulse(t,11.2,11.35,12.05,12.2);
   const follow=pulse(t,5.1,7,10.8,12.3),bx=570+together*65+follow*120,by=798-follow*52;
   const bo={arm:-together*.16-.22*follow,nod:.04*Math.sin(t*1.6),lean:.02*follow,walk:pulse(t,5.1,5.3,6.8,7)+pulse(t,10.8,11,12.1,12.3),phase:(together*65+follow*120)/8};
   const grip=pulse(t,9.1,9.35,10.55,11),lift=22*pulse(t,9.35,9.65,9.75,10)+12*pulse(t,10.06,10.3,10.55,10.8);
   const go={arm:together*.10+grip*.9-.14*pulse(t,7,7.3,7.65,8),nod:-pulse(t,7,7.4,7.7,8.1)*.075,walk:moving,phase:toPrint*18+toSeal*12+home*24};
   gy-=lift;shadow(g,bx,by,100);paint(g,'h0',bx,by,.78-follow*.06,bo);
   if(t>11)prop(g,'stamp',1243,474,69,88);
   // One continuous pose is used through walking, printing and stamping: no face/robe swap.
   if(t<6.5||t>11.2)shadow(g,gx,gy+3,70*gs/.78,.10);
   paint(g,'h1',gx,gy,gs,go);
   const boyHand=handPoint('h0',bx,by,.78-follow*.06,bo),girlHand=handPoint('h1',gx,gy,gs,go);
   const carried={x:girlHand.x+45*gs/.78,y:girlHand.y+12*gs/.78};
   let p=t<5?carryPoint(boyHand,girlHand,pass,[32,12],[45*gs/.78,12*gs/.78],'workshop_handoff'):carried;
   let px=p.x,py=p.y,pw=lerp(lerp(150,98,toPrint),150,home),ph=lerp(lerp(58,40,toPrint),58,home);
   const atPrint=ease((t-6.3)/.4)*(1-ease((t-8.15)/.25)),atSeal=ease((t-9.0)/.2)*(1-ease((t-10.9)/.3));
   px=lerp(px,1074,atPrint);py=lerp(py,428,atPrint);px=lerp(px,1234,atSeal);py=lerp(py,496,atSeal);
   const ink=ease((t-7.1)/.7),red=ease((t-10)/.15);
   if(t>=6.5&&t<8.5)patch(g,base5,970,438,236,90);
   if(t>=9.05&&t<=11.2)patch(g,base5,1154,508,177,88);
   sheet(g,px,py,pw,ph,.035*Math.sin(t*.8),ink,red);
   // Only one stamp: a lift, decisive press at local 10.0, and return.
   const stampX=lerp(1243,girlHand.x,grip),stampY=lerp(474,girlHand.y+29,grip);
   if(t<=11)prop(g,'stamp',stampX,stampY,69,88,-.025*pulse(t,9.3,9.6,9.75,10));
   contacts.push({label:'stamp_grip',amount:grip,hand:girlHand,object:{x:stampX,y:stampY},handleOffset:[0,-29],pressTime:10});
   // Drying-rack empty capacity stays two slots; no additional loose order sheets are spawned.
  }else{
   const extend=pulse(t,1.1,2.4,3.7,4.8),accept=ease((t-3.2)/1.0),retreat=80*ease((t-4.7)/1.1),greet=pulse(t,4.1,4.5,6.3,7.1);
   g.save();g.beginPath();g.rect(831,0,610,648);g.clip();
   const go={arm:-extend*.20+greet*(-.18+.055*Math.sin(t*4+1)),nod:.05*pulse(t,3.5,3.8,4,4.4),lean:extend*.018},bo={arm:extend*.22,nod:-.065*accept,walk:pulse(t,4.7,4.85,5.65,5.8),phase:retreat/7.5};
   paint(g,'h0',946+greet*24,775,.68,{arm:greet*(-.24+.075*Math.sin(t*4)),nod:.045*Math.sin(t*1.1),lean:greet*.025});
   paint(g,'h5',1187+extend*18,778,.72,go);
   g.restore();
   // Solid counter masks the lower bodies; foreground customer remains unmasked.
   patch(g,images.c5,831,648,610,153);
   paint(g,'n5',1460+retreat,830-retreat*.16,.81-retreat*.0007,bo);
   const p=carryPoint(handPoint('h5',1187+extend*18,778,.72,go),handPoint('n5',1460+retreat,830-retreat*.16,.81-retreat*.0007,bo),accept,[38,5],[0,-7],'final_jiaozi');
   sheet(g,p.x,p.y,102,57,-.035+accept*.05,1,1);
  }
 }
 meta.movementRanges={chapter1_travel_px:108,previous_chapter1_px:38,chapter2_approach_px:65,chapter3_approach_px:54,chapter4_retreat_px:68,chapter5_boy_follow_px:120,chapter6_retreat_px:80,foot_swing_radians:.14,body_bounce_source_px:3.5,bounce_scales_with_character:true};
 meta.polish={handAnchoredTransfers:5,continuousWorkshopPose:'h1',stampHeldBySameHand:true,occlusionOption:true,gait:'distance-driven phases, gradual start/stop, supporting foot counters torso bounce'};
 window.CharacterMotion={init,draw,paint,handPoint,meta,debug:{sprites,rigs,props,contacts}};
})();
