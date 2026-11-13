/* F01 v11: deterministic localized paper deformation and atlas pedestrians.
   Clouds, branches and hanging paper are displaced from the original image once;
   no duplicate static cloud is left below a translated copy. The book stays fixed. */
(function(){
 const W=1672,H=941,backgrounds=[];let gl,screen,program,textures=[];
 const ranges={0:[960,65,1515,260],3:[955,55,1480,250],4:[834,35,1210,158],5:[816,25,1140,123]};
 const meta={method:'Localized continuous UV displacement of original paper artwork; atlas walkers composited separately',cloudChapters:[1,4,5,6],cloudDisplacementAmplitude_px:18,branchAmplitude_px:3.5,lanternAmplitude_px:4,walkersPerChapter:[3,0,0,2,0,1],walkDistance_px:[90,0,0,82,0,70],cloudRegions:ranges,walkerMotion:'Separate smooth start/stop trajectories; phase follows traveled distance; stationary feet and phase after each arrival'};
 const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{x=clamp(x);return x*x*x*(x*(x*6-15)+10)};
 const walkerPaths={0:[['n2',565,534,655,543,.20,false,.45,4.8],['n5',838,527,770,518,.19,true,.8,4.55],['n4',692,512,734,521,.16,false,1.0,4.35]],3:[['n2',871,501,953,515,.19,false,.5,4.8],['n5',1009,488,950,484,.17,true,.95,4.4]],5:[['n2',560,443,630,466,.12,false,.5,6.8]]};
 function getWalkerStates(i,t){return (walkerPaths[i]||[]).map(([id,x0,y0,x1,y1,s,flip,start,duration],n)=>{
  const p=clamp((t-start)/duration),q=smooth(p),distance=Math.hypot(x1-x0,y1-y0)*q;
  // Ease the gait amplitude near both ends, while cumulative distance determines phase.
  const walk=smooth(p/.15)*smooth((1-p)/.15),phase=distance/(120*s)*Math.PI;
  return {id,x:x0+(x1-x0)*q,y:y0+(y1-y0)*q,s,flip,walk,phase,distance,n};
 })}
 function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
 async function init({images}){
  screen=document.createElement('canvas');screen.width=W;screen.height=H;
  gl=screen.getContext('webgl',{alpha:false,preserveDrawingBuffer:true,antialias:false});if(!gl)throw Error('WebGL needed for environment layers');
  const vs=shader(gl.VERTEX_SHADER,'attribute vec2 a; varying vec2 uv; void main(){gl_Position=vec4(a,0.,1.);uv=vec2((a.x+1.)*.5,(1.-a.y)*.5);}');
  const fs=shader(gl.FRAGMENT_SHADER,`precision highp float;varying vec2 uv;uniform sampler2D pic;uniform float t;uniform int chapter;
   float zone(vec2 p,vec4 r,float edge){return smoothstep(r.x,r.x+edge,p.x)*(1.-smoothstep(r.z-edge,r.z,p.x))*smoothstep(r.y,r.y+edge,p.y)*(1.-smoothstep(r.w-edge,r.w,p.y));}
   float hill(vec2 p,vec2 c,vec2 radius){float d=length((p-c)/radius);return 1.-smoothstep(.2,1.,d);}
   void main(){vec2 p=uv*vec2(1672.,941.);vec2 d=vec2(0.);float cloud=0.;
    if(chapter==0){float roof=p.x<1150.?263.:(p.x<1340.?263.-(p.x-1150.)*.48:172.+(p.x-1340.)*.46);cloud=zone(p,vec4(948.,57.,1525.,275.),24.)*(1.-smoothstep(roof-28.,roof-8.,p.y));}
    if(chapter==3){float roof=p.x<1140.?246.:(p.x<1340.?246.-(p.x-1140.)*.4:166.+(p.x-1340.)*.45);cloud=zone(p,vec4(939.,52.,1490.,262.),23.)*(1.-smoothstep(roof-29.,roof-9.,p.y));}
    if(chapter==4)cloud=zone(p,vec4(826.,28.,1224.,167.),22.);
    if(chapter==5)cloud=zone(p,vec4(817.,18.,1144.,125.),14.);
    d.x+=18.*sin(t*.40-.8)*cloud;d.y+=2.*sin(t*.52)*cloud;
    if(chapter==0||chapter>=3){float branch=hill(p,vec2(485.,105.),vec2(345.,125.))+hill(p,vec2(183.,183.),vec2(122.,102.));d.x+=3.5*sin(t*1.55+p.x*.003)*branch;d.y+=1.5*cos(t*1.4+p.x*.003)*branch;}
    // Hanging lantern and fabric motion has a fixed top attachment.
    vec4 lantern=vec4(0.);if(chapter==0)lantern=vec4(179.,383.,284.,535.);if(chapter==1)lantern=vec4(146.,278.,270.,511.);if(chapter==2)lantern=vec4(233.,277.,296.,416.);if(chapter==3)lantern=vec4(218.,333.,365.,510.);if(chapter==4)lantern=vec4(1217.,293.,1304.,427.);if(chapter==5)lantern=vec4(762.,290.,865.,474.);
    float pendulum=zone(p,lantern,14.)*clamp((p.y-lantern.y)/(lantern.w-lantern.y),0.,1.);d.x+=4.*sin(t*2.1+.7)*pendulum;
    if(chapter==1)d.x+=3.*sin(t*1.4+p.y*.012)*zone(p,vec4(1317.,276.,1497.,506.),16.);
    if(chapter==0||chapter==3){vec4 people=chapter==0?vec4(568.,383.,923.,490.):vec4(774.,374.,959.,463.);float crowd=zone(p,people,14.)*(1.-smoothstep(people.w-26.,people.w-7.,p.y));d.x+=1.2*sin(t*1.3+p.x*.065)*crowd;d.y+=.45*cos(t*1.6+p.x*.065)*crowd;}
    gl_FragColor=texture2D(pic,(p-d)/vec2(1672.,941.));
   }`);
  program=gl.createProgram();gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
  const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
  const pos=gl.getAttribLocation(program,'a');gl.enableVertexAttribArray(pos);gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);
  for(let i=0;i<6;i++){backgrounds[i]=images['c'+i];const tx=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tx);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,backgrounds[i]);textures.push(tx)}
 }
 function drawBackground(g,i,t){gl.useProgram(program);gl.bindTexture(gl.TEXTURE_2D,textures[i]);gl.uniform1i(gl.getUniformLocation(program,'pic'),0);gl.uniform1f(gl.getUniformLocation(program,'t'),t);gl.uniform1i(gl.getUniformLocation(program,'chapter'),i);gl.drawArrays(gl.TRIANGLES,0,6);g.drawImage(screen,0,0);
  // Cast shadows stay attached to the road. Foreground characters naturally occlude these walkers.
  for(const {id,x,y,s,flip,walk,phase,n} of getWalkerStates(i,t)){g.save();g.fillStyle='rgba(97,66,34,.10)';g.beginPath();g.ellipse(x,y,22*s/.2,2.8*s/.2,0,0,Math.PI*2);g.fill();g.restore();CharacterMotion.paint(g,id,x,y,s,{flip,walk,phase,arm:.08*Math.sin(phase)*walk,nod:.025*Math.sin(phase*.5)*walk,lean:.015*Math.sin(phase)*walk})}
 }
 window.EnvironmentMotion={init,drawBackground,backgrounds,meta,getWalkerStates};
})();
