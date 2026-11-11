"""Quiet, non-interactive papercraft furnishing for level 01.

The six production stations keep the strongest silhouettes and colour accents.
All floor furnishing is outside the y=3.3..5.7 circulation band.  Declared
footprints are world-aligned, including the rotated right-side cabinet.
"""

from math import pi, sin, cos


def _root(api, name, loc, footprint=None):
    ob = api.empty(name, loc)
    ob["asset_id"] = name
    ob["role"] = "decorative_prop"
    ob["non_interactive"] = True
    ob["task"] = "F15"
    ob["version"] = "v05_20261111"
    if footprint is not None:
        ob["footprint"] = list(footprint)
    return ob


def _paper(api, name, loc, width, depth, parent, mat="paper_edge", curl=.018):
    """A slightly curled six-corner sheet with visible paper thickness."""
    x,y,z=loc
    outline=[(-width/2,-depth/2), (width/2-.05,-depth/2),
             (width/2,-depth/2+.05), (width/2,depth/2),
             (-width/2,depth/2), (-width/2,-depth/2)]
    top=[(x+a,y+b,z+(curl if i==2 else 0)) for i,(a,b) in enumerate(outline[:-1])]
    n=len(top)
    verts=top+[(a,b,c-.006) for a,b,c in top]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    api.mesh(name,verts,faces,mat,parent=parent)
    return top


def _stack(api,name,loc,parent,w=.35,d=.28,count=5):
    x,y,z=loc
    for i in range(count):
        _paper(api,f"{name}_sheet_{i}",
               (x+(.003 if i%2 else -.003),y,z+.008*i),w,d,parent,
               "paper" if i==count-1 else "paper_edge", curl=.007 if i<count-1 else .018)
    # A shallow fold crease makes the top feel like worked paper, not a slab.
    api.line(name+"_crease",[(x-w*.40,y-d*.20,z+.008*(count-1)+.002),
             (x+w*.30,y+d*.26,z+.008*(count-1)+.003)],
             "paper_edge",radius=.0013,parent=parent)


def _roll(api,name,loc,parent,r=.075,length=.34):
    """Paper roll on its side, with an exposed spiral end facing the camera."""
    x,y,z=loc
    api.cyl(name+"_body",loc,r,length,"paper_edge",parent=parent,
            vertices=16,rotation=(pi/2,0,0))
    # A lighter, thin end cap reveals wound layers; no coloured workflow marker.
    api.cyl(name+"_end",(x,y-length/2-.001,z),r-.002,.002,"paper",parent=parent,
            vertices=16,rotation=(pi/2,0,0))
    pts=[]
    for k in range(84):
        t=k/83
        rr=.012+(r-.015)*t
        angle=pi*5.2*t
        pts.append((x+rr*cos(angle),y-length/2-.0025,z+rr*sin(angle)))
    api.line(name+"_visible_spiral",pts,"paper_edge",radius=.0021,parent=parent)
    api.cyl(name+"_core",(x,y-length/2-.003,z),.009,.003,"wood_dark",parent=parent,
            vertices=10,rotation=(pi/2,0,0))
    # A narrow neutral paper belt binds the roll around its middle.
    api.cyl(name+"_binding",(x,y+.018,z),r+.0015,.025,"paper_edge",parent=parent,
            vertices=16,rotation=(pi/2,0,0))


def _cabinet(api,name,loc,width,depth,height,rotation=0):
    footprint=(width,depth) if not rotation else (depth,width)
    root=_root(api,name,loc,footprint)
    root.rotation_euler.z=rotation
    root["visual_category"]="closed_storage_furniture"
    # Framed closed panels distinguish storage from the open production tables.
    # Stop below the cap: coincident top faces cause black patches in Cycles.
    api.box(name+"_case",(0,0,(height+.05)/2),(width-.045,depth-.035,height-.15),
            "wood_dark",parent=root,bevel=.016)
    api.box(name+"_top_folded_edge",(0,0,height-.026),(width,depth,.052),
            "wood",parent=root,bevel=.018)
    for sx in (-1,1):
        for sy in (-1,1):
            api.box(name+f"_foot_{sx}_{sy}",
                    (sx*(width/2-.075),sy*(depth/2-.065),.075),(.085,.085,.15),
                    "wood_dark",parent=root,bevel=.009)
    yfront=-depth/2+.010
    api.box(name+"_upper_drawer",(0,yfront,height-.145),
            (width-.14,.025,.145),"paper_edge",parent=root,bevel=.008)
    door_h=height-.34
    door_w=(width-.17)/2
    for side in (-1,1):
        xx=side*(door_w/2+.012)
        api.box(name+f"_door_{side}",(xx,yfront,.15+door_h/2),
                (door_w,.025,door_h),"wood",parent=root,bevel=.008)
        api.box(name+f"_inset_{side}",(xx,yfront-.007,.15+door_h/2),
                (door_w-.055,.007,door_h-.055),"paper_edge",parent=root,bevel=.004)
        api.cyl(name+f"_pull_{side}",(side*.065,yfront-.005,.15+door_h*.7),
                .018,.014,"metal",parent=root,vertices=8,rotation=(pi/2,0,0))
    api.cyl(name+"_drawer_pull",(0,yfront-.005,height-.145),.018,.014,
            "metal",parent=root,vertices=8,rotation=(pi/2,0,0))
    # Muted mitred paper corner reinforcements, not bright metal hardware.
    for side in (-1,1):
        xx=side*(width/2-.035)
        verts=[(xx,yfront-.012,height-.058),
               (xx-side*.09,yfront-.012,height-.058),
               (xx,yfront-.012,height-.14)]
        api.mesh(name+f"_paper_corner_{side}",verts,[(0,1,2)],"wood_light",parent=root)
    return root


