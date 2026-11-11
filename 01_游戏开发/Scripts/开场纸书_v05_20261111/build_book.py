"""F01 opening: horizontal tabletop pop-up storybook, Blender 5.3.
Thin cut-paper scenery, ground-level folding hinges and ordinary bound leaves.
Six automatic chapters; no borrowed reference frames enter the final artwork.
"""
import bpy, math, json, sys, random
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
OUT=ROOT/'01_游戏开发/Art/开场纸书_v05_20261111'; A=OUT/'assets'; W=HERE/'work'
OUT.mkdir(exist_ok=True,parents=True);W.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
S=bpy.context.scene;S.render.engine='BLENDER_EEVEE';S.eevee.taa_render_samples=64
S.eevee.use_raytracing=False;S.eevee.shadow_ray_count=3
S.render.resolution_x=1920;S.render.resolution_y=1080;S.render.resolution_percentage=100
S.render.fps=24;S.frame_start=1;S.frame_end=1152
S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB';S.render.film_transparent=False
S.view_settings.view_transform='AgX'
S.world=bpy.data.worlds.new('Warm paper studio');S.world.use_nodes=True
S.world.node_tree.nodes['Background'].inputs[0].default_value=(.66,.49,.31,1)
S.world.node_tree.nodes['Background'].inputs[1].default_value=.65
FONT=bpy.data.fonts.load('C:/Windows/Fonts/simkai.ttf')
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=.95
 # A fine physical surface, deliberately restrained rather than noisy grain.
 n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=190;n.inputs['Detail'].default_value=1
 bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.11;bump.inputs['Distance'].default_value=.012
 m.node_tree.links.new(n.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 return m
ivory=mat('暖象牙纸',(.86,.74,.53));pale=mat('厚卡纸切边',(.95,.86,.67));ink=mat('黛墨',(.045,.115,.12));navy=mat('黛青封面',(.035,.10,.13));red=mat('朱砂色纸',(.65,.085,.035));gold=mat('银杏金纸',(.82,.49,.12));wood=mat('赭木纸',(.35,.16,.065));jade=mat('碧水纸',(.17,.46,.43));sage=mat('远山纸',(.39,.53,.40));blue=mat('瓦蓝纸',(.13,.24,.34));rose=mat('花瓣纸',(.72,.32,.25));dark=mat('背景青灰',(.065,.105,.103))
def empty(name,loc=(0,0,0),p=None):
 o=bpy.data.objects.new(name,None);S.collection.objects.link(o);o.location=loc;o.parent=p;return o
def cube(name,loc,size,m,p=None,bevel=.008):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.location=loc;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);o.parent=p
 if bevel:
  q=o.modifiers.new('Cut edge','BEVEL');q.width=bevel;q.segments=2
 return o
def polygon(name,vs,m,p=None,thick=.018):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],[list(range(len(vs)))]);mesh.update();mesh.materials.append(m)
 o=bpy.data.objects.new(name,mesh);S.collection.objects.link(o);o.parent=p
 if thick:q=o.modifiers.new('Thin cardstock','SOLIDIFY');q.thickness=thick
 return o
def line(name,pts,m,p=None,width=.012):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=width;d.bevel_resolution=1
 sp=d.splines.new('POLY');sp.points.add(len(pts)-1)
 for v,co in zip(sp.points,pts):v.co=(*co,1)
 o=bpy.data.objects.new(name,d);S.collection.objects.link(o);o.parent=p;d.materials.append(m);return o
def txt(name,body,loc,size,m,p=None,rot=(math.pi/2,0,0),align='CENTER'):
 d=bpy.data.curves.new(name,'FONT');d.body=body;d.font=FONT;d.size=size;d.align_x=align;d.align_y='CENTER';d.space_line=1.25;d.extrude=.0004
 o=bpy.data.objects.new(name,d);S.collection.objects.link(o);o.location=loc;o.rotation_euler=rot;o.parent=p;d.materials.append(m);return o
def key(o,prop,f,val):setattr(o,prop,val);o.keyframe_insert(prop,frame=f)
def shown(o,start,end):
 for f,v in [(1,True),(max(start-1,1),True),(start,False),(end,False),(end+1,True)]:o.hide_render=v;o.keyframe_insert('hide_render',frame=f)
def disk(name,loc,r,m,p=None):
 x,y,z=loc;return polygon(name,[(x+math.cos(t*math.tau/64)*r,y,z+math.sin(t*math.tau/64)*r) for t in range(64)],m,p)
cache={};texmats={}
warmfloor=mat('暖杏纸地台',(.84,.64,.39));warmsky=mat('浅赭天空纸',(.68,.39,.16));apricot=mat('柔杏色纸',(.86,.56,.26))
dark.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.26,.145,.075,1)
def image_mat(file):
 if file in texmats:return texmats[file]
 im=bpy.data.images.load(str(A/file),check_existing=True);w,h=im.size
 pix=np.asarray(im.pixels[:],np.float32).reshape(h,w,4);cache[file]=(w,h,pix)
 m=bpy.data.materials.new(file);m.use_nodes=True;n=m.node_tree.nodes;n.clear()
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');tx=n.new('ShaderNodeTexImage');tx.image=im
 bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=.07
 m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.18
 clip=n.new('ShaderNodeMath');clip.operation='GREATER_THAN';clip.inputs[1].default_value=.45
 m.node_tree.links.new(tx.outputs['Alpha'],clip.inputs[0]);m.node_tree.links.new(clip.outputs[0],bs.inputs['Alpha']);m.node_tree.links.new(bs.outputs[0],out.inputs[0])
 texmats[file]=m;return m
