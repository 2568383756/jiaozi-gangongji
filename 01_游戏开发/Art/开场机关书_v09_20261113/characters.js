/* F01 v09: adopted paper puppets. Chroma keying and articulated compositing keep the supplied drawings intact.
   The twelve source poses come from the user's two adopted atlases; no old scene face is used. */
(function(){
 const W=1672,H=941, sprites={},rigs={},props={};let images,base5;
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
 function rig(id,source){
  const cfg=configs[id],headRect=rect(...cfg.head),head=part(source,headRect),body=C(),bg=body.getContext('2d');bg.drawImage(source,0,0);
  const parts=[{name:'head',shape:headRect,c:head,pivot:cfg.neck}];
  if(cfg.arm){const c=part(source,cfg.arm);parts.push({name:'arm',shape:cfg.arm,c,pivot:cfg.pivot});const hg=head.getContext('2d');hg.globalCompositeOperation='destination-out';poly(hg,cfg.arm);hg.fill();hg.globalCompositeOperation='source-over'}
  // Feet pivot at the ankles. Robes and shorts remain attached to the torso.
  const footY=id==='n3'?444:420;
  for(let s=0;s<2;s++){const shape=rect(s?270:145,footY,s?150:125,92);parts.push({name:s?'footR':'footL',shape,c:part(source,shape),pivot:[s?320:225,footY+4]})}
  bg.globalCompositeOperation='destination-out';for(const p of parts){poly(bg,p.shape);bg.fill()}bg.globalCompositeOperation='source-over';
  rigs[id]={body,parts};sprites[id]=source;
 }
 function paint(g,id,x,y,s,o={}){
  const r=rigs[id],walk=o.walk||0,phase=o.phase||0;
  const bounce=walk?Math.abs(Math.sin(phase))*3:0;
  g.save();g.translate(x,y-bounce);g.scale(o.flip?-s:s,s);g.translate(-256,-490);
  // Layer the paper hinges with torso overlaps; no duplicate original arms remain.
  for(const p of r.parts.filter(p=>p.name.startsWith('foot'))){g.save();g.translate(...p.pivot);g.rotate((p.name==='footR'?1:-1)*Math.sin(phase)*walk*.12);g.translate(-p.pivot[0],-p.pivot[1]);g.drawImage(p.c,0,0);g.restore()}
  g.drawImage(r.body,0,0);
  for(const p of r.parts.filter(p=>!p.name.startsWith('foot'))){
   let a=p.name==='head'?(o.nod||0):(o.arm||0);
   g.save();g.translate(...p.pivot);g.rotate(a);g.translate(-p.pivot[0],-p.pivot[1]);g.drawImage(p.c,0,0);g.restore();
   if(p.name==='arm'){g.save();g.beginPath();g.arc(p.pivot[0],p.pivot[1],15,0,Math.PI*2);g.clip();g.drawImage(sprites[id],0,0);g.restore()}
  }g.restore();
 }
 function prop(g,id,x,y,w,h,a=0,flip=false){g.save();g.translate(x,y);g.rotate(a);if(flip)g.scale(-1,1);g.drawImage(props[id],-w/2,-h/2,w,h);g.restore()}
 function patch(g,img,x,y,w,h){g.drawImage(img,x,y,w,h,x,y,w,h)}
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
  if(options.background!==false)g.drawImage(i===4?base5:images['c'+i],0,0);
  if(i===0){
   const travel=38*ease((t-.7)/4.5),walk=pulse(t,.65,1.1,5.2,5.7),bob=Math.sin(t*5)*3*walk;
   const x=635+travel,y=755;
   shadow(g,x,y,110);
   // The pole runs behind the raised hands; both baskets follow the same paper hinge.
   g.save();g.translate(travel,bob);g.strokeStyle='#fff0ce';g.lineWidth=17;g.lineCap='round';g.beginPath();g.moveTo(451,599);g.lineTo(830,599);g.stroke();g.strokeStyle='#9b5a23';g.lineWidth=11;g.stroke();
   for(const bx of [465,816]){const sway=Math.sin(t*4+(bx>600?.45:0))*.035*walk;g.save();g.translate(bx,599);g.rotate(sway);g.strokeStyle='#8e5d2f';g.lineWidth=3;g.beginPath();g.moveTo(-7,0);g.lineTo(-40,80);g.moveTo(7,0);g.lineTo(40,80);g.stroke();prop(g,'cash',0,108,115,104);g.restore()}g.restore();
   paint(g,'n0',x,y,.72,{walk,phase:t*5,nod:.025*Math.sin(t*2)});
   const tx=1028+travel,ty=747;
   shadow(g,tx,ty,90);paint(g,'n4',tx,ty,.7,{walk,phase:t*5+1,nod:-.035,arm:-.06});
   prop(g,'cart',1295+travel,625,320,263,0,true);
   // Wheel center coordinates match the mirrored cart sprite.
   for(const wx of [1278,1382])prop(g,'wheel',wx+travel,699,97,98,-travel/45,true);
  }else if(i===1){
   const reach=pulse(t,1,2.1,4.1,5.3),nod=pulse(t,3.4,3.7,4,4.5);
   paint(g,'n2',1050,786,.84,{arm:reach*.18,nod:-nod*.07});
   patch(g,images.c1,803,601,508,190);patch(g,images.c1,1137,450,140,148);
   paint(g,'n1',690+reach*14,793,.85,{arm:-reach*.18,nod:nod*.065});
   sheet(g,886-reach*27,574-reach*14,99,47,-.04+reach*.08);
  }else if(i===2){
   const reach=pulse(t,1.1,2.2,3.8,5.2),nod=pulse(t,3.4,3.8,4.15,4.5);
   paint(g,'n3',948,787,.79,{arm:reach*.22,nod:-nod*.065});
   patch(g,images.c2,691,667,492,146);
   paint(g,'n1',623+reach*8,819,.76,{arm:-reach*.22,nod:nod*.07});
   sheet(g,801-reach*26,628-reach*8,81,43,-.04);
  }else if(i===3){
   const reach=pulse(t,1.1,2.1,3.9,4.7),accept=ease((t-3.1)/1.2),step=22*ease((t-4.2)/1.1);
   paint(g,'n4',1285,634,.43,{arm:-.07+Math.sin(t*2)*.06,nod:.02*Math.sin(t*1.3)});
   patch(g,images.c3,1090,585,408,126);
   paint(g,'n2',675,795,.77,{flip:true,arm:reach*.17,nod:.035*Math.sin(t*1.4)});
   patch(g,images.c3,301,646,551,166);
   paint(g,'n5',1044+step,796,.8,{arm:reach*.18,nod:-.05*accept,walk:step>0&&step<21?1:0,phase:t*5});
   prop(g,'parcel',844+accept*41+step,603-reach*10,86,86,-.03+accept*.05);
  }else if(i===4){
   const together=pulse(t,.9,2.2,3.8,5.2),pass=ease((t-2)/2.2);
   const toPrint=ease((t-5.0)/1.6),toSeal=ease((t-8.4)/.8),home=ease((t-11.2)/1.0);
   let gx=lerp(938-together*69,1107,toPrint),gy=lerp(797,514,toPrint),gs=lerp(.78,.48,toPrint);
   gx=lerp(gx,1278,toSeal);gy=lerp(gy,573,toSeal);gx=lerp(gx,935,home);gy=lerp(gy,797,home);gs=lerp(gs,.78,home);
   const moving=(t>5&&t<6.6)||(t>8.4&&t<9.2)||(t>11.2&&t<12.2);
   shadow(g,570+together*65,798,100);paint(g,'h0',570+together*65,798,.78,{arm:-together*.13,nod:.045*Math.sin(t*1.6)});
   paint(g,t>6.5&&t<11.3?'h3':'h1',gx,gy,gs,{arm:together*.13,nod:-pulse(t,7,7.4,7.7,8.1)*.1,walk:moving?1:0,phase:t*6});
   let px=lerp(688,858,pass),py=644-together*8,pw=150,ph=58;
   px=lerp(px,1074,toPrint);py=lerp(py,428,toPrint);pw=lerp(pw,98,toPrint);ph=lerp(ph,40,toPrint);
   px=lerp(px,1234,toSeal);py=lerp(py,496,toSeal);
   px=lerp(px,856,home);py=lerp(py,644,home);pw=lerp(pw,150,home);ph=lerp(ph,58,home);
   const ink=ease((t-7.1)/.7),red=ease((t-10)/.15);
   if(toPrint>.5&&home<.3){patch(g,base5,970,438,236,90);patch(g,base5,1154,508,177,88)}
   sheet(g,px,py,pw,ph,.035*Math.sin(t*.8),ink,red);
   // Only one stamp: a lift, decisive press at local 10.0, and return.
   const lift=38*pulse(t,9.25,9.65,9.75,10.0)+24*pulse(t,10.06,10.3,10.6,10.95);
   prop(g,'stamp',1243,474-lift,69,88,-.04*pulse(t,9.3,9.6,9.75,10));
   // Drying-rack empty capacity stays two slots; no additional loose order sheets are spawned.
  }else{
   const extend=pulse(t,1.1,2.4,3.7,4.8),accept=ease((t-3.2)/1.0),retreat=48*ease((t-4.7)/1.1);
   g.save();g.beginPath();g.rect(831,0,610,648);g.clip();
   paint(g,'h0',946,775,.68,{arm:-.22*pulse(t,4.2,4.6,5.2,5.8),nod:.04*Math.sin(t*1.1)});
   paint(g,'h5',1187,778,.72,{arm:-extend*.19,nod:.04*pulse(t,3.5,3.8,4,4.4)});
   g.restore();
   // Solid counter masks the lower bodies; foreground customer remains unmasked.
   patch(g,images.c5,831,648,610,153);
   paint(g,'n5',1460+retreat,830,.81,{arm:extend*.19,nod:-.055*accept,walk:retreat>0&&retreat<47?1:0,phase:t*5});
   sheet(g,1321+accept*32+retreat,626-extend*13,102,57,-.045+accept*.065,1,1);
  }
 }
 window.CharacterMotion={init,draw,meta,debug:{sprites,rigs,props}};
})();
