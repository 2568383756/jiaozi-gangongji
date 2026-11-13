// Executed in the compositor browser. Test layers independently so background
// movement cannot conceal a frozen actor or accidentally satisfy an actor check.
window.runLayerChecks=function(){
 const c=document.createElement('canvas');c.width=1672;c.height=941;const g=c.getContext('2d',{willReadFrequently:true});
 const snap=(fn,i,t)=>{g.clearRect(0,0,1672,941);fn(g,i,t);return g.getImageData(0,0,1672,941).data};
 function delta(a,b,roi=[0,0,1672,941]){let changed=0,magenta=0;for(let y=roi[1];y<roi[1]+roi[3];y++)for(let x=roi[0];x<roi[0]+roi[2];x++){const k=(y*1672+x)*4;if(Math.abs(a[k]-b[k])+Math.abs(a[k+1]-b[k+1])+Math.abs(a[k+2]-b[k+2])+Math.abs(a[k+3]-b[k+3])>45)changed++;if(b[k+3]>160&&b[k]>170&&b[k+2]>170&&b[k+1]<65)magenta++}return {changed,magenta}}
 const results=[];
 if(window.CartMotion){
  const zero=CartMotion.getState(0),moved=CartMotion.getState(48);let rollingError=0,verticalError=0;
  moved.wheels.forEach((w,n)=>{rollingError=Math.max(rollingError,Math.abs((w.angle-zero.wheels[n].angle)*w.radius-48));verticalError=Math.max(verticalError,Math.abs(w.cy-zero.wheels[n].cy),Math.abs(w.hubAngle))});
  results.push({name:'cart_roll_distance_and_axles',rollingError,verticalError,passed:rollingError<1e-8&&verticalError===0&&moved.wheels.every(w=>w.angle>0)});
  const cart=(g,_i,travel)=>{g.save();g.translate(-travel,0);CartMotion.draw(g,1295,625,travel);g.restore()},a=snap(cart,0,0),b=snap(cart,0,48);
  let innerChanged=0,rimChanged=0,hubChanged=0;
  for(const w of zero.wheels)for(let y=Math.floor(w.cy-w.ry);y<=Math.ceil(w.cy+w.ry);y++)for(let x=Math.floor(w.cx-w.rx);x<=Math.ceil(w.cx+w.rx);x++){
   const radius=Math.hypot((x-w.cx)/w.sx,(y-w.cy)/w.sy),k=(y*1672+x)*4,changed=Math.abs(a[k]-b[k])+Math.abs(a[k+1]-b[k+1])+Math.abs(a[k+2]-b[k+2])>30;
   if(changed){if(radius>37&&radius<50)rimChanged++;if(radius<9)hubChanged++;if(radius>14&&radius<31)innerChanged++}
  }
  results.push({name:'cart_rotating_spokes_fixed_rims_and_hubs',innerChanged,rimChanged,hubChanged,passed:innerChanged>100&&rimChanged<8&&hubChanged===0});
 }
 if(CharacterMotion.debug.contacts){
  for(const [i,label,w,h,before,after] of [[1,'private_receipt',99,47,1,5.3],[2,'official_receipt',81,43,1,5.3],[3,'cloth_parcel',86,86,1,5.3],[4,'workshop_handoff',150,58,1,4.5],[5,'final_jiaozi',102,57,1,6]]){
   const endpoints=[];for(const [t,hand] of [[before,'sourceHand'],[after,'targetHand']]){CharacterMotion.draw(g,i,t,{background:false});const p=CharacterMotion.debug.contacts.find(p=>p.label===label);if(!p)throw Error('Missing contact '+label);const dx=Math.max(0,Math.abs(p.object.x-p[hand].x)-w/2),dy=Math.max(0,Math.abs(p.object.y-p[hand].y)-h/2);endpoints.push({time:t,hand,gapToObjectBounds:Math.hypot(dx,dy)})}
   results.push({name:'handoff_endpoints_'+label,endpoints,passed:endpoints.every(p=>Number.isFinite(p.gapToObjectBounds)&&p.gapToObjectBounds<12)});
  }
  const samples=[];for(const t of [9.4,9.65,10,10.3,10.5]){CharacterMotion.draw(g,4,t,{background:false});const p=CharacterMotion.debug.contacts.find(p=>p.label==='stamp_grip');if(!p)throw Error('Missing stamp contact');const gap=Math.hypot(p.object.x+p.handleOffset[0]-p.hand.x,p.object.y+p.handleOffset[1]-p.hand.y);samples.push({time:t,amount:p.amount,gap})}
  results.push({name:'stamp_held_contact',samples,passed:samples.every(p=>p.gap<1)});
 }
 if(EnvironmentMotion.getWalkerStates)for(const i of [0,3,5]){
  let unsynchronized=0,movingSamples=0;let prev=EnvironmentMotion.getWalkerStates(i,0);
  for(let t=.1;t<=9;t+=.1){const next=EnvironmentMotion.getWalkerStates(i,t);next.forEach((p,n)=>{const distance=Math.hypot(p.x-prev[n].x,p.y-prev[n].y);if(distance>.04){movingSamples++;if(p.phase===prev[n].phase||(p.walk<.001&&prev[n].walk<.001))unsynchronized++}});prev=next}
  const stopA=EnvironmentMotion.getWalkerStates(i,8),stopB=EnvironmentMotion.getWalkerStates(i,9),stopped=stopA.every((p,n)=>p.x===stopB[n].x&&p.y===stopB[n].y&&p.phase===stopB[n].phase&&p.walk===0);
  results.push({name:'pedestrian_gait_chapter_'+(i+1),movingSamples,unsynchronized,stopped,passed:movingSamples>10&&unsynchronized===0&&stopped});
 }
 for(let i=0;i<6;i++){
  const actor=(g,i,t)=>CharacterMotion.draw(g,i,t,{background:false});
  const d=delta(snap(actor,i,1.4),snap(actor,i,i===4?8:5));results.push({name:'isolated_character_chapter_'+(i+1),...d,passed:d.changed>1000&&d.magenta===0});
  const leaves=Ambience.drawLeaves?((g,i,t)=>Ambience.drawLeaves(g,i,t,'all')):Ambience.drawOver;
  const leaf=delta(snap(leaves,i,1.5),snap(leaves,i,4));results.push({name:'isolated_leaves_chapter_'+(i+1),...leaf,passed:leaf.changed>30&&leaf.magenta===0});
  const b1=snap(EnvironmentMotion.drawBackground,i,1.5),b2=snap(EnvironmentMotion.drawBackground,i,4.5);
  const edge=delta(b1,b2,[0,855,1672,86]);results.push({name:'fixed_book_edges_chapter_'+(i+1),...edge,passed:edge.changed===0});
 }
 for(const i of [0,3,4,5]){const r=EnvironmentMotion.meta.cloudRegions[i];const d=delta(snap(EnvironmentMotion.drawBackground,i,1),snap(EnvironmentMotion.drawBackground,i,4),[r[0],r[1],r[2]-r[0],r[3]-r[1]]);results.push({name:'cloud_motion_chapter_'+(i+1),...d,passed:d.changed>100})}
 for(const i of [0,3,4]){
  const water=Ambience.drawWater||Ambience.drawUnder;
  const a=snap(water,i,1.5),b=snap(water,i,3.7),d=delta(a,b);
  const mask=document.createElement('canvas');mask.width=1672;mask.height=941;const mg=mask.getContext('2d');mg.fillStyle='#fff';
  for(const p of Ambience.meta.waterRegions[i]){mg.beginPath();p.forEach(([x,y],n)=>n?mg.lineTo(x,y):mg.moveTo(x,y));mg.closePath();mg.fill();mg.lineWidth=2;mg.stroke()}
  const m=mg.getImageData(0,0,1672,941).data;let leaked=0;for(let k=3;k<b.length;k+=4)if(b[k]>8&&m[k]===0)leaked++;
  results.push({name:'clipped_water_chapter_'+(i+1),...d,leaked,passed:d.changed>40&&leaked===0});
 }
 // The same time must render exactly the same pixels, independent of seek order.
 renderFrame(37.3);const output=document.querySelector('canvas'),og=output.getContext('2d'),p=og.getImageData(0,0,1920,1080).data;
 renderFrame(49);renderFrame(37.3);const q=og.getImageData(0,0,1920,1080).data;let different=0;for(let k=0;k<p.length;k++)if(p[k]!==q[k])different++;
 results.push({name:'deterministic_scrubbing',differentBytes:different,passed:different===0});
 return {environment:EnvironmentMotion.meta,ambience:Ambience.meta,cart:window.CartMotion?.meta||null,results};
};