def cutout(name,file,uv,loc,height,p=None,width=None):
 m=image_mat(file);iw,ih,pix=cache[file];u0,v0,u1,v1=uv
 lo=int(u0*iw);hi=int(u1*iw);bot=int(v0*ih);top=int(v1*ih)
 left=[];right=[]
 for row in range(bot,top,5):
  hits=np.flatnonzero(pix[row,lo:hi,3]>.48)
  # Trim neighbour silhouettes in UV space; original raster assets are unchanged.
  if file=='扁平纸艺植物云纹_v02.png' and .37<u0<.4:
   row_u=(hits+lo)/iw;limit=.667 if row/ih>.57 else .605
   hits=hits[(row_u>.388)&(row_u<limit)]
  if file=='扁平纸艺建筑_v02.png' and .28<u0<.31:
   row_u=(hits+lo)/iw;hits=hits[(row_u>.294)&(row_u<.704)]
  if len(hits):left.append(((lo+int(hits[0]))/iw,row/ih));right.append(((lo+int(hits[-1]))/iw,row/ih))
 outline=left+right[::-1]
 if len(outline)<6:outline=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)]
 width=width or height*(hi-lo)/(top-bot)
 vs=[((u-u0)/(u1-u0)*width-width/2,0,(v-v0)/(v1-v0)*height) for u,v in outline]
 o=polygon(name,vs,m,p,.025);o.location=loc;layer=o.data.uv_layers.new(name='Asset UV')
 for loop in o.data.loops:layer.data[loop.index].uv=outline[loop.vertex_index]
 o['source_asset']=file;return o
PAIR='扁平纸团印桃_v02.png';ARCH='扁平纸艺建筑_v02.png';PLANT='扁平纸艺植物云纹_v02.png'
def actor(name,idx,loc,h,p):
 root=empty(name,loc,p);cutout(name+'剪纸',PAIR,(idx*.5,0,(idx+1)*.5,1),(0,0,0),h,root)
 cube(name+'折叠支脚',(0,.10,.016),(.35,.28,.025),pale,root)
 return root
def house(name,idx,loc,h,p):
 # Nonuniform image widths preserve the generated assets' actual gutters.
 region=[(0,0,.29,1),(.29,0,.71,1),(.71,0,1,1)][idx]
 return cutout(name,ARCH,region,loc,h,p)
def plant(name,idx,loc,h,p):return cutout(name,PLANT,[(0,0,.38,1),(.38,0,.70,1),(.70,0,1,1)][idx],loc,h,p)
def mountain(name,x,y,z,w,h,m,p):
 return polygon(name,[(x-w/2,y,z),(x-w*.32,y,z+h*.38),(x-w*.08,y,z+h*.81),(x+w*.06,y,z+h),(x+w*.26,y,z+h*.55),(x+w/2,y,z)],m,p)
def leaf(name,x,y,z,w,h,m,p):
 o=polygon(name,[(x,y,z),(x-w/2,y,z+h*.6),(x-w*.25,y,z+h),(x+w*.3,y,z+h*.95),(x+w*.5,y,z+h*.55)],m,p)
 line(name+'刻线',[(x,y-.014,z),(x,y-.014,z+h*.9)],wood,p,.004);return o

# One ordinary bound volume: two continuous facing leaves, not radial rooms.
paper=mat('奶油棉纸',(.91,.80,.61));covermat=mat('赭红书衣',(.31,.072,.035))
printink=mat('暖墨印字',(.018,.006,.002));printred=mat('朱砂印字',(.19,.018,.006))
whiteink=mat('浅金印字',(.9,.78,.54))
grey=mat('铁钱灰纸',(.19,.20,.17));lightgrey=mat('铁钱切边',(.43,.40,.31))
tea=mat('茶青纸',(.28,.36,.17));sand=mat('暖沙色印底',(.77,.57,.31))
book=empty('BOOK · 正常双页书册')
book['mechanism']='single vertical spine; five right-to-left leaf turns; side pull tabs'
BW=6.55;BOTTOM=.35;TOP=7.55

def page_mesh(name,side,y,m,p=book,thickness=.025):
 vs=[];faces=[];n=36
 for j in range(n+1):
  t=j/n;x=side*(.045+t*(BW-.045));yy=y-.14*math.sin(t*math.pi)+.08*math.exp(-t*8)
  vs.extend([(x,yy,BOTTOM),(x,yy,TOP)])
 for j in range(n):faces.append((j*2,j*2+1,j*2+3,j*2+2))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],faces);mesh.update();mesh.materials.append(m)
 ob=bpy.data.objects.new(name,mesh);S.collection.objects.link(ob);ob.parent=p
 mod=ob.modifiers.new('卡纸厚度','SOLIDIFY');mod.thickness=thickness
 return ob

for side in [-1,1]:
 cube('硬书壳', (side*3.34,.43,3.94),(6.68,.18,7.45),covermat,book,.065)
 for k in range(12):page_mesh('纸页叠边_%s_%02d'%(side,k),side,.37-k*.022,pale if k%3 else ivory,thickness=.016)
 page_mesh('当前左页' if side<0 else '当前右页',side,.065,paper)
 for x in [side*.28,side*6.27]:line('纸页压印边',[(x,-.10,.68),(x,-.10,7.2)],sand,book,.007)
 line('页眉压线',[(side*.32,-.12,6.56),(side*6.22,-.12,6.56)],gold,book,.009)
 line('页脚压线',[(side*.32,-.12,1.62),(side*6.22,-.12,1.62)],gold,book,.009)
 for x in [side*.43,side*6.1]:
  for z in [.82,7.1]:
   polygon('角花',[(x-.06,-.13,z),(x,-.13,z+.07),(x+.06,-.13,z),(x,-.13,z-.07)],gold,book,.008)
cube('装订圆脊',(0,.37,3.94),(.19,.25,7.46),covermat,book,.06)
line('中缝线',[(0,-.09,.4),(0,-.09,7.5)],wood,book,.012)
# Ribbon and a thin cover lip make the page block unmistakably a book.
polygon('朱红书签',[(.12,.30,.4),(.37,.30,.4),(.37,-.8,.03),(.25,-.8,.13),(.12,-.8,.03)],red,book,.025)
cube('暖木桌面',(0,2,-.11),(200,200,.18),warmfloor,bevel=0)

