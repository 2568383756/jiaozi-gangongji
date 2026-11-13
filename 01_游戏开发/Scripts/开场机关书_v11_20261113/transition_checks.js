// Output-space flash/continuity check. This is not an aesthetic-quality score.
window.runTransitionChecks=function(){
 const output=document.querySelector('canvas'),probe=document.createElement('canvas');probe.width=480;probe.height=270;const g=probe.getContext('2d',{willReadFrequently:true});
 function capture(t){renderFrame(t);g.clearRect(0,0,480,270);g.drawImage(output,0,0,480,270);return g.getImageData(0,0,480,270).data}
 function meanDelta(a,b){let sum=0;for(let k=0;k<a.length;k+=4)sum+=Math.abs(a[k]-b[k])+Math.abs(a[k+1]-b[k+1])+Math.abs(a[k+2]-b[k+2]);return sum/(480*270*3*255)}
 const checks=[];for(let i=0;i<6;i++){
  const start=INTRO.starts[i],end=INTRO.ends[i],zones=[['open',start,start+1.25]];if(i<5)zones.push(['fold',end-2.65,end-1.6],['turn',end-1.7,end+.1]);
  for(const [name,a,b] of zones){let previous=capture(a),max=0,worst=a,samples=0;
   for(let t=a+1/24;t<=b+1e-6;t+=1/24){const next=capture(t),d=meanDelta(previous,next);if(d>max){max=d;worst=t}previous=next;samples++}
   checks.push({name:name+'_chapter_'+(i+1),samples,maxNormalizedMeanPixelDelta:max,worstTime:worst,passed:Number.isFinite(max)&&max<.12});
  }
 }
 return {version:'v11_20261113',method:'480x270 RGB mean absolute difference across consecutive 24 fps frames; only guards against broad flashes/cuts, manual review still required',pageMechanics:window.BookMechanics?.meta||null,checks};
};
