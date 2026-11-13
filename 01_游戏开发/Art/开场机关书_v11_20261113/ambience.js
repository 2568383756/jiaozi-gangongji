/* F01 v11: paper leaf cutout trajectories and water-only clipped ripples.
   All coordinates are in the unchanged 1672 x 941 source plane. */
(function(){
 let images,leaf;const W=1672,H=941;
 const waterRegions={0:[[[1070,805],[1134,779],[1238,776],[1209,796],[1286,830],[1319,848],[1170,847],[1157,834]],[[843,594],[899,596],[917,616],[965,628],[944,647],[848,668],[829,666],[894,641],[931,632],[897,621],[850,613]],[[936,454],[967,453],[1003,467],[997,486],[1029,497],[1074,518],[1082,532],[1049,549],[1022,548],[1058,528],[1024,511],[991,498],[975,478]]],3:[[[967,397],[1023,397],[1068,402],[1099,417],[1114,435],[1053,433],[1009,418],[968,420]]],4:[[[171,639],[425,639],[436,679],[160,679]],[[271,492],[313,500],[343,512],[340,530],[310,550],[260,566],[218,579],[190,598],[154,598],[175,577],[214,560],[261,548],[302,528],[294,511],[268,507]],[[995,834],[1086,805],[1141,781],[1203,783],[1227,804],[1266,817],[1390,835]]],5:[]};
 const waterCenterlines={0:[[[1230,782],[1163,795],[1116,810],[1191,832],[1285,847]],[[855,600],[899,607],[917,622],[945,633],[894,652],[840,667]],[[948,457],[985,470],[988,486],[1031,510],[1062,528],[1037,545]]],3:[[[978,404],[1014,409],[1056,420],[1096,429]]],4:[null,[[278,499],[320,516],[314,534],[264,557],[216,574],[167,594]],[[1190,788],[1140,805],[1137,819],[1174,832],[1264,840]]]},waterArcs={};
 const meta={leafSource:'assets/clean01.png, top ginkgo fan; runtime polygon cutout',leafCounts:[6,2,2,6,7,6],leafLayers:{back:[4,1,1,4,5,4],front:[2,1,1,2,2,2]},waterRegions,waterCenterlines,waterChapters:[1,4,5],waterMethod:'Arc-length sampled river paths with moving cream paper streaks; three staggered expanding vat ripples; strict river/vat clipping',leafMotion:'Depth-separated curved descent, wind drift, softened ground settling; front leaves confined to left/right margins',chapterTypes:[['cloud','pedestrians','leaves','river','lantern'],['leaves','lantern','curtain'],['leaves','lantern'],['cloud','pedestrians','leaves','river','lantern'],['cloud','leaves','river','vat ripples','lantern'],['cloud','pedestrian','leaves','lantern']]};
 const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
 function trace(g,p){g.beginPath();p.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath()}
 function makeArc(points){
  const samples=[],dist=[0];let total=0;
  for(let n=0;n<points.length-1;n++)for(let j=0;j<20;j++){
   const u=j/20,p0=points[Math.max(0,n-1)],p1=points[n],p2=points[n+1],p3=points[Math.min(points.length-1,n+2)];
   const v=[0,1].map(k=>.5*((2*p1[k])+(-p0[k]+p2[k])*u+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*u*u+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*u*u*u));
   if(samples.length){const prev=samples[samples.length-1];total+=Math.hypot(v[0]-prev[0],v[1]-prev[1]);dist.push(total)}samples.push(v);
  }
  const last=points[points.length-1],prev=samples[samples.length-1];total+=Math.hypot(last[0]-prev[0],last[1]-prev[1]);samples.push(last);dist.push(total);return {samples,dist,total};
 }
 function arcPoint(arc,f,offset=0){const wanted=clamp(f)*arc.total;let n=1;while(n<arc.dist.length-1&&arc.dist[n]<wanted)n++;const p=arc.samples[n-1],q=arc.samples[n],u=(wanted-arc.dist[n-1])/(arc.dist[n]-arc.dist[n-1]||1),dx=q[0]-p[0],dy=q[1]-p[1],len=Math.hypot(dx,dy)||1;return [p[0]+dx*u-dy/len*offset,p[1]+dy*u+dx/len*offset]}
 async function init(args){images=args.images;leaf=document.createElement('canvas');leaf.width=92;leaf.height=85;const g=leaf.getContext('2d');g.translate(-419,-3);trace(g,[[456,78],[449,68],[434,52],[427,39],[431,26],[442,16],[454,12],[467,9],[484,14],[494,21],[501,36],[489,49],[470,64],[460,81]]);g.clip();g.drawImage(images.c0,0,0);for(const [chapter,lines] of Object.entries(waterCenterlines))waterArcs[chapter]=lines.map(p=>p?makeArc(p):null)}
 function drawWater(g,i,t){
  const regs=waterRegions[i]||[];regs.forEach((p,k)=>{g.save();trace(g,p);g.clip();
   g.strokeStyle='rgba(246,242,201,.72)';g.lineWidth=1.5;g.lineCap='round';
   if(i===4&&k===0){for(let n=0;n<3;n++){const f=((t*.24+n/3)%1);g.globalAlpha=Math.sin(f*Math.PI)*.65;g.beginPath();g.ellipse(295,657,16+f*127,2+f*23,0,0,Math.PI*2);g.stroke()}}
   else {const arc=waterArcs[i][k];for(let lane=0;lane<2;lane++)for(let n=0;n<4;n++){
    const f=((t*23/arc.total+n*.25+lane*.105)%1),tail=.10,offset=lane?5:-5;
    g.globalAlpha=smooth(f/.08)*smooth((1-f)/.1)*(.55+lane*.08);g.beginPath();
    for(let j=0;j<=8;j++){const v=arcPoint(arc,f-tail+j/8*tail,offset);if(j)g.lineTo(...v);else g.moveTo(...v)}g.stroke();
   }}
   g.restore();
  });
 }
 function drawLeaves(g,i,t,layer='all'){
  const count=meta.leafCounts[i],backCount=meta.leafLayers.back[i],dur=i===4?14:i===5?10:8;
  g.save();g.beginPath();g.rect(77,0,1520,840);g.clip();
  for(let n=0;n<count;n++){
   const front=n>=backCount;if(layer==='back'&&front||layer==='front'&&!front)continue;
   const edgeChapter=i===1||i===2,frontIndex=n-backCount;
   const start=front?(.6+frontIndex*(dur>10?5.4:1.4)):n*(dur>10?1.25:dur===10?.8:.55)-.45,life=edgeChapter?5.4:front?5.7:5.1+(n%3)*.45;
   const f=clamp((t-start)/life),settle=smooth((f-.82)/.18),travel=1-Math.pow(1-f,1.18);
   const right=front&&frontIndex%2===1;
   const sx=edgeChapter?(front?1480:140):front?(right?1490:170):225+(n%3)*180,sy=edgeChapter?545:front?(right?710:370):125+(n%3)*70;
   const ex=edgeChapter?(front?1370:285):front?(right?1400:240):370+(n%4)*195,ey=front?824:755+(n%3)*25;
   const sway=Math.sin(f*Math.PI*3+n)*28*Math.sin(f*Math.PI),x=sx+(ex-sx)*travel+sway,y=sy+(ey-sy)*travel;
   const size=edgeChapter?.21:front?.32:.19+(n%3)*.035,fold=.55+.45*Math.abs(Math.cos(f*7+n)),angle=(n%2?1:-1)*(.1+travel*3.6);
   g.save();g.globalAlpha=smooth((t-start)/.35)*(i<5?1-smooth((t-(dur-2.5))/.5):1);
   g.translate(x,y);g.rotate(angle);g.scale(size,size*(fold*(1-settle)+.34*settle));
   g.shadowColor='rgba(132,74,22,.15)';g.shadowBlur=3;g.shadowOffsetY=4;g.drawImage(leaf,-46,-42);g.restore();
  }g.restore();
 }
 function drawUnder(g,i,t){drawWater(g,i,t);drawLeaves(g,i,t,'back')}
 function drawOver(g,i,t){drawLeaves(g,i,t,'front')}
 window.Ambience={init,drawUnder,drawOver,drawWater,drawLeaves,meta};
})();