titles=['铁钱难行','纸券初生','官办交子','一纸通市','纸艺开工','合做交子']
small=['北宋 · 蜀地','交子铺户','益州交子务','从街市，到纸艺世界','与你的搭档一起','交子赶工记']
captions=[
 '北宋蜀地，街市买卖日渐兴旺。\n沉重的铁钱，却让往来多有不便。',
 '商人把钱存进铺户，取回一纸凭券。\n凭券取钱，也渐渐凭券做起了买卖。',
 '从民间的凭券，到官府发行的纸币。\n益州交子务，开启了交子的新篇。',
 '一纸交子，让买卖少了搬钱的辛劳。\n而在纸艺世界里，故事正等你们接续。',
 '抄出的纸等风晾干，再印上墨纹与朱印。\n你们接力，赶出作坊的开张第一单。',
 '你们的模样，随第一张交子送进街巷。\n交个纸友，一起开工，故事才刚开始。']

chapters=[];tabs=[];motions=[]
def vis_tree(root,start,end):
 for ob in [root]+list(root.children_recursive):shown(ob,start,end)
def drive(ob,prop,index,tab,expr):
 fc=ob.driver_add(prop,index);d=fc.driver;d.type='SCRIPTED';v=d.variables.new();v.name='pull';v.type='TRANSFORMS';v.targets[0].id=tab;v.targets[0].transform_type='LOC_X';v.targets[0].transform_space='LOCAL_SPACE';d.expression=expr
def slab(name,loc,w,h,m,p):return cube(name,loc,(w,.035,h),m,p,.012)
def border(name,x,y,z,w,h,m,p,width=.012):
 return line(name,[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2),(x-w/2,y,z-h/2)],m,p,width)
def coin(name,loc,r,p):
 # An actual square opening, not a black dot: iron cash, cut from grey paper.
 vs=[];n=32
 for j in range(n):
  a=j*math.tau/n;c=math.cos(a);s=math.sin(a);q=.28*r/max(abs(c),abs(s))
  vs.extend([(loc[0]+c*r,loc[1],loc[2]+s*r),(loc[0]+c*q,loc[1],loc[2]+s*q)])
 faces=[(j*2,((j+1)%n)*2,((j+1)%n)*2+1,j*2+1) for j in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],faces);mesh.materials.append(grey)
 ob=bpy.data.objects.new(name,mesh);S.collection.objects.link(ob);ob.parent=p;q=ob.modifiers.new('铁钱纸片厚度','SOLIDIFY');q.thickness=.045
 line('钱缘',[(loc[0]+math.cos(a*math.tau/64)*r*.87,loc[1]-.028,loc[2]+math.sin(a*math.tau/64)*r*.87) for a in range(65)],lightgrey,p,.009)
 for a in [0,math.pi/2,math.pi,math.pi*1.5]:
  x=loc[0]+math.cos(a)*r*.57;z=loc[2]+math.sin(a)*r*.57
  line('钱文刻痕',[(x-.04,loc[1]-.03,z-.035),(x+.04,loc[1]-.03,z+.035)],lightgrey,p,.014)
 return ob
def receipt(name,loc,w,h,p,heading='交 子',seal=False):
 root=empty(name,loc,p);slab('纸券底纸',(0,0,0),w,h,pale,root);border('券纹边框',0,-.03,0,w-.12,h-.12,wood,root,.014)
 border('券纹内框',0,-.04,0,w-.23,h-.23,sand,root,.007)
 txt('券标题',heading,(0,-.05,h*.29),w*.19,ink,root)
 # Stylised printed rules and landscape, not an archaeological reconstruction.
 for k in range(5):line('雕版竖纹',[((k-2)*w*.12,-.05,-h*.08),((k-2)*w*.12,-.05,h*.08)],wood,root,.01)
 mountain('券上纹样',0,-.05,-h*.31,w*.65,h*.17,sand,root)
 if seal:
  slab('券上朱印',(w*.24,-.07,-h*.23),w*.21,w*.21,red,root)
  txt('印文','信',(w*.24,-.10,-h*.23),w*.13,pale,root)
 return root
def lantern(name,x,y,z,p):
 root=empty(name,(x,y,z),p)
 polygon('灯笼纸片',[(-.19,0,-.28),(-.26,0,-.10),(-.26,0,.17),(-.16,0,.34),(.16,0,.34),(.26,0,.17),(.26,0,-.10),(.19,0,-.28)],red,root)
 for dx in [-.13,0,.13]:line('灯纸折痕',[(dx,-.02,-.25),(dx,-.02,.3)],gold,root,.008)
 line('灯绳',[(0,0,.34),(0,0,.68)],wood,root,.009);line('灯穗',[(0,0,-.28),(0,0,-.52)],gold,root,.014)
 return root
def stand(name,x,y,z,w,h,p):
 root=empty(name,(x,y,z),p);slab('台面',(0,0,h),w,.1,wood,root)
 for a in [-1,1]:slab('台脚',(a*w*.4,.05,h/2),.08,h,gold,root)
 return root

