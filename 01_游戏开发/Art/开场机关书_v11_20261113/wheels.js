/* F01 v11: one original wheel rim per wheel, a circular moving spoke insert,
   and an axle cap that remains fixed to the cart. No second complete wheel is pasted.
   Pixel coordinates measured on the 1448 x 1086 adopted atlas. */
(function(){
 'use strict';
 const BOX={x:31,y:405,w:341,h:280},DEFAULT={x:1295,y:625,w:320,h:263};
 const SOURCE_WHEELS=[{id:'front_screen_left',cx:220.5,cy:618.5,r:51,rotor:34.5,hub:12.2},{id:'front_screen_right',cx:106.25,cy:618.5,r:51,rotor:34.5,hub:12.2}];
 let body,contactShadow,rotors=[],hubs=[],ready=false;
 const meta={source:'assets/props_adopted.png',sourceDimensions:[1448,1086],cartBox:BOX,wheelCount:2,
  method:'Keep the sole original outer rims and frame; replace only circular inner spoke discs; fixed original axle caps above the rotors',
  noDuplicateWholeWheel:true,rotation:'Clockwise in screen coordinates for rightward travel; radians = travel / projected ground radius',
  sourceWheels:SOURCE_WHEELS,defaultPlacement:DEFAULT,shadow:'Two small contact shadows anchored below the original wheels',
  note:'The adopted cart is drawn in a side elevation; both visible wheels belong to its near side, not different perspective planes.'};
 const canvas=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c};
 const clamp=x=>Math.max(0,Math.min(1,x));
 function chroma(source){const c=canvas(source.width,source.height),g=c.getContext('2d',{willReadFrequently:true});g.drawImage(source,0,0);const d=g.getImageData(0,0,c.width,c.height),p=d.data;
  for(let k=0;k<p.length;k+=4){const spill=Math.min(p[k],p[k+2])-p[k+1];if(p[k]>80&&p[k+2]>80&&spill>22){const a=1-clamp((spill-22)/145);p[k+3]=Math.round(a*255);if(a>.05&&a<1){p[k]=Math.max(0,Math.min(255,(p[k]-(1-a)*255)/a));p[k+2]=Math.max(0,Math.min(p[k+1]+12,(p[k+2]-(1-a)*255)/a))}}}g.putImageData(d,0,0);return c;
 }
 function disk(source,cx,cy,r){const c=canvas(112,112),g=c.getContext('2d');g.beginPath();g.arc(56,56,r,0,Math.PI*2);g.clip();g.drawImage(source,56-cx,56-cy);return c}
 async function init(){const image=await new Promise((resolve,reject)=>{const im=new Image;im.onload=()=>resolve(im);im.onerror=()=>reject(Error('Missing adopted prop atlas'));im.src='assets/props_adopted.png'});const keyed=chroma(image);
  body=canvas(BOX.w,BOX.h);body.getContext('2d').drawImage(keyed,BOX.x,BOX.y,BOX.w,BOX.h,0,0,BOX.w,BOX.h);
  rotors=SOURCE_WHEELS.map(w=>disk(keyed,w.cx,w.cy,w.rotor));hubs=SOURCE_WHEELS.map(w=>disk(keyed,w.cx,w.cy,w.hub));
  contactShadow=canvas(112,16);const sg=contactShadow.getContext('2d');sg.fillStyle='rgba(86,51,24,.14)';sg.beginPath();sg.ellipse(56,8,51*.54,3.1,0,0,Math.PI*2);sg.fill();ready=true;
 }
 function getState(travel=0,x=DEFAULT.x,y=DEFAULT.y,w=DEFAULT.w,h=DEFAULT.h){const sx=w/BOX.w,sy=h/BOX.h;
  return {travel,cart:{x:x+travel,y,w,h},wheels:SOURCE_WHEELS.map(v=>({id:v.id,cx:x+travel+w/2-(v.cx-BOX.x)*sx,cy:y-h/2+(v.cy-BOX.y)*sy,rx:v.r*sx,ry:v.r*sy,radius:v.r*sy,angle:travel/(v.r*sy),hubAngle:0,sx,sy,contactY:y-h/2+(v.cy-BOX.y+v.r)*sy}))};
 }
 function draw(g,x=DEFAULT.x,y=DEFAULT.y,travel=0,w=DEFAULT.w,h=DEFAULT.h){if(!ready)throw Error('Await CartMotion.init() before drawing');const state=getState(travel,x,y,w,h);g.save();g.imageSmoothingQuality='high';
  // These shadows do not rotate or rise with the spokes.
  for(const wheel of state.wheels)g.drawImage(contactShadow,wheel.cx-56*wheel.sx,wheel.contactY+1-8*wheel.sy,112*wheel.sx,16*wheel.sy);
  g.save();g.translate(state.cart.x,y);g.scale(-1,1);g.drawImage(body,-w/2,-h/2,w,h);g.restore();
  for(let n=0;n<state.wheels.length;n++){const wheel=state.wheels[n];
   // Rotate a circular source disc first, then project it. The oval outline stays fixed.
   g.save();g.translate(wheel.cx,wheel.cy);g.scale(wheel.sx,wheel.sy);g.beginPath();g.arc(0,0,SOURCE_WHEELS[n].rotor,0,Math.PI*2);g.clip();g.rotate(wheel.angle);g.scale(-1,1);g.drawImage(rotors[n],-56,-56);g.restore();
   // Reapply the original small hub cap without rotation, visibly anchoring the axle.
   g.save();g.translate(wheel.cx,wheel.cy);g.scale(-wheel.sx,wheel.sy);g.drawImage(hubs[n],-56,-56);g.restore();
  }g.restore();return state;
 }
 window.CartMotion={init,draw,getState,meta};
})();
