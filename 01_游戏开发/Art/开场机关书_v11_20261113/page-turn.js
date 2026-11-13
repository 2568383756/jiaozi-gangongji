/* F01 v11: curled, textured paper page over the fixed book photograph.
   Surface: an inextensible ruled ribbon, integrated from its local tangent angles.
   The same spine and oblique projection are used for every vertex. No backdrop is rotated.
   API: PageTurn.draw(ctx, normalizedProgress, normalizedBlankCanvas). */
(() => {
  'use strict';
  const WIDTH=780, COLS=44, ROWS=8, SPINE_X=827, TOP=468, DEPTH=393, Z_SCREEN=.43;
  const clamp=x=>Math.max(0,Math.min(1,x));
  const smooth=x=>{x=clamp(x);return x*x*x*(x*(x*6-15)+10)};
  function point(ctx,p){ctx.lineTo(p.x,p.y)}
  function path(ctx,pts){ctx.beginPath();pts.forEach((p,i)=>i?point(ctx,p):ctx.moveTo(p.x,p.y));ctx.closePath()}
  function surface(progress){
    const p=clamp(progress), turn=smooth(p), wave=Math.sin(Math.PI*p), curl=.58*Math.sin(2*Math.PI*p);
    const rows=[];
    for(let j=0;j<=ROWS;j++){
      const v=j/ROWS, rest=Math.asin((30-19*v)/(WIDTH*Z_SCREEN)), base=rest+(Math.PI-2*rest)*turn;
      const sx=(721+82*v)/(WIDTH*Math.cos(rest));
      let x=0,z=0;const row=[];
      row.push({x:SPINE_X,y:TOP+DEPTH*v,z:0,v,u:0,theta:base,worldX:0});
      for(let k=1;k<=COLS;k++){
        const u=(k-.5)/COLS;
        // The free corner lifts first; trailing curvature reverses as the leaf settles.
        const theta=base+curl*Math.pow(u,1.25)+wave*.22*(v-.35)*Math.pow(u,1.6);
        x+=WIDTH/COLS*Math.cos(theta);z+=WIDTH/COLS*Math.sin(theta);
        row.push({x:SPINE_X+x*sx,y:TOP+DEPTH*v-z*Z_SCREEN,z,v,u:k/COLS,theta,worldX:x});
      }
      rows.push(row);
    }
    return rows;
  }
  function sourcePoint(p,back){
    // Sample the actual warm paper fibers inside the original page.
    return {x:900+550*(back?1-p.u:p.u),y:500+295*p.v};
  }
  function triangle(ctx,img,s,d){
    const [a,b,c]=s,[q,r,t]=d;
    const den=a.x*(b.y-c.y)+b.x*(c.y-a.y)+c.x*(a.y-b.y);
    if(Math.abs(den)<1e-5)return;
    const ax=(q.x*(b.y-c.y)+r.x*(c.y-a.y)+t.x*(a.y-b.y))/den;
    const bx=(q.x*(c.x-b.x)+r.x*(a.x-c.x)+t.x*(b.x-a.x))/den;
    const cx=(q.x*(b.x*c.y-c.x*b.y)+r.x*(c.x*a.y-a.x*c.y)+t.x*(a.x*b.y-b.x*a.y))/den;
    const ay=(q.y*(b.y-c.y)+r.y*(c.y-a.y)+t.y*(a.y-b.y))/den;
    const by=(q.y*(c.x-b.x)+r.y*(a.x-c.x)+t.y*(b.x-a.x))/den;
    const cy=(q.y*(b.x*c.y-c.x*b.y)+r.y*(c.x*a.y-a.x*c.y)+t.y*(a.x*b.y-b.x*a.y))/den;
    // A subpixel clip overlap suppresses cracks between texture triangles.
    const mx=(q.x+r.x+t.x)/3,my=(q.y+r.y+t.y)/3;
    const expanded=d.map(n=>{const dx=n.x-mx,dy=n.y-my,len=Math.hypot(dx,dy)||1;return {x:n.x+dx/len*.38,y:n.y+dy/len*.38}});
    ctx.save();path(ctx,expanded);ctx.clip();ctx.transform(ax,ay,bx,by,cx,cy);ctx.drawImage(img,0,0);ctx.restore();
  }
  function outline(rows){
    return [...rows[0],...rows.slice(1).map(r=>r[COLS]),...rows[ROWS].slice(0,-1).reverse(),...rows.slice(1,ROWS).reverse().map(r=>r[0])];
  }
  function shadow(ctx,rows,p){
    const outside=outline(rows).map(n=>({x:n.x+n.z*.11,y:TOP+DEPTH*n.v-(30-19*n.v)*Math.min(1,Math.abs(n.worldX)/WIDTH)+n.z*.025}));
    ctx.save();
    path(ctx,[{x:118,y:435},{x:827,y:468},{x:1549,y:438},{x:1630,y:850},{x:827,y:861},{x:36,y:850}]);ctx.clip();
    const height=Math.max(...rows.flat().map(n=>n.z));
    ctx.filter='blur('+(3+height*.028)+ 'px)';
    ctx.fillStyle='rgba(88,47,19,'+(.16*Math.sin(Math.PI*p))+')';path(ctx,outside);ctx.fill();ctx.restore();
  }
  function draw(ctx,progress,blank){
    if(!blank||progress<=0||progress>=1)return;
    const p=clamp(progress),rows=surface(p),border=outline(rows);
    ctx.save();
    ctx.globalAlpha*=Math.min(1,smooth(p/.035),smooth((1-p)/.045));
    shadow(ctx,rows,p);
    // Base fill eliminates potential subpixel holes even at edge-on orientation.
    path(ctx,border);ctx.fillStyle='#f9e3b8';ctx.fill();
    const tris=[];
    for(let j=0;j<ROWS;j++)for(let k=0;k<COLS;k++){
      const a=rows[j][k],b=rows[j][k+1],c=rows[j+1][k+1],d=rows[j+1][k];
      for(const points of [[a,b,c],[a,c,d]]){
        const theta=points.reduce((s,n)=>s+n.theta,0)/3;
        tris.push({points,theta,depth:points.reduce((s,n)=>s+n.z*.91+n.v*350,0)/3});
      }
    }
    tris.sort((a,b)=>a.depth-b.depth);
    for(const tri of tris){
      const back=Math.cos(tri.theta)<0;
      triangle(ctx,blank,tri.points.map(n=>sourcePoint(n,back)),tri.points);
    }
    // Continuous light across the whole surface avoids a visible triangle/strip grid.
    const outer=rows[Math.floor(ROWS/2)][COLS],back=p>.5;
    const shade=.025+.075*Math.sin(Math.PI*p)+(back?.045:0);
    const lighting=ctx.createLinearGradient(SPINE_X,660,Math.abs(outer.x-SPINE_X)>5?outer.x:SPINE_X+5,outer.y);
    lighting.addColorStop(0,'rgba(105,64,27,'+(shade+.075)+')');
    lighting.addColorStop(.27,'rgba(138,87,36,'+(shade+.035)+')');
    lighting.addColorStop(.72,'rgba(181,127,61,'+shade+')');
    lighting.addColorStop(1,'rgba(210,160,90,'+shade*.5+')');
    ctx.save();path(ctx,border);ctx.clip();ctx.fillStyle=lighting;ctx.fillRect(0,0,1672,941);ctx.restore();
    // A narrow bright top edge and a darker lower edge express cardstock thickness.
    ctx.save();ctx.beginPath();rows[0].forEach((n,i)=>i?point(ctx,n):ctx.moveTo(n.x,n.y));ctx.lineWidth=1.55;ctx.strokeStyle='#fff3d6';ctx.stroke();
    ctx.beginPath();rows[ROWS].forEach((n,i)=>i?point(ctx,n):ctx.moveTo(n.x,n.y));ctx.lineWidth=2.1;ctx.strokeStyle='rgba(155,111,58,.68)';ctx.stroke();
    ctx.beginPath();rows.forEach((r,i)=>i?point(ctx,r[COLS]):ctx.moveTo(r[COLS].x,r[COLS].y));ctx.lineWidth=1.5;ctx.strokeStyle='#fff0ce';ctx.stroke();ctx.restore();
    ctx.restore();
  }
  window.PageTurn={draw,surface,version:'v11_20261113',columns:COLS,rows:ROWS};
})();