for i in range(6):
 start=i*192+1;end=(i+1)*192
 chapter=empty('CHAPTER_%02d · '%(i+1)+titles[i],p=book);chapters.append(chapter)
 txt('章节标题',titles[i],(-3.32,-.20,6.99),.42,wood,chapter)
 txt('右页小题',small[i],(3.3,-.20,6.99),.25,red,chapter)
 # A low paper caption flap bridges the gutter without the spine crossing type.
 slab('故事纸条',(0,-.54,1.04),11.7,1.04,paper,chapter)
 for side in [-1,1]:polygon('纸条折角',[(side*5.85,-.54,.52),(side*6.04,-.36,.65),(side*6.04,-.36,1.42),(side*5.85,-.54,1.56)],ivory,chapter)
 txt('故事文字',captions[i],(0,-.59,1.03),.302,ink,chapter)
 for side in [-1,1]:txt('页码',str(i*2+(1 if side<0 else 2)).zfill(2),(side*6.22,-.16,.57),.13,wood,chapter)
 # The shared illustrated field crosses the gutter; popups project only a little.
 art=empty('纸上画幅_%02d'%i,(0,0,0),chapter);motions.append(art)
 disk('暖日纸片',(3.80,-.22,5.52),.60,gold,art)
 mountain('远山左',-3.5,-.25,2.05,5,2.8,sand,art)
 mountain('远山右',3.9,-.26,2.05,4.4,3.55,sage,art)
 polygon('绵延纸地',[(-6,-.36,1.9),(-6,-.36,2.25),(-4,-.36,2.55),(-1,-.36,2.32),(2,-.36,2.62),(5.9,-.36,2.2),(5.9,-.36,1.9)],apricot,art)
 line('纸地刻边',[(-5.7,-.40,2.06),(-3.9,-.40,2.25),(-1.4,-.40,2.13),(1,-.40,2.31),(4,-.40,2.11),(5.7,-.40,2.08)],gold,art,.018)
 plant('薄纸如意云',2,(1.6,-.41,5.18),1.25,art)
 # The visible paper strip slides through the right page slit; no UI lever.
 tab=empty('PULL_TAB_%02d'%i,(0,0,0),chapter);tabs.append(tab)
 slab('抽拉纸签',(6.28,.01,2.37),1.40,.45,pale,tab)
 border('纸签描边',6.28,-.018,2.37,1.31,.35,gold,tab,.01)
 polygon('抽拉箭头',[(6.69,-.04,2.37),(6.48,-.04,2.48),(6.48,-.04,2.26)],red,tab,.008)
 txt('纸签字','拉',(6.18,-.04,2.37),.18,wood,tab)
 line('滑槽',[(6.48,-.17,2.06),(6.48,-.17,2.68)],wood,chapter,.022)
 # Physical fold supports below the artwork, restrained and deliberately visible.
 for x in [-3.8,2.8]:
  polygon('弹起折脚',[(x,-.12,2.10),(x+.28,-.82,2.10),(x+.46,-.82,2.1),(x+.18,-.12,2.10)],pale,art)
  line('折脚压痕',[(x+.1,-.38,2.11),(x+.38,-.38,2.11)],sand,art,.006)
 for f,val in [(start,0),(start+12,0),(start+52,.72),(start+132,.72),(start+151,0),(end,0)]:key(tab,'location',f,(val,0,0))
 # Fold toward the page before the next leaf turns. This is shallow paper relief.
 for f,sy in [(start,.04),(start+20,.5),(start+52,1),(start+145,1),(start+164,.02),(end,.02)]:
  if i==5 and f>start+145:sy=1
  key(art,'scale',f,(1,sy,1))
 vis_tree(chapter,start,end)

# 1. Trade flourishes, but iron cash burdens the traveller.
p=motions[0]
house('左侧街铺',0,(-4.45,-.61,2.08),3.82,p);house('右侧街铺',2,(3.96,-.6,2.08),3.7,p)
plant('街口银杏',0,(-5.35,-.81,2.05),3.3,p);plant('街口竹叶',1,(5.38,-.84,2.05),2.9,p)
lantern('街边灯',-2.8,-.8,4.52,p);lantern('街边灯',2.7,-.8,4.52,p)
cart=empty('沉重的钱车',(-.9,-1.17,2.56),p)
slab('车斗',(0,0,.25),2.15,.63,wood,cart)
border('木车刻边',0,-.04,.25,1.96,.47,gold,cart,.015)
for x in [-.74,.74]:
 disk('车轮',(x,-.06,-.22),.27,wood,cart);disk('车轴',(x,-.09,-.22),.07,gold,cart)
 for a in range(6):line('辐条',[(x,-.08,-.22),(x+math.cos(a*math.tau/6)*.24,-.08,-.22+math.sin(a*math.tau/6)*.24)],gold,cart,.009)