def _basket(api):
    root=_root(api,"decor_woven_paper_basket",(.66,1.00,0),(.64,.64))
    root["visual_category"]="basket_of_scrap_paper"
    sides=12
    vertices=[]
    for rad,z in [(.225,.025),(.285,.35),(.265,.35),(.208,.045)]:
        vertices.extend((rad*cos(2*pi*i/sides),rad*sin(2*pi*i/sides),z) for i in range(sides))
    faces=[]
    for i in range(sides):
        j=(i+1)%sides
        faces.extend([(i,j,sides+j,sides+i),
                      (sides+i,sides+j,2*sides+j,2*sides+i),
                      (2*sides+i,2*sides+j,3*sides+j,3*sides+i)])
    faces.append(tuple(range(3*sides,4*sides)))
    api.mesh("basket_open_woven_body",vertices,faces,"paper_edge",parent=root)
    for k,z in enumerate((.12,.23,.35)):
        r=.225+(.285-.225)*(z-.025)/.325
        pts=[(r*cos(2*pi*i/sides),r*sin(2*pi*i/sides),z) for i in range(sides+1)]
        api.line(f"basket_horizontal_weave_{k}",pts,"wood",radius=.008,parent=root)
    # Sparse vertical bamboo ribbons, a single geometry object.
    verts,fs=[],[]
    for i in range(sides):
        t=2*pi*i/sides
        for z,r in ((.04,.230),(.335,.283)):
            for dt in (-.023,.023):
                verts.append((r*cos(t+dt),r*sin(t+dt),z))
        b=i*4
        fs.append((b,b+1,b+3,b+2))
    api.mesh("basket_vertical_weave",verts,fs,"wood_light",parent=root)
    # Bent sheets stay inside the basket footprint, with readable layers.
    for i,(xx,yy,zz) in enumerate([(-.075,.025,.26),(.045,-.035,.275),(.025,.04,.29)]):
        _paper(api,f"basket_scrap_{i}",(xx,yy,zz),.23,.20,root,
               "paper_edge" if i<2 else "paper",curl=.075)
    return root


def _plant(api,parent,loc):
    x,y,z=loc
    api.cyl("cabinet_plant_pot",loc,.090,.13,"stone",parent=parent,vertices=8)
    api.cyl("cabinet_plant_pot_rim",(x,y,z+.058),.102,.025,"paper_edge",
            parent=parent,vertices=8)
    api.cyl("cabinet_plant_soil",(x,y,z+.073),.084,.012,"wood_dark",parent=parent,vertices=8)
    # Each broad leaf is folded down its spine; muted wet-paper material.
    for i in range(6):
        angle=i*pi/3+.2
        spread=.10 if i%2 else .14
        h=.22 if i%2 else .17
        base=(x,y,z+.075)
        tip=(x+spread*cos(angle),y+spread*sin(angle),z+.075+h)
        mid=(x+spread*.5*cos(angle),y+spread*.5*sin(angle),z+.075+h*.65)
        lateral=(-sin(angle)*.042,cos(angle)*.042,0)
        left=(mid[0]+lateral[0],mid[1]+lateral[1],mid[2]-.018)
        right=(mid[0]-lateral[0],mid[1]-lateral[1],mid[2]-.018)
        api.mesh(f"plant_folded_leaf_{i}",[base,left,tip,right,mid],
                 [(0,1,4),(1,2,4),(2,3,4),(3,0,4)],"wet",parent=parent)


