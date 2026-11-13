// Executed in the compositor browser. Test layers independently so background
// movement cannot conceal a frozen actor or accidentally satisfy an actor check.
window.runLayerChecks=function(){
 const c=document.createElement('canvas');c.width=1672;c.height=941;const g=c.getContext('2d',{willReadFrequently:true});
 const snap=(fn,i,t)=>{g.clearRect(0,0,1672,941);fn(g,i,t);return g.getImageData(0,0,1672,941).data};
 function delta(a,b,roi=[0,0,1672,941]){let changed=0,magenta=0;for(let y=roi[1];y<roi[1]+roi[3];y++)for(let x=roi[0];x<roi[0]+roi[2];x++){const k=(y*1672+x)*4;if(Math.abs(a[k]-b[k])+Math.abs(a[k+1]-b[k+1])+Math.abs(a[k+2]-b[k+2])+Math.abs(a[k+3]-b[k+3])>45)changed++;if(b[k+3]>160&&b[k]>170&&b[k+2]>170&&b[k+1]<65)magenta++}return {changed,magenta}}
 const results=[];
 for(let i=0;i<6;i++){
  const actor=(g,i,t)=>CharacterMotion.draw(g,i,t,{background:false});
  const d=delta(snap(actor,i,1.4),snap(actor,i,i===4?8:5));results.push({name:'isolated_character_chapter_'+(i+1),...d,passed:d.changed>1000&&d.magenta===0});
  const leaf=delta(snap(Ambience.drawOver,i,1.5),snap(Ambience.drawOver,i,4));results.push({name:'isolated_leaves_chapter_'+(i+1),...leaf,passed:leaf.changed>30&&leaf.magenta===0});
  const b1=snap(EnvironmentMotion.drawBackground,i,1.5),b2=snap(EnvironmentMotion.drawBackground,i,4.5);
  const edge=delta(b1,b2,[0,855,1672,86]);results.push({name:'fixed_book_edges_chapter_'+(i+1),...edge,passed:edge.changed===0});
 }
 for(const i of [0,3,4,5]){const r=EnvironmentMotion.meta.cloudRegions[i];const d=delta(snap(EnvironmentMotion.drawBackground,i,1),snap(EnvironmentMotion.drawBackground,i,4),[r[0],r[1],r[2]-r[0],r[3]-r[1]]);results.push({name:'cloud_motion_chapter_'+(i+1),...d,passed:d.changed>100})}
 for(const i of [0,3,4]){
  const a=snap(Ambience.drawUnder,i,1.5),b=snap(Ambience.drawUnder,i,3.7),d=delta(a,b);
  const mask=document.createElement('canvas');mask.width=1672;mask.height=941;const mg=mask.getContext('2d');mg.fillStyle='#fff';
  for(const p of Ambience.meta.waterRegions[i]){mg.beginPath();p.forEach(([x,y],n)=>n?mg.lineTo(x,y):mg.moveTo(x,y));mg.closePath();mg.fill();mg.lineWidth=2;mg.stroke()}
  const m=mg.getImageData(0,0,1672,941).data;let leaked=0;for(let k=3;k<b.length;k+=4)if(b[k]>8&&m[k]===0)leaked++;
  results.push({name:'clipped_water_chapter_'+(i+1),...d,leaked,passed:d.changed>40&&leaked===0});
 }
 // The same time must render exactly the same pixels, independent of seek order.
 renderFrame(37.3);const output=document.querySelector('canvas'),og=output.getContext('2d'),p=og.getImageData(0,0,1920,1080).data;
 renderFrame(49);renderFrame(37.3);const q=og.getImageData(0,0,1920,1080).data;let different=0;for(let k=0;k<p.length;k++)if(p[k]!==q[k])different++;
 results.push({name:'deterministic_scrubbing',differentBytes:different,passed:different===0});
 return {environment:EnvironmentMotion.meta,ambience:Ambience.meta,results};
};