line('车辕',[(1,-.02,.22),(2.17,-.02,.04)],wood,cart,.045)
for j in range(10):coin('铁钱堆',(-.8+(j%5)*.39,-.06-(j//5)*.06,.60+(j//5)*.32),.27,cart)
drive(cart,'location',0,tabs[0],'-1.4+pull*1.15')
traveller=empty('推车行商',(1.62,-.03,.15),cart)
polygon('行商纸袍',[(-.15,0,.05),(-.25,0,.67),(-.15,0,.96),(.15,0,.96),(.25,0,.55),(.2,0,.05)],tea,traveller)
disk('行商脸',(0,-.03,1.10),.21,ivory,traveller)
polygon('行商帽',[(-.28,-.05,1.24),(0,-.05,1.43),(.28,-.05,1.24)],wood,traveller)
line('推车双臂',[(-.14,-.05,.80),(-.44,-.05,.52),(-.57,-.05,.18)],tea,traveller,.07)
for x in [-.12,.12]:line('迈步纸腿',[(x,0,.12),(x+.1,0,-.25)],wood,traveller,.06)
txt('铁钱画注','铁钱虽重，买卖不停。',(.15,-1.0,5.68),.26,wood,p)
coin('近景铁钱',(1.85,-1.28,3.72),.64,p);coin('近景铁钱',(2.58,-1.16,3.12),.49,p)
line('穿钱绳',[(1.85,-1.34,3.72),(2.58,-1.22,3.12),(2.78,-1.14,2.3)],gold,p,.024)

# 2. Deposit cash, take a receipt; a paper claim also passes between people.
p=motions[1]
house('交子铺户门面',1,(-3.74,-.6,2.08),4.13,p)
slab('铺户牌匾',(-3.74,-.67,4.43),1.38,.39,wood,p);txt('铺户牌匾字','交 子 铺',(-3.74,-.71,4.43),.22,pale,p)
stand('存钱柜台',-2.1,-1.1,2.12,2.1,.85,p)
for j in range(6):coin('存入铁钱',(-2.8+(j%3)*.4,-1.16,3.19+(j//3)*.3),.24,p)
note=receipt('可移动凭券',(1.7,-1.0,4.0),1.8,2.45,p,'交 子')
drive(note,'location',0,tabs[1],'.6+pull*1.7')
line('抽签连接纸条',[(.5,-.38,3.0),(5.7,-.38,3.0),(5.7,-.38,2.37),(6.4,-.38,2.37)],ivory,p,.07)
txt('存钱注','存钱',(-2.1,-1.2,2.44),.23,pale,p)
txt('凭券注','凭券取钱 · 转让交易',(2.3,-1.15,2.45),.24,wood,p)
plant('铺外银杏',0,(4.75,-.83,2.09),3.15,p)
for x in [-.5,.0,.5]:polygon('递券箭纹',[(x+.08,-.80,4),(x-.07,-.8,4.1),(x-.07,-.8,3.9)],gold,p)

# 3. Private jiaozi develops into official issue, with a clear historical title.
p=motions[2]
house('交子务纸建筑',1,(.8,-.58,2.07),4.15,p)
slab('交子务匾',(.8,-.69,4.54),1.56,.42,wood,p);txt('官署匾文','益州交子务',(.8,-.73,4.54),.21,pale,p)
receipt('民间凭券',(-3.52,-.9,3.83),1.32,1.95,p,'交 子')
txt('民间画注','民间铺户',(-3.52,-1.0,2.47),.25,wood,p)
official=receipt('官发纸币',(3.72,-1.03,3.91),1.64,2.35,p,'交 子',True)
drive(official,'location',2,tabs[2],'3.25+pull*.92')
txt('官办画注','官府发行',(3.72,-1.13,2.47),.25,wood,p)
for j in range(4):
 x=-2.25+j*.45;polygon('发展箭纹',[(x+.2,-.80,4),(x,-.80,4.13),(x,-.80,3.87)],gold,p)
lantern('官署灯',-.5,-.75,4.7,p);lantern('官署灯',2.13,-.75,4.7,p)
plant('官署竹',1,(-5.18,-.8,2.08),3.25,p)

# 4. Cloth and tea make its everyday use tangible, then the narrative crosses
# from historical inspiration into the fictional papercraft game.
p=motions[3]
house('茶铺',0,(-4.15,-.59,2.07),3.7,p);house('布铺',2,(4.1,-.60,2.07),3.7,p)
left=stand('茶摊',-2.8,-1.10,2.1,2.4,.85,p)
for j in range(3):
 x=-.7+j*.7;slab('茶篓',(x,-.08,1.12),.53,.45,tea,left);border('茶篓包边',x,-.11,1.12,.47,.38,gold,left,.01);txt('茶字','茶',(x,-.14,1.12),.21,pale,left)
right=stand('布摊',2.9,-1.12,2.1,2.5,.85,p)
for j in range(3):
 slab('折叠布匹',(-.6+j*.58,-.06,1.03),.48,.3,[rose,jade,gold][j],right)
 line('布匹折线',[(-.8+j*.58,-.09,.97),(-.4+j*.58,-.09,.97)],pale,right,.013)
bill=receipt('流通纸券',(0,-1.26,4.06),1.25,1.83,p,'交 子',True)
drive(bill,'location',0,tabs[3],'-1+pull*2.5')
txt('便于交易','一纸轻便，买卖相通。',(0,-.75,5.77),.29,wood,p)
for x in [-1.75,1.75]:line('纸带流线',[(x*.65,-.85,4.8),(x,-.85,4.35),(x*1.3,-.85,3.9)],gold,p,.018)
plant('市集银杏',0,(5.42,-.84,2.07),2.65,p)

# 5. The first appearance of the player pair. Five stations and one shared
# table; the drying rack has exactly two visible sheet slots.
p=motions[4]
house('纸艺作坊',1,(.05,-.52,2.08),4.12,p)
slab('作坊匾',(.05,-.64,4.54),1.4,.42,wood,p);txt('作坊文字','交 子 坊',(.05,-.69,4.54),.23,pale,p)
plant('纸院竹',1,(-5.4,-.8,2.06),3.2,p);plant('纸院银杏',0,(5.33,-.78,2.07),3.3,p)
# Small but legible sequential craft stations are part of the illustration.
vat=empty('F05_抄纸槽',(-3.73,-1.00,2.18),p)
slab('纸槽正面',(0,0,.47),1.3,.76,wood,vat);slab('纸浆面',(0,-.04,.81),1.14,.15,jade,vat)
for x in [-.57,.57]:slab('槽沿',(x,-.05,.84),.09,.19,gold,vat)
for j in range(5):line('槽板缝',[(-.5+j*.25,-.035,.18),(-.5+j*.25,-.035,.71)],gold,vat,.008)
wet=empty('抄出湿纸',(-3.73,-1.1,3.3),p)
slab('湿纸',(0,0,0),.72,.52,pale,wet);border('竹帘',0,-.03,0,.86,.65,gold,wet,.035)
drive(wet,'location',2,tabs[4],'2.92+pull*.76')
rack=empty('F06_双槽晾纸架',(-1.79,-.86,2.3),p)
for x in [-.66,.66]:slab('晾架竖杆',(x,0,.85),.05,1.7,wood,rack)
slab('晾架横杆',(0,0,1.7),1.44,.06,wood,rack)
for j in range(2):
 border('晾纸槽_%d'%j,-.33+j*.66,-.045,1.26,.49,.61,sand,rack,.009)
 for x in [-.48+j*.66,-.2+j*.66]:slab('夹纸签',(x,-.09,1.59),.045,.13,gold,rack)
printing=stand('F07_印刷台',.05,-1.06,2.12,1.32,.78,p)
slab('印刷版纹',(0,-.06,.94),.85,.23,ink,printing)
for j in range(5):line('黑版刻线',[(-.32+j*.16,-.085,.85),(-.32+j*.16,-.085,1.03)],gold,printing,.008)
seal=stand('F08_盖印台',1.8,-1.04,2.12,1.32,.78,p)
slab('黑墨票',(0,-.08,.94),.78,.24,ivory,seal);line('墨纹',[(-.25,-.11,.96),(.2,-.11,.96)],ink,seal,.024)
stamp=empty('落朱印',(1.8,-1.16,3.65),p);slab('印章底',(0,0,0),.38,.18,red,stamp);slab('印柄',(0,0,.23),.16,.33,wood,stamp)
for f,z in [(769,3.65),(866,3.65),(888,3.18),(898,3.58),(960,3.58)]:key(stamp,'location',f,(1.8,-1.16,z))
stand('F09_交付台',3.74,-1.0,2.12,1.35,.78,p)
stand('F04_共享台',.05,-.75,3.12,1.2,.51,p)
boy=actor('zhituan_game',0,(-4.9,-1.4,1.98),1.85,p);girl=actor('yintao_game',1,(4.83,-1.4,1.98),1.85,p)
for ob,sgn in [(boy,1),(girl,-1)]:
 for f,a in [(769,0),(810,sgn*.08),(840,0),(888,sgn*.08),(922,0)]:key(ob,'rotation_euler',f,(0,a,0))
# One story sheet travels through every stage. Empty rack outlines show both
# available slots, without inventing a second work-in-progress order.
wet.hide_render=True
sheet=empty('单张纸_完整工序',(-3.73,-1.32,3.3),p)
slab('工序底纸',(0,0,0),.53,.64,pale,sheet)
for f,x,z in [(769,-3.73,2.98),(790,-3.73,3.42),(812,-2.12,3.56),(833,-2.12,3.56),(851,.05,3.16),(865,.05,3.16),(879,1.8,3.16),(901,1.8,3.16),(927,3.74,3.16),(960,3.74,3.16)]:key(sheet,'location',f,(x,-1.32,z))
printed=empty('黑墨状态',p=sheet)
for j in range(5):line('票面墨纹',[(-.18+j*.09,-.04,-.21),(-.18+j*.09,-.04,.21)],printink,printed,.011)
for f,sc in [(769,.0001),(850,.0001),(865,1),(960,1)]:key(printed,'scale',f,(sc,sc,sc))
sealmark=slab('朱印状态',(.14,-.06,-.19),.14,.14,red,sheet)
for f,sc in [(769,.0001),(887,.0001),(890,1),(960,1)]:key(sealmark,'scale',f,(sc,sc,sc))
for x,body in [(-3.73,'抄纸'),(-1.79,'晾干'),(.05,'印刷'),(1.8,'盖印'),(3.74,'交付')]:txt('工序字',body,(x,-1.28,1.89),.17,wood,p)

# 6. Only now is the character-pair game banknote revealed.
p=motions[5]
house('开张作坊',1,(.05,-.50,2.07),4.12,p)
plant('金色纸树',0,(-5.1,-.80,2.08),3.7,p);plant('淡墨竹叶',1,(5.1,-.80,2.08),3.1,p)
lantern('开张灯',-2.5,-.75,4.96,p);lantern('开张灯',2.5,-.75,4.96,p)
ticket=empty('首张双人组合交子',(0,-1.28,2.42),p)
cutout('组合票面','组合交子_纸团印桃_引用_v01.png',(0,0,1,1),(0,0,0),2.8,ticket)
drive(ticket,'location',2,tabs[5],'2.05+pull*.60')
actor('zhituan_final',0,(-2.63,-1.40,2.02),2.55,p);actor('yintao_final',1,(2.63,-1.40,2.02),2.55,p)
stand('交付柜台',0,-1.17,2.04,2.28,.34,p)
txt('游戏正式标题','交子赶工记',(0,-1.18,5.87),.61,wood,p)
for x in [-4.1,4.1]:
 for j in range(3):leaf('纸页小花',x+j*.12,-1.15,2.15,.24,.45+j*.17,[gold,sage,rose][j],p)

# All chapter geometry was appended after the text skeleton: now assign the
# same discrete visibility interval to each entire subtree.
for i,chapter in enumerate(chapters):vis_tree(chapter,i*192+1,(i+1)*192 if i==5 else i*192+166)
# The sieve remains at the vat; the sheet above is the only travelling item.
wet.animation_data_clear()
wet.location=(-3.73,-1.08,3.12)
drive(wet,'location',2,tabs[4],'3.0+pull*.22')
for child in wet.children:
 if child.name.startswith('湿纸'):
  child.animation_data_clear();child.hide_render=True

# A real sheet turns about the binding (vertical Z). The sheet's front and
# back ornaments make the direction legible; there are never radial sectors.
for i in range(5):
 start=i*192+165;end=(i+1)*192
 hinge=empty('TURNING_LEAF_%02d'%i,p=book)
 page_mesh('翻动纸页',1,-.20,paper,hinge,.045)
 for y in [-.43,.02]:
  border('翻页细框',3.25,y,3.93,5.91,6.60,gold,hinge,.012)
  disk('页上印花',(3.25,y,3.95),.75,sand,hinge)
  for j in range(12):
   a=j*math.tau/12;leaf('纸页花纹',3.25+math.sin(a)*.5,y-.008,3.95+math.cos(a)*.5,.16,.29,ivory,hinge)
 # At mid-turn it projects toward the camera, then rests on the left stack.
 for f,a in [(start,0),(start+6,-.12),(start+18,-math.pi*.54),(end,-math.pi)]:key(hinge,'rotation_euler',f,(0,0,a))
 vis_tree(hinge,start,end)

# Printed text needs stronger pigment than scenery under the soft studio lights.
for ob in S.objects:
 if ob.type=='FONT':
  current=ob.data.materials[0] if ob.data.materials else None
  ob.data.materials.clear();ob.data.materials.append(whiteink if current==pale else printred if current==red else printink)
  ob.data.bevel_depth=.0015;ob.data.bevel_resolution=0

# v05: the volume lies open on the table. Pages are the ground; the scenery
# stands independently above it. Existing artwork is kept as thin paper cuts.
# Each element has its own bottom hinge, so it folds onto its own page.
popup_hinges=[]
# A tangible title placard above the final scene, supported by folded poles.
for ob in motions[5].children:
 if ob.name.startswith('游戏正式标题'):ob.location=(0,-.9,6.5)
crest=empty('终章折纸题匾',(0,-.86,2.0),motions[5])
slab('标题纸匾',(0,0,4.5),4.75,.85,pale,crest)
border('题匾描边',0,-.025,4.5,4.57,.69,gold,crest,.014)
for side in [-1,1]:
 slab('题匾支杆',(side*2.12,.05,2.22),.055,4.44,wood,crest)
vis_tree(crest,961,1152)
for i,art in enumerate(motions):
 start=i*192+1;S.frame_set(start+89);bpy.context.view_layer.update()
 items=list(art.children)
 art_matrix_inv=art.matrix_world.inverted()
 for item in items:
  # Explanatory labels are printed on the page in the new arrangement; they
  # should not float in mid-air as independent text silhouettes.
  if item.type=='FONT' and not item.name.startswith(('游戏正式标题','官署匾文','铺户牌匾字','作坊文字')):
   item.animation_data_clear();item.hide_render=True;continue
  subitems=[item]+list(item.children_recursive)
  points=[]
  for ob in subitems:
   if ob.type in {'MESH','CURVE','FONT'} and not ob.hide_render:
    points.extend([art_matrix_inv @ ob.matrix_world @ Vector(v) for v in ob.bound_box])
  if not points:continue
  xmin=min(v.x for v in points);xmax=max(v.x for v in points)
  ymin=min(v.y for v in points);ymax=max(v.y for v in points)
  zmin=min(v.z for v in points);zmax=max(v.z for v in points)
  cx=(xmin+xmax)/2;cy=(ymin+ymax)/2
  # Separate the front, middle, and back layers without thickening the paper.
  base_z=zmin
  if item.name.startswith(('可移动凭券','民间凭券','官发纸币','流通纸券','F04_共享台')):base_z=2.05
  elif item.name.startswith('首张双人组合交子'):base_z=2.34
  # Even a high sun/cloud folds about the paper ground, rather than hovering
  # at its old height when horizontal. Height translation for the receipt
  # cards remains separate from that floor-level hinge.
  anchor_z=2.05
  hinge=empty('POPUP_%02d_%s'%(i,item.name),(cx,cy*3,anchor_z),art)
  item.parent=hinge;item.delta_location=Vector(item.delta_location)-Vector((cx,cy,anchor_z+zmin-base_z))
  angle=math.pi/2 if cy*3+3>.20 else -math.pi/2
  for f,a in [(start,angle),(start+12,angle*.72),(start+46,0),(start+145,0),(start+164,angle),(start+191,angle)]:
   if i==5 and f>start+145:a=0
   key(hinge,'rotation_euler',f,(a,0,0))
  popup_hinges.append(hinge)
  # Paper engineering support: a small triangular folded gusset behind each
  # substantial upright card. Geometry shares the card's fold animation.
  if zmax-zmin>.8 and xmax-xmin>.45 and item.type!='FONT':
   support=polygon('V折纸撑',[(0,.02,.015),(0,.42,.015),(0,.02,min(.55,(zmax-zmin)*.3))],ivory,hinge,.012)
   shown(support,start,(i+1)*192 if i==5 else start+165)
 art.animation_data_clear();art.scale=(1,1,1);art.parent=None;art.location=(0,3,-1.24)

# Reorient just the bound volume and its printed matter, not the upright cuts.
book.rotation_euler.x=-math.pi/2;book.location=(0,-3.95,.65)
for i,chapter in enumerate(chapters):
 for ob in chapter.children:
  if ob.type=='FONT' and ob.name.startswith('章节标题'):ob.location.z=1.68;ob.location.y=-.24;ob.data.size=.29
  elif ob.type=='FONT' and ob.name.startswith('右页小题'):ob.location.z=1.68;ob.location.y=-.24;ob.data.size=.19
  elif ob.type=='FONT' and ob.name.startswith('故事文字'):ob.location.y=-.20;ob.data.size=.36
  elif ob.name.startswith('故事纸条'):ob.location.y=-.12
  elif ob.name.startswith('纸条折角'):
   for v in ob.data.vertices:v.co.y=(v.co.y+.54)/3-.12
old_ribbon=bpy.data.objects.get('朱红书签');old_ribbon.hide_render=True
polygon('前缘书签',[(.13,-2.9,.66),(.37,-2.9,.66),(.37,-3.75,.40),(.37,-3.86,.12),(.25,-3.84,.22),(.13,-3.86,.12),(.13,-3.75,.40)],red,None,.02)

# Printed paths and collage fragments give the page a real ground plane.
# Each is tied to the currently visible chapter; no extra scene or room exists.
for i in range(6):
 floor=empty('PAGE_GROUND_%02d'%i)
 # Fine paired-page paved street, with a narrow visible binding gutter.
 for side in [-1,1]:
  for row in range(5):
   for col in range(5):
    x=side*(.50+col*1.08);y=-1.65+row*.88
    line('地面印线',[(x-.41,y-.32,.76),(x+.41,y-.32,.76),(x+.41,y+.32,.76),(x-.41,y+.32,.76),(x-.41,y-.32,.76)],sand,floor,.004)
  line('纸页地面镶线',[(side*.32,-1.98,.80),(side*6.03,-1.98,.80),(side*6.03,3.15,.80)],gold,floor,.012)
 if i==0:
  line('钱车纸路',[(x*.33,-.48+.13*math.sin(x*.5),.75) for x in range(-14,13)],sand,floor,.09)
 elif i==3:
  for side in [-1,1]:polygon('街市织物地垫',[(side*1.4,-.9,.75),(side*4.3,-.9,.75),(side*4.3,.75,.75),(side*1.4,.75,.75)],sage if side<0 else rose,floor,.012)
 elif i in [4,5]:
  polygon('院中纸水渠',[(-5.6,-1.55,.75),(-4.8,-1.55,.75),(-4.4,2.9,.75),(-5.3,2.9,.75)],jade,floor,.015)
  for j in range(4):line('水渠细纹',[(-5.4+j*.13,-1.4,.78),(-5.05+j*.13,2.7,.78)],pale,floor,.009)
 # Rear corner scraps reinforce the handcrafted look without confetti noise.
 for side in [-1,1]:
  for j in range(3):
   x=side*(5.55+j*.15);y=2.7-j*.25
   polygon('剪纸落叶',[(x-.09,y,.73),(x,y+.21,.74),(x+.09,y,.73),(x,y-.13,.73)],gold if j%2 else sage,floor,.012)
 vis_tree(floor,i*192+1,(i+1)*192 if i==5 else i*192+166)

# Wooden tabletop rather than a blank display-board background.
tablemat=mat('胡桃暖木桌',(.22,.080,.025))
nodes=tablemat.node_tree.nodes;links=tablemat.node_tree.links
coord=nodes.new('ShaderNodeTexCoord');grain=nodes.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=3;grain.inputs['Detail'].default_value=2
stretch=nodes.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(5,180,4)
links.new(coord.outputs['Generated'],stretch.inputs[0]);links.new(stretch.outputs[0],grain.inputs['Vector'])
ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(.14,.044,.012,1);ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(.26,.098,.032,1)
links.new(grain.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],nodes.get('Principled BSDF').inputs['Base Color'])
table=bpy.data.objects.get('暖木桌面');table.data.materials.clear();table.data.materials.append(tablemat)
for j in range(-8,9):line('木桌板缝',[(-40,j*2.15,-.008),(40,j*2.15,-.008)],wood,None,.009)

def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Book story camera');cam=bpy.data.objects.new('Book story camera',d);S.collection.objects.link(cam);S.camera=cam
d.type='ORTHO';d.ortho_scale=15.80;cam.location=(.35,-23,17.5);aim(cam,(0,-.10,1.35))
# Keep a large hold view, then make room for the real raised leaf during turns.
for i in range(6):
 start=1+i*192
 for f,target,scale in [(start,(0,-.10,1.35),15.8),(start+145,(0,-.10,1.35),15.8)]:
  aim(cam,target);cam.keyframe_insert('rotation_euler',frame=f);d.ortho_scale=scale;d.keyframe_insert('ortho_scale',frame=f)
 if i<5:
  for f,target,scale in [(start+173,(0,1.1,2.15),24.2),(start+184,(0,1.1,2.15),24.2),(start+191,(0,-.1,1.35),15.8)]:
   aim(cam,target);cam.keyframe_insert('rotation_euler',frame=f);d.ortho_scale=scale;d.keyframe_insert('ortho_scale',frame=f)
for name,loc,power,size,c in [('柔暖主光',(-7,-12,14),2100,8,(1,.82,.60)),('纸面补光',(8,-9,9),1700,10,(1,.91,.75)),('书页边缘光',(0,4,13),2100,8,(1,.75,.46))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=c;o=bpy.data.objects.new(name,d);S.collection.objects.link(o);o.location=loc;aim(o,(0,0,3.9))
audio=A/'开场配乐与纸声_v05.wav'
if audio.exists():S.sequence_editor_create().strips.new_sound('原创拨弦与翻纸',str(audio),1,1)
for i,name in enumerate(titles):S.timeline_markers.new(name,frame=1+i*192)
S['task_id']='F01-opening';S['version']='v05_20261111';S['form']='horizontal open two-page book on wooden table; upright folding paper scenery; five leaf turns and six automatic mechanisms'
S['history_boundary']='Chapters 1-3 historical inspiration; chapter 4 transitions to fiction; chapter 5-6 game characters and pair bill'
S['status']='Blender media source; Unity integration untested'
S.eevee.taa_render_samples=32;S.eevee.shadow_ray_count=1
S.render.filepath=str(W/'frames_final'/'frame_');(W/'frames_final').mkdir(exist_ok=True)
S.frame_set(1060)
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'开场纸书_v05_20261111.blend'))
report={'version':'v05_20261111','blender':bpy.app.version_string,'fps':24,'frames':1152,'seconds':48,'resolution':[1920,1080],'engine':S.render.engine,'objects':len(S.objects),'turning_leaves':5,'pull_tabs':6,'popup_hinges':len(popup_hinges),'chapters':6,'packed_images':[(im.name,bool(im.packed_file)) for im in bpy.data.images if im.source=='FILE'],'form':S['form'],'captions':captions,'character_medium':'flat textured cut-paper silhouette meshes, not skeletal character models'}
(OUT/'制作核验_v05.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if '--preview' in sys.argv:
 S.render.resolution_percentage=65
 for f in [20,90,155,180,183,200,285,475,665,860,1060]:
  S.frame_set(f);S.render.filepath=str(W/('preview_%04d.png'%f));bpy.ops.render.render(write_still=True)
print('BOOK_BUILD_OK',len(S.objects))