def _wall_notice(api):
    root=_root(api,"decor_wall_notice",(.86,7.775,1.72))
    root["visual_category"]="wall_mounted_paper_notice"
    api.box("notice_backboard",(0,0,0),(.64,.025,.48),
            "wood_dark",parent=root,bevel=.01)
    for sx in (-1,1):
        api.box(f"notice_wall_mount_{sx}",(sx*.20,.045,0),(.055,.10,.25),
                "wood_dark",parent=root,bevel=.004)
    # Paper notice planes have a lifted lower corner rather than a rigid block.
    for i,(xx,zz,w,h) in enumerate([(-.11,.045,.25,.31),(.15,-.05,.22,.26)]):
        vertices=[(xx-w/2,-.018,zz+h/2),(xx+w/2,-.018,zz+h/2),
                  (xx+w/2,-.043,zz-h/2),(xx-w/2,-.018,zz-h/2)]
        api.mesh(f"notice_sheet_{i}",vertices,[(0,3,2,1)],"paper_edge",parent=root)
        api.cyl(f"notice_pin_{i}",(xx,-.025,zz+h*.38),.012,.016,
                "wood",parent=root,vertices=8,rotation=(pi/2,0,0))
        # Faint short rules, no new gameplay instruction or bright title.
        for row in range(3):
            api.line(f"notice_ink_rule_{i}_{row}",
                     [(xx-w*.29,-.027,zz+.055-row*.045),
                      (xx+w*(.20 if row==2 else .30),-.027,zz+.055-row*.045)],
                     "wood_dark",radius=.0015,parent=root)
    return root


def _tool_rack(api):
    root=_root(api,"decor_wall_tool_rack",(3.98,7.765,1.47))
    root["visual_category"]="wall_mounted_tools"
    api.box("tool_rack_rail",(0,0,.12),(.82,.045,.09),"wood_dark",parent=root,bevel=.009)
    for sx in (-1,1):
        api.box(f"tool_rack_wall_mount_{sx}",(sx*.27,.045,.12),(.06,.10,.08),
                "wood_dark",parent=root,bevel=.004)
    for i,xx in enumerate((-.25,0,.25)):
        api.cyl(f"tool_hook_{i}",(xx,-.05,.12),.018,.09,"wood",parent=root,
                vertices=8,rotation=(pi/2,0,0))
        api.box(f"tool_handle_{i}",(xx,-.085,-.035),(.024,.023,.27),
                "wood",parent=root,bevel=.003)
        if i==0:
            # Broad thin bamboo spatula, intentionally unlike the active tools.
            api.box("tool_bamboo_scraper",(xx,-.085,-.21),(.09,.018,.13),
                    "wood_light",parent=root,bevel=.008)
        else:
            api.box(f"tool_brush_binding_{i}",(xx,-.085,-.16),(.047,.036,.035),
                    "paper_edge",parent=root,bevel=.004)
            api.box(f"tool_brush_head_{i}",(xx,-.085,-.215),(.058,.025,.09),
                    "wood_dark",parent=root,bevel=.007)
    return root


def build_decoration(api,spec):
    """Return five deliberately non-interactive furnishing roots."""
    if tuple(spec["base"]["floor"])!=(12,8):
        raise ValueError("Decoration v02 expects the 12 x 8 m level 01 layout")
    api.collection("DECOR_01_Quiet_Storage")
    roots=[]
    back=_cabinet(api,"decor_rear_storage_cabinet",(3.95,7.35,0),1.2,.55,.62)
    back["placement_note"]="Right edge 4.55 m; clear of rear portal and drying rack"
    _stack(api,"rear_cabinet_paper_stack",(-.30,.02,.64),back,w=.34,d=.29,count=6)
    _roll(api,"rear_cabinet_roll_A",(.17,.005,.702),back,r=.075,length=.35)
    _roll(api,"rear_cabinet_roll_B",(.36,.005,.695),back,r=.068,length=.31)
    roots.append(back)
    right=_cabinet(api,"decor_right_low_cabinet",(11.40,1.00,0),1.3,.55,.55,rotation=pi/2)
    right["placement_note"]="World footprint .55 x 1.30; outside main lane and stamping station"
    _stack(api,"right_cabinet_used_paper",(-.34,.015,.57),right,w=.35,d=.27,count=4)
    _plant(api,right,(.36,0,.63))
    roots.append(right)
    roots.append(_basket(api))
    api.collection("DECOR_02_Wall_Details")
    roots.append(_wall_notice(api))
    roots.append(_tool_rack(api))
    return roots
