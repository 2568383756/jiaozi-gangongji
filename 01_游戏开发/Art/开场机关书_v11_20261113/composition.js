/* F01 v11. Fixed-camera 2.5D paper-book animation, adopted character atlas and curved leaves.
   No external dependencies. Coordinates refer to a normalized 1672 x 941 canvas.
   Polygon cutouts are editable compositor masks, not claimed as production sprites. */
const W=1672,H=941,DURATION=56;
const starts=[0,8,16,24,32,46], ends=[8,16,24,32,46,56];
const titles=["铁钱难行","纸券初生","官办交子","一纸通市","纸艺开工","合做交子"];
const lines=[
["北宋蜀地，街市买卖日渐兴旺。","沉重的铁钱，却让往来多有不便。"],
["商人把钱存进铺户，取回一纸凭券。","凭券取钱，也渐渐凭券做起了买卖。"],
["从民间的凭券，到官府发行的纸币。","益州交子务，开启了交子的新篇。"],
["一纸交子，让买卖少了搬钱的辛劳。","而在纸艺世界里，故事正等你们接续。"],
["抄出的纸等风晾干，再印上墨纹与朱印。","你们接力，赶出作坊的开张第一单。"],
["你们的模样，随第一张交子送进街巷。","交个纸友，一起开工，故事才刚开始。"]];
const polygons=[
[
[[565,744],[570,699],[471,689],[459,638],[480,611],[506,553],[502,538],[564,534],[568,507],[561,482],[581,446],[615,429],[645,434],[673,450],[703,454],[738,487],[752,532],[808,536],[820,551],[812,568],[839,615],[851,638],[840,687],[816,705],[745,705],[720,695],[716,722],[727,742],[678,751],[659,746],[645,708],[620,738],[605,750]],
[[947,691],[938,662],[938,625],[936,581],[954,550],[973,528],[969,490],[979,456],[1014,428],[1060,417],[1071,396],[1096,389],[1124,400],[1146,425],[1146,450],[1158,456],[1151,484],[1130,489],[1115,533],[1100,554],[1118,591],[1116,624],[1135,629],[1132,731],[1070,736],[1036,731],[1001,741],[963,735]]],
[
[[637,791],[618,780],[630,737],[620,697],[615,654],[609,615],[611,577],[634,546],[614,516],[594,478],[554,480],[554,457],[572,447],[576,415],[594,382],[627,363],[657,357],[690,372],[709,380],[748,394],[774,422],[790,464],[801,486],[822,491],[842,501],[841,522],[816,538],[798,547],[789,582],[790,638],[781,670],[776,717],[792,774],[772,790],[733,790],[718,778],[704,798]],
[[889,501],[894,484],[938,478],[965,475],[971,448],[981,406],[1007,379],[1056,354],[1091,341],[1124,351],[1140,370],[1138,393],[1126,405],[1148,424],[1153,449],[1143,477],[1127,502],[1145,521],[1156,548],[1136,574],[1090,577],[1062,563],[1012,561],[970,544],[935,528],[911,525]]],
[
[[539,822],[539,791],[548,761],[529,742],[531,705],[547,671],[574,636],[548,615],[527,583],[496,579],[490,544],[510,529],[507,508],[525,480],[554,463],[582,468],[596,478],[628,476],[666,490],[696,521],[710,561],[716,588],[698,621],[728,636],[751,631],[769,645],[753,661],[725,665],[725,694],[693,722],[686,765],[699,808],[688,821],[647,822],[626,806],[608,821]],
[[794,615],[813,602],[852,584],[847,548],[863,508],[875,478],[894,461],[911,428],[943,417],[984,424],[1019,438],[1023,466],[1014,508],[1047,555],[1035,589],[1015,575],[1005,603],[1003,632],[993,659],[951,670],[910,665],[874,663],[837,664],[815,651]]],
[
[[575,649],[585,625],[596,587],[612,564],[598,538],[589,505],[575,485],[575,461],[583,430],[608,406],[632,400],[656,420],[690,419],[725,435],[755,462],[773,499],[773,536],[748,563],[774,577],[801,577],[820,588],[824,606],[801,620],[772,621],[744,641],[699,645],[636,648]],
[[840,596],[857,583],[884,587],[908,574],[891,549],[883,522],[891,483],[914,452],[946,427],[985,416],[1016,402],[1043,396],[1073,414],[1086,441],[1080,458],[1106,479],[1107,508],[1095,530],[1075,553],[1045,563],[1028,590],[1035,630],[1042,662],[1073,724],[1046,738],[1049,768],[1056,788],[1038,800],[1003,800],[982,789],[960,798],[919,795],[903,784],[910,763],[918,733],[905,730],[906,678],[881,663],[866,626],[846,618]],
[[1217,584],[1221,557],[1234,531],[1227,505],[1217,480],[1225,451],[1238,442],[1241,420],[1259,405],[1285,411],[1293,425],[1322,433],[1347,453],[1355,483],[1344,512],[1327,531],[1358,549],[1360,566],[1341,578],[1305,566],[1279,567],[1265,588]]],
[
[[510,792],[511,761],[520,733],[510,715],[518,671],[538,627],[510,607],[472,642],[453,633],[460,600],[443,581],[465,564],[440,526],[432,486],[473,455],[493,412],[548,410],[591,397],[626,415],[645,448],[687,472],[699,509],[685,541],[679,555],[710,564],[702,595],[677,619],[683,634],[698,642],[695,661],[673,676],[654,682],[656,712],[651,743],[660,774],[650,791],[608,796],[592,788],[568,798],[529,799]],
[[751,615],[750,584],[761,553],[777,540],[770,527],[778,510],[799,492],[809,467],[840,445],[883,439],[918,451],[954,473],[981,506],[1004,541],[1031,549],[1042,573],[1020,588],[1022,622],[1003,646],[973,652],[982,688],[999,736],[972,749],[980,779],[967,798],[923,800],[905,790],[885,800],[846,800],[829,791],[832,765],[841,746],[814,733],[821,706],[811,701],[810,677],[824,662],[809,642],[796,632],[774,633]]],
[
[[914,643],[922,601],[910,574],[878,558],[878,537],[864,514],[877,492],[874,474],[868,451],[880,420],[900,402],[914,381],[950,372],[978,357],[1012,366],[1035,389],[1056,405],[1080,436],[1073,460],[1062,477],[1073,499],[1063,534],[1047,552],[1045,573],[1057,609],[1070,642]],
[[1066,643],[1080,605],[1097,573],[1081,561],[1068,539],[1078,518],[1086,491],[1102,459],[1136,426],[1174,400],[1202,393],[1234,402],[1262,426],[1281,461],[1283,488],[1299,505],[1288,530],[1289,550],[1272,567],[1246,575],[1221,583],[1236,594],[1248,603],[1242,621],[1225,626],[1200,612],[1181,644]],
[[1310,618],[1321,603],[1336,611],[1352,584],[1355,554],[1365,527],[1375,512],[1371,490],[1390,460],[1425,442],[1460,438],[1502,453],[1534,470],[1554,501],[1576,526],[1576,546],[1561,571],[1545,585],[1525,603],[1515,624],[1517,653],[1535,688],[1515,716],[1515,744],[1510,790],[1525,816],[1511,834],[1468,836],[1446,825],[1426,836],[1380,831],[1367,815],[1380,793],[1380,750],[1364,727],[1369,693],[1335,681],[1320,662],[1328,638],[1312,636]]]
];
const canvas=document.querySelector('canvas'), ctx=canvas.getContext('2d');
const make=()=>{let c=document.createElement('canvas');c.width=W;c.height=H;return c};
const stage=make(), sc=stage.getContext('2d');
const clamp=x=>Math.min(1,Math.max(0,x)), ease=x=>{x=clamp(x);return x*x*(3-2*x)};
function trace(g,pts){g.beginPath();pts.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath()}
const images={}, floorMasks=[], cloudWindows=[];
const foldScratch=make(), foldCtx=foldScratch.getContext('2d'), environmentFrame=make(), environmentCtx=environmentFrame.getContext('2d');
const movingMask=make(), movingMaskCtx=movingMask.getContext('2d');
// Complete cloud silhouettes retained as paper, despite their warm sky-like palette.
const cloudContours={
0:[[933,189],[1000,167],[1108,179],[1147,124],[1226,117],[1250,79],[1322,69],[1378,74],[1434,111],[1509,142],[1514,194],[1435,233],[1187,276],[933,273]],
3:[[921,174],[1078,135],[1216,113],[1230,67],[1305,52],[1383,74],[1436,110],[1491,139],[1482,193],[1402,211],[1290,239],[1151,257],[927,258]],
4:[[829,148],[846,117],[907,104],[942,106],[956,77],[997,65],[1014,43],[1060,42],[1097,61],[1107,79],[1144,77],[1174,97],[1209,109],[1188,128],[1128,144],[1085,156],[1035,163],[988,151],[948,154],[889,160]],
5:[[821,112],[832,85],[884,72],[934,67],[960,44],[994,32],[1031,36],[1051,61],[1090,67],[1125,87],[1132,104],[1094,111],[1040,122],[991,122],[945,113],[904,118],[859,115]]
};
const introFont = new FontFace('IntroKai', 'local("STKaiti"), local("华文楷体"), local("KaiTi")');
const fontReady = introFont.load().then(f=>{document.fonts.add(f);window.introFontLoaded=true}).catch(()=>{window.introFontLoaded=false});
function silhouette(source,i){
 const c=make(),g=c.getContext('2d');g.drawImage(source,0,0);
 const d=g.getImageData(0,0,W,H),p=d.data,visited=new Uint8Array(W*H),q=new Int32Array(W*H);let head=0,tail=0;
 const push=n=>{if(n<0||n>=W*835||visited[n])return;visited[n]=1;const z=n*4,r=p[z],gg=p[z+1],b=p[z+2];if(r>210&&gg>160&&b>125&&r-gg<65&&gg-b<55){q[tail++]=n;p[z+3]=0}};
 for(let x=0;x<W;x++)push(x);for(let y=0;y<835;y++){push(y*W);push(y*W+W-1)}
 while(head<tail){const n=q[head++];if(n%W)push(n-1);if(n%W<W-1)push(n+1);push(n-W);push(n+W)}
 // Preserve light awnings, gables and cream paper interiors underneath each
 // established skyline. They can share the sky colour but belong to the card.
 // Three consecutive non-sky pixels reject isolated paper-grain noise.
 for(let x=0;x<W;x++){let run=0,top=400;for(let y=0;y<400;y++){const z=(y*W+x)*4,r=p[z],gg=p[z+1],b=p[z+2];const sky=r>210&&gg>160&&b>125&&r-gg<65&&gg-b<55;run=sky?0:run+1;if(run>=3){top=y-2;break}}for(let y=top;y<400;y++)p[(y*W+x)*4+3]=255}
 for(let y=400;y<H;y++)for(let x=0;x<W;x++){
  const left=119-(y-400)*.195,right=1550+(y-400)*.195;
  p[(y*W+x)*4+3]=(y<835&&x>left&&x<right)?255:0;
 }
 g.putImageData(d,0,0);
 // Clouds use the same warm palette as the backdrop. Their enclosed mask must
 // be restored explicitly, otherwise background keying leaves only a thin curl.
 const cloud=cloudContours[i];
 if(cloud){
  const cm=make(),cg=cm.getContext('2d');trace(cg,cloud);cg.fillStyle='#fff';cg.fill();const cd=cg.getImageData(0,0,W,H).data,src=source.getContext('2d').getImageData(0,0,W,H).data,restored=g.getImageData(0,0,W,H);
  for(let z=0;z<src.length;z+=4)if(cd[z+3]&&src[z+1]-src[z+2]>26){restored.data[z]=src[z];restored.data[z+1]=src[z+1];restored.data[z+2]=src[z+2];restored.data[z+3]=255}
  g.putImageData(restored,0,0);
 }
 g.globalCompositeOperation='destination-in';const edge=g.createLinearGradient(0,790,0,840);edge.addColorStop(0,'#fff');edge.addColorStop(1,'rgba(255,255,255,0)');g.fillStyle=edge;g.fillRect(0,0,W,H);g.globalCompositeOperation='source-over';
 return c;
}
function prepareFolds(i){
 floorMasks[i]=silhouette(window.EnvironmentMotion.backgrounds[i]||images['c'+i],i);
 const cloud=cloudContours[i];if(!cloud)return;
 // A small search window follows the original cloud region with room for the
 // environment's 18 px drift. It is not an opaque rectangle in the final mask.
 const cm=make(),cg=cm.getContext('2d');trace(cg,cloud);cg.fillStyle=cg.strokeStyle='#fff';cg.lineWidth=48;cg.lineJoin='round';cg.fill();cg.stroke();
 const x=Math.max(0,Math.floor(Math.min(...cloud.map(p=>p[0]))-24)),y=Math.max(0,Math.floor(Math.min(...cloud.map(p=>p[1]))-24));
 const w=Math.min(W-x,Math.ceil(Math.max(...cloud.map(p=>p[0]))+24)-x),h=Math.min(H-y,Math.ceil(Math.max(...cloud.map(p=>p[1]))+24)-y);
 cloudWindows[i]={x,y,w,h,alpha:cg.getImageData(x,y,w,h).data};
}
function currentFoldMask(i){
 const region=cloudWindows[i];if(!region)return floorMasks[i];
 movingMaskCtx.clearRect(0,0,W,H);movingMaskCtx.drawImage(floorMasks[i],0,0);
 const {x,y,w,h,alpha}=region,src=environmentCtx.getImageData(x,y,w,h).data,d=movingMaskCtx.getImageData(x,y,w,h),p=d.data;
 // Refill only current cream paper pixels. Retain the quiet backdrop outside
 // their contour and use a soft colour threshold for the cloud's pale rim.
 for(let z=0;z<src.length;z+=4){if(!alpha[z+3]||src[z]<210||src[z+1]<160||src[z+2]<125)continue;const keep=alpha[z+3]*clamp((src[z+1]-src[z+2]-22)/5);p[z+3]=Math.max(p[z+3],keep)}
 movingMaskCtx.putImageData(d,x,y);return movingMask;
}
const load=(key,file)=>new Promise((ok,fail)=>{let im=new Image;im.onload=()=>{let c=make();c.getContext('2d').drawImage(im,0,0,W,H);images[key]=c;ok()};im.onerror=fail;im.src='assets/'+file});
window.ready=Promise.all([fontReady,load('ground','ground.png'),load('blank','blank.png'),...starts.flatMap((_,i)=>[load('s'+i,'scene0'+(i+1)+'.png'),load('c'+i,i===5?'clean06_perspective_v02.png':i===4?'clean05_no_stamp_v01.png':'clean0'+(i+1)+'.png')])]).then(async()=>{
 await Promise.all([window.EnvironmentMotion.init({images,make,trace}),window.Ambience.init({images,make,trace}),window.CharacterMotion.init({images,polygons,make,trace}),window.CartMotion.init()]);
 for(let i=0;i<6;i++)prepareFolds(i);
 renderFrame(0);window.loaded=true;
});
function buildScene(i,t){
 sc.clearRect(0,0,W,H);
 window.EnvironmentMotion.drawBackground(sc,i,t);
 window.Ambience.drawUnder(sc,i,t);
 window.CharacterMotion.draw(sc,i,t,{background:false});
 window.Ambience.drawOver(sc,i,t);
}
function composeBook(i,t,dur){
 // Close the standees first; the leaf then turns with its spine fixed.
 const closing=i<5?ease((t-(dur-2.35))/.6):0;
 const opening=ease(t/.95), spread=opening*(1-closing);
 ctx.drawImage(images.blank,0,0);
 if(spread>=1){buildScene(i,t);ctx.drawImage(stage,0,0)}
 else if(spread>0){
  environmentCtx.clearRect(0,0,W,H);window.EnvironmentMotion.drawBackground(environmentCtx,i,t);
  // The clean printed floor stays flat. A single connected scenic card keeps
  // originally occluded roofs and branches together instead of exposing holes.
  const floorAlpha=ease(spread/.22);
  ctx.save();ctx.globalAlpha=floorAlpha;ctx.drawImage(images.ground,0,0);ctx.restore();
  const angle=Math.PI*.5*spread,sy=Math.sin(angle),tilt=Math.cos(angle);
  foldCtx.clearRect(0,0,W,H);foldCtx.drawImage(environmentFrame,0,0);foldCtx.globalCompositeOperation='destination-in';foldCtx.drawImage(currentFoldMask(i),0,0);foldCtx.globalCompositeOperation='source-over';
  ctx.save();ctx.globalAlpha=ease(spread/.16);ctx.translate(0,830);ctx.transform(1,0,-.025*tilt,Math.max(.002,sy),0,0);ctx.translate(0,-830);ctx.drawImage(foldScratch,0,0);ctx.restore();
  // Counter occlusion uses the same hinge projection as the scenic card; a
  // different transform would expose legs or create rectangular repair patches.
  sc.clearRect(0,0,W,H);window.CharacterMotion.draw(sc,i,t,{background:false});
  const actorSpread=ease((spread-.08)/.92);
  ctx.save();ctx.globalAlpha=ease(actorSpread/.2);ctx.translate(0,830);ctx.transform(1,0,-.025*tilt,Math.max(.002,sy),0,0);ctx.translate(0,-830);ctx.drawImage(stage,0,0);ctx.restore();
  // In the last small angle, dissolve the exact fully-open composite over the
  // reconstructed layers. Its current-time clouds/characters match the next frame.
  const join=ease((spread-.82)/.18);if(join>0){buildScene(i,t);ctx.save();ctx.globalAlpha=join;ctx.drawImage(stage,0,0);ctx.restore()}
 }
 if(i<5 && t>dur-1.75)window.PageTurn.draw(ctx,(t-dur+1.75)/1.75,images.blank);
}
window.renderFrame=function(time){
 const t=Math.max(0,Math.min(DURATION,time));
 let i=starts.findLastIndex(v=>t>=v), local=t-starts[i],dur=ends[i]-starts[i];
 ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='#fae7d3';ctx.fillRect(0,0,1920,1080);
 ctx.fillStyle='#f9dec7';ctx.fillRect(0,0,1920,1080);
 ctx.save();ctx.translate(60,12);ctx.scale(1800/W,1800/W);composeBook(i,local,dur);ctx.restore();
 const capIn=ease((local-.7)/.5),capOut=i<5?1-ease((local-dur+2.5)/.4):1;
 ctx.save();ctx.globalAlpha=capIn*capOut;
 ctx.textAlign='center';ctx.fillStyle='#573924';ctx.font='34px IntroKai, STKaiti, KaiTi, serif';
 ctx.letterSpacing='1px';ctx.fillText(lines[i][0],960,1008);ctx.fillText(lines[i][1],960,1050);ctx.letterSpacing='0px';
 ctx.restore();
 // Final invitation is typography outside the illustrated book, not printed into it.
 if(t>54){const f=ease((t-54)/1.6);ctx.fillStyle='rgba(250,231,211,'+f*.91+')';ctx.fillRect(0,0,1920,1080);ctx.globalAlpha=f;ctx.fillStyle='#8b3927';ctx.textAlign='center';ctx.font='80px IntroKai, STKaiti, KaiTi, serif';ctx.fillText('交子赶工记',960,487);ctx.font='34px IntroKai, STKaiti, KaiTi, serif';ctx.fillText('交个纸友，一起开工。',960,556);ctx.globalAlpha=1}
 return {chapter:i+1,title:titles[i],time:t,duration:DURATION};
};
window.INTRO={duration:DURATION,starts,ends,titles,lines,polygons,foldMeta:{method:'Connected scenic cardstock and separate actor cardstock folding over a fixed printed floor; softened lower edge',cloudMasksRestored:[1,4,5,6],currentTimeEnvironment:true,fullOpenBlendStart:.82}};
