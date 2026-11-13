/* F01 v10: paper leaf cutout trajectories and water-only clipped ripples.
   All coordinates are in the unchanged 1672 x 941 source plane. */
(function(){
 let images,leaf;const W=1672,H=941;
 const waterRegions={0:[[[1070,805],[1134,779],[1238,776],[1209,796],[1286,830],[1319,848],[1170,847],[1157,834]],[[843,594],[899,596],[917,616],[965,628],[944,647],[848,668],[829,666],[894,641],[931,632],[897,621],[850,613]],[[936,454],[967,453],[1003,467],[997,486],[1029,497],[1074,518],[1082,532],[1049,549],[1022,548],[1058,528],[1024,511],[991,498],[975,478]]],3:[[[967,397],[1023,397],[1068,402],[1099,417],[1114,435],[1053,433],[1009,418],[968,420]]],4:[[[171,639],[425,639],[436,679],[160,679]],[[271,492],[313,500],[343,512],[340,530],[310,550],[260,566],[218,579],[190,598],[154,598],[175,577],[214,560],[261,548],[302,528],[294,511],[268,507]],[[995,834],[1086,805],[1141,781],[1203,783],[1227,804],[1266,817],[1390,835]]],5:[]};
 const meta={leafSource:'assets/clean01.png, top ginkgo fan; runtime polygon cutout',leafCounts:[6,2,2,6,7,6],waterRegions,waterChapters:[1,4,5],waterMethod:'Moving cream paper strokes and widening vat ellipses, clipped to hand-checked river/vat polygons',leafMotion:'Curved descent, wind drift, rotation, folded foreshortening, then ground settling',chapterTypes:[['cloud','pedestrians','leaves','river','lantern'],['leaves','lantern','curtain'],['leaves','lantern'],['cloud','pedestrians','leaves','river','lantern'],['cloud','leaves','river','vat ripples','lantern'],['cloud','pedestrian','leaves','lantern']]};
 function trace(g,p){g.beginPath();p.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath()}
 async function init(args){images=args.images;leaf=document.createElement('canvas');leaf.width=92;leaf.height=85;const g=leaf.getContext('2d');g.translate(-419,-3);trace(g,[[456,78],[449,68],[434,52],[427,39],[431,26],[442,16],[454,12],[467,9],[484,14],[494,21],[501,36],[489,49],[470,64],[460,81]]);g.clip();g.drawImage(images.c0,0,0)}
 function drawUnder(g,i,t){
  const regs=waterRegions[i]||[];regs.forEach((p,k)=>{g.save();trace(g,p);g.clip();
   const xs=p.map(v=>v[0]),ys=p.map(v=>v[1]),left=Math.min(...xs),right=Math.max(...xs),top=Math.min(...ys),bottom=Math.max(...ys),height=bottom-top;
   g.strokeStyle='rgba(246,242,201,.66)';g.lineWidth=1.6;g.lineCap='round';
   if(i===4&&k===0){for(let n=0;n<4;n++){const f=((t*.28+n*.25)%1);g.globalAlpha=Math.sin(f*Math.PI)*.72;g.beginPath();g.ellipse(295,657,20+f*128,3+f*25,0,0,Math.PI*2);g.stroke()}}
   else for(let n=0;n<9;n++){const f=((n*.137+t*.12)%1),y=top+f*height,x=left+(right-left)*(.15+.7*((n*.317)%1));g.globalAlpha=Math.sin(f*Math.PI)*.83;g.beginPath();g.moveTo(x-12,y);g.bezierCurveTo(x-3,y-3,x+12,y+3,x+25,y+1);g.stroke()}
   g.restore();
  });
 }
 function drawOver(g,i,t){
  const count=meta.leafCounts[i],dur=i===4?14:i===5?10:8;
  g.save();g.beginPath();g.rect(77,0,1520,840);g.clip();
  for(let n=0;n<count;n++){
   const edgeChapter=i===1||i===2;
   const start=n*(dur>10?.95:dur===10?.6:.37)-.4,life=edgeChapter?5.6:5.8+(n%3)*.6;
   let f=Math.max(0,Math.min(1,(t-start)/life));
   const sx=edgeChapter?(n?1510:140):230+(n%3)*205,sy=edgeChapter?550:110+(n%3)*75;
   const ex=edgeChapter?(n?1400:285):390+(n%4)*300,ey=790+(n%2)*34;
   const sway=Math.sin(f*Math.PI*3+n)*34*Math.sin(f*Math.PI),x=sx+(ex-sx)*f+sway,y=sy+(ey-sy)*f;
   const size=edgeChapter?.21:.24+(n%3)*.05;
   g.save();g.globalAlpha=Math.min(1,Math.max(0,(t-start)*3))*(i<4?Math.max(0,Math.min(1,(dur-2.1-t)*3)):1);
   g.translate(x,y);g.rotate((n%2?1:-1)*(.1+f*4.3));g.scale(size,size*(f>=1?.34:.55+.45*Math.abs(Math.cos(f*8+n))));
   g.shadowColor='rgba(132,74,22,.15)';g.shadowBlur=3;g.shadowOffsetY=4;g.drawImage(leaf,-46,-42);g.restore();
  }g.restore();
 }
 window.Ambience={init,drawUnder,drawOver,meta};
})();
