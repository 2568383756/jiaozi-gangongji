"""First-level papercraft architecture, metre scale, Blender XY floor / Z up.

This builder uses only the narrow API passed by the scene assembly script.  It
does not clear the scene, save files, configure a renderer, or run on import.
The two workshop zones have no divider.  Length-adjusted wall ends close the
2 m modular grid around the separately specified 2.8 m rear portal.
"""

from math import pi, sin, cos


def _tag(obj, asset, dimensions, role="environment"):
    obj["asset_id"] = asset
    obj["task"] = "F15"
    obj["role"] = role
    obj["width"], obj["depth"], obj["height"] = dimensions
    obj["units"] = "m"
    return obj


def _cuboids(api, name, parts, mat, parent):
    """Batch disconnected straight details into one editable mesh."""
    vertices, faces = [], []
    for loc, size in parts:
        x, y, z = loc
        a, b, c = (v * 0.5 for v in size)
        start = len(vertices)
        vertices.extend([(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),
                         (x-a,y+b,z-c),(x-a,y-b,z+c),(x+a,y-b,z+c),
                         (x+a,y+b,z+c),(x-a,y+b,z+c)])
        faces.extend(tuple(start+i for i in f) for f in
                     [(0,3,2,1),(4,5,6,7),(0,1,5,4),
                      (1,2,6,5),(2,3,7,6),(3,0,4,7)])
    return api.mesh(name, vertices, faces, mat, parent=parent)


def _profile(api, name, outline, front, back, material, parent):
    """A thin cut-paper silhouette extruded along Y; outline is local X/Z."""
    n = len(outline)
    area=sum(outline[i][0]*outline[(i+1)%n][1]-
             outline[(i+1)%n][0]*outline[i][1] for i in range(n))
    if area < 0:
        outline=list(reversed(outline))
    vertices = [(x,y,z) for y in (front,back) for x,z in outline]
    faces = [tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces += [(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    return api.mesh(name,vertices,faces,material,parent=parent)


def _key_bars(points, thickness=.025, y=-.095, depth=.026):
    """Turn right-angle lattice strokes into batchable rectangular sticks."""
    parts=[]
    for a,b in zip(points,points[1:]):
        parts.append((((a[0]+b[0])/2,y,(a[1]+b[1])/2),
                      (abs(b[0]-a[0])+thickness,depth,
                       abs(b[1]-a[1])+thickness)))
    return parts


def _tiles(api, name, width, depth, height, parent, z0=0):
    """Closed low-poly paper-tile strips, all pieces in a single mesh.

    Their front-to-back incline and six-sided arc are geometry, not normal-map
    decoration.  All vertices stay within the declared strip bounding box.
    """
    vertices, faces = [], []
    count = max(2, round(width / .24))
    step = width / count
    # The underside meets the supporting beam at the front edge; it must not
    # sink through that beam and create coincident outer faces on low walls.
    thickness = min(.025, height * .20)
    for tile in range(count):
        offset = len(vertices)
        center = -width/2 + (tile+.5)*step
        for underside in (False, True):
            for back in (False, True):
                yy = depth/2 if back else -depth/2
                zz = height*.65 if back else height*.20
                for k in range(7):
                    xx = center - step/2 + step*k/6
                    zz1 = z0 + zz + height*.35*sin(pi*k/6)
                    if underside:
                        zz1 -= thickness
                    vertices.append((xx, yy, zz1))
        for k in range(6):
            faces.append((offset+k,offset+k+1,offset+8+k,offset+7+k))
            faces.append((offset+14+k,offset+21+k,offset+22+k,offset+15+k))
            faces.append((offset+k,offset+14+k,offset+15+k,offset+k+1))
            faces.append((offset+7+k,offset+8+k,offset+22+k,offset+21+k))
        faces.extend([(offset,offset+7,offset+21,offset+14),
                      (offset+6,offset+20,offset+27,offset+13)])
    return api.mesh(name, vertices, faces, "roof", parent=parent)


def _floor(api, ix, iy):
    yard = ix < 3
    kind = "env_floor_courtyard" if yard else "env_floor_workshop"
    root = _tag(api.empty(f"{kind}_{ix:02d}_{iy:02d}",
                          (ix*2+1, iy*2+1, 0)), kind, (2,2,.1))
    api.box(root.name+"_slab", (0,0,-.05), (2,2,.1),
            "floor_courtyard" if yard else "floor_workshop", parent=root, bevel=.012)
    seams = []
    if yard:
        # Deliberately broad paving: three rows, no gravel/noise clutter.
        for yy in (-.333, .333):
            seams.append(((0,yy,.0008),(1.975,.004,.0015)))
        for row, yy in enumerate((-.666,0,.666)):
            offsets = (-.50,.48) if (ix+iy+row)%2 else (-.28,.68)
            for xx in offsets:
                seams.append(((xx,yy,.0008),(.004,.658,.0015)))
    else:
        for yy in (-.60,-.20,.20,.60):
            seams.append(((0,yy,.0008),(1.975,.004,.0015)))
        for row in range(5):
            xx = -.50 if (row+ix+iy)%2 else .50
            seams.append(((xx,-.80+row*.4,.0008),(.004,.390,.0015)))
    _cuboids(api,root.name+"_joints",seams,
             "paper_edge", root)
    return root


def _wall(api, name, center, width, height, angle=0, window=False, low=False):
    kind = "env_wall_low" if low else (
        "env_wall_window" if window else "env_wall_plain")
    root = _tag(api.empty(name, center), kind, (width,.2,height))
    root.rotation_euler.z = angle
    root["nominal_module_width"] = 2.0
    root["length_variant"] = abs(width-2.0) > .001
    coping = .08 if low else 0
    top = height-coping
    base_h = min(.14, top*.28)
    post_w=min(.11,width*.36)
    beam_h=.11
    post_top=top-beam_h
    # The paper enters the timber rebate by 6-8 mm. Its end/top planes are
    # fully inside the frame, never coplanar with an exposed timber surface.
    paper_bottom=base_h-.006
    paper_top=post_top+.008
    api.box(name+"_paper_panel", (0,0,(paper_bottom+paper_top)/2),
            (width-2*post_w+.012,.115,paper_top-paper_bottom),
            "paper", parent=root, bevel=.013)
    api.box(name+"_stone_foot", (0,0,base_h/2), (width,.2,base_h),
            "stone", parent=root, bevel=.012)
    # Posts stop at the lintel underside instead of intersecting it. The
    # short 0.2 m wall filler also uses narrower posts, avoiding post overlap.
    frame = [((-width/2+post_w/2,0,(base_h+post_top)/2),
              (post_w,.2,post_top-base_h)),
             (( width/2-post_w/2,0,(base_h+post_top)/2),
              (post_w,.2,post_top-base_h)),
             ((0,0,top-beam_h/2),(width,.2,beam_h))]
    _cuboids(api,name+"_timber_frame",frame,"wood",root)
    if low:
        _tiles(api,name+"_tile_coping",width,.20,.08,root,z0=height-.08)
    elif window and width >= 1.1:
        ww = min(1.55,width-.34)
        wh, wz = .86, 1.64
        root["window_pattern"]="stepped_key_lattice"
        # Warm matte mulberry-paper panes set behind a two-depth timber frame.
        api.box(name+"_window_recess", (0,-.062,wz), (ww+.10,.018,wh+.10),
                "wood_dark",parent=root,bevel=.008)
        api.box(name+"_mulberry_paper_pane",(0,-.075,wz),(ww-.025,.012,wh-.025),
                "paper",parent=root,bevel=.002)
        frames, bars = [], []
        for xx in (-ww/2,ww/2):
            frames.append(((xx,-.092,wz),(.060,.034,wh+.060)))
        for zz in (wz-wh/2,wz+wh/2):
            frames.append(((0,-.092,zz),(ww,.034,.060)))
        # A clear central rectangular opening surrounded by four returning
        # stepped keys (huiwen / bubujin), rather than a generic square grid.
        inner_w,inner_h=ww-.36,wh-.32
        bars += _key_bars([(-inner_w/2,wz-inner_h/2),(inner_w/2,wz-inner_h/2),
                          (inner_w/2,wz+inner_h/2),(-inner_w/2,wz+inner_h/2),
                          (-inner_w/2,wz-inner_h/2)],thickness=.027)
        for sx in (-1,1):
            for sz in (-1,1):
                x=sx*(ww/2-.08);z=wz+sz*(wh/2-.08)
                points=[(x-sx*.24,z),(x,z),(x,z-sz*.22),
                        (x-sx*.115,z-sz*.22),(x-sx*.115,z-sz*.105),
                        (x-sx*.20,z-sz*.105)]
                bars += _key_bars(points,thickness=.025)
        for xx in (-ww*.15,ww*.15):
            bars += _key_bars([(xx,wz-wh/2),(xx,wz-inner_h/2)],.025)
            bars += _key_bars([(xx,wz+inner_h/2),(xx,wz+wh/2)],.025)
        _cuboids(api,name+"_window_moulded_frame",frames,"wood",root)
        _cuboids(api,name+"_window_lattice",bars,"wood_dark",root)
        api.box(name+"_window_sill",(0,-.09,wz-wh/2-.055),
                (ww+.15,.12,.045),"wood_light",parent=root,bevel=.008)
        # Shaped sparrow braces remain attached to the frame and within its
        # actual 0.2 m wall depth, avoiding protrusions into playing space.
        for side in (-1,1):
            x0=side*(width/2-.12)
            outline=[(x0,top-.10),(x0-side*.34,top-.10),
                     (x0-side*.33,top-.15),(x0-side*.23,top-.18),
                     (x0-side*.20,top-.25),(x0-side*.10,top-.29),
                     (x0,top-.40)]
            _profile(api,name+f"_sparrow_brace_{side}",outline,-.095,-.05,"wood",root)
    return root


def _eave(api, name, center, width, angle=0, lift_left=False, lift_right=False):
    """Two overlapping courses of blue paper tiles, thin circular tile ends.

    Only real architectural ends turn upward; seams between adjacent modular
    pieces remain level. The roof remains a narrow wall-attached canopy.
    """
    root = _tag(api.empty(name,center),"env_eave",(width,.70,.67))
    root.rotation_euler.z=angle
    root["nominal_module_width"] = 2.0
    root["length_variant"] = abs(width-2.0) > .001
    root["roof_style"]="double_course_folded_tile_eave"
    root["tile_paper_thickness"] = .018
    count=max(2,round(width/.205))
    step=width/count

    def uplift(x):
        value=0.0
        for enabled,distance in ((lift_left,x+width/2),(lift_right,width/2-x)):
            if enabled:
                value=max(value,.080*max(0,1-distance/.45)**2)
        return value

    vv,ff=[],[]
    courses=[([-.36,-.20,.045],[.13,.18,.315]),
             ([-.025,.145,.34],[.302,.442,.54])]
    for ys,zs in courses:
        for tile in range(count):
            first=len(vv)
            for bottom in (False,True):
                for row in range(3):
                    for column in range(7):
                        x=-width/2+step*(tile+column/6)
                        z=zs[row]+.043*sin(pi*column/6)+uplift(x)
                        vv.append((x,ys[row],z-(.018 if bottom else 0)))
            for row in range(2):
                for col in range(6):
                    a=first+row*7+col
                    ff.append((a,a+1,a+8,a+7))
                    ff.append((a+21,a+28,a+29,a+22))
            for col in range(6):
                a=first+col;b=first+14+col
                ff.append((a,a+21,a+22,a+1))
                ff.append((b,b+1,b+22,b+21))
            for row in range(2):
                a=first+row*7;b=a+6
                ff.append((a,a+7,a+28,a+21))
                ff.append((b,b+21,b+28,b+7))
    api.mesh(name+"_two_courses_blue_paper_tiles",vv,ff,"roof",parent=root)

    # Thin circular wadang end plates are geometry, with a tiny inset boss.
    vv,ff=[],[]
    bosses=[]
    for tile in range(count):
        x=-width/2+step*(tile+.5)
        z=.133+uplift(x)
        first=len(vv);segments=12;radius=min(.062,step*.36)
        for yy in (-.375,-.355):
            vv.extend((x+radius*cos(2*pi*k/segments),yy,
                       z+radius*sin(2*pi*k/segments)) for k in range(segments))
        ff.append(tuple(first+k for k in range(segments)))
        ff.append(tuple(first+segments+k for k in range(segments-1,-1,-1)))
        ff.extend((first+k,first+k+segments,
                   first+(k+1)%segments+segments,first+(k+1)%segments)
                  for k in range(segments))
        # The small dark square is a stamped inset, not a projecting ornament.
        bosses.append(((x,-.376,z),(.027,.004,.027)))
    api.mesh(name+"_round_wadang_paper_ends",vv,ff,"roof",parent=root)
    _cuboids(api,name+"_wadang_impressed_centers",bosses,"teal",root)

    # Side-eave ends formerly coincided with the high wall's end face at
    # world y=6. Recess the supporting timber, keeping the roof silhouette
    # and the nominal module width untouched.
    support_width=width-.024 if abs(angle)>1e-6 else width
    api.box(name+"_lower_timber_beam",(0,.035,.055),(support_width,.23,.11),
            "wood",parent=root,bevel=.012)
    # Exact face-to-face vertical contact; no shared area on the end faces.
    api.box(name+"_upper_timber_beam",(0,.055,.1375),(support_width,.19,.055),
            "wood_light",parent=root,bevel=.006)
    braces=[]
    for i in range(max(2,round(width/.34))):
        xx=-width/2+(i+.5)*width/max(2,round(width/.34))
        braces.append(((xx,-.12,.082),(.065,.43,.045)))
        braces.append(((xx,.025,.015),(.11,.18,.045)))
    _cuboids(api,name+"_exposed_rafters_and_tenon_blocks",braces,"wood_light",root)

    # Raised paper verge only at true end walls. Its curved profile gives the
    # subtle ancient eave silhouette without introducing a closed full roof.
    for side,enabled in ((-1,lift_left),(1,lift_right)):
        if not enabled:
            continue
        vertices=[]
        profile=[(-.38,.225),(-.20,.26),(.02,.40),(.18,.555),(.35,.64)]
        for xx in (side*(width/2-.038),side*(width/2-.004)):
            for y,z in profile:
                vertices.extend([(xx,y,z),(xx,y,z-.042)])
        faces=[]
        for j in range(4):
            a=j*2
            faces += [(a,a+2,a+3,a+1),(a+10,a+11,a+13,a+12),
                      (a,a+10,a+12,a+2),(a+1,a+3,a+13,a+11)]
        faces += [(0,1,11,10),(8,18,19,9)]
        if side < 0:
            faces = [tuple(reversed(face)) for face in faces]
        api.mesh(name+f"_upturned_paper_verge_{side}",vertices,faces,"roof",parent=root)
    return root


def _corner(api,name,center,height,angle):
    """Actual L cross-section; no overlapping two-wall approximation."""
    root=_tag(api.empty(name,center),"env_wall_corner",(.4,.4,height))
    root.rotation_euler.z=angle
    root["wall_thickness"] = .2
    # Default outside faces are left (-X) and back (+Y).
    outline=[(-.2,-.2),(0,-.2),(0,0),(.2,0),(.2,.2),(-.2,.2)]
    def extrusion(suffix,z0,z1,mat,profile=None):
        ring=outline if profile is None else profile
        n=len(ring)
        verts=[(x,y,z) for z in (z0,z1) for x,y in ring]
        faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        return api.mesh(name+suffix,verts,faces,mat,parent=root)
    # Reserve a real 90 x 90 mm corner rebate for the exposed wood stitch.
    # The former full L solid shared both outer planes with the wood strip,
    # producing a long black band from floor to eave in exterior views.
    rebated_outline=[(-.2,-.2),(0,-.2),(0,0),(.2,0),(.2,.2),
                     (-.11,.2),(-.11,.11),(-.2,.11)]
    extrusion("_paper_L",.12,height-.065,"paper",rebated_outline)
    extrusion("_foot_L",0,.12,"stone")
    extrusion("_cap_L",height-.065,height,"roof")
    # Keep the warm outer corner stitch within the L's actual envelope.
    stitch_top=height-.065
    api.box(name+"_vertical_stitch",(-.155,.155,(stitch_top+.12)/2),
            (.09,.09,stitch_top-.12),"wood",parent=root,bevel=.003)
    return root


def _portal(api):
    root = _tag(api.empty("env_portal_rear_attached",(6,7.9,0)),
                "env_portal",(2.8,.2,2.4))
    root["clear_width"], root["clear_height"] = 2.4,2.1
    for side in (-1,1):
        api.box(f"portal_post_{side}",(side*1.3,0,1.2),(.2,.2,2.4),
                "wood",parent=root,bevel=.012)
        # Stone aprons project in Y and retreat 2 mm in X, so no face shares
        # the timber post's planes. The door's X clearance remains unchanged.
        api.box(f"portal_foot_{side}",(side*1.3,0,.08),(.196,.216,.16),
                "stone",parent=root,bevel=.010)
    api.box("portal_header",(0,0,2.25),(2.8,.2,.3),
            "wood_light",parent=root,bevel=.015)
    root["portal_style"]="attached_paper_mill_plaque_gate"
    # All shoulders below z=2.1 point OUTWARD from the door posts. The required
    # 2.4 x 2.1 m opening therefore remains physically empty, including its top.
    for side in (-1,1):
        x=side*1.3
        outline=[(x,2.37),(x+side*.44,2.37),(x+side*.43,2.29),
                 (x+side*.34,2.26),(x+side*.30,2.18),(x+side*.18,2.14),
                 (x+side*.12,2.04),(x,1.99)]
        _profile(api,f"portal_outward_sparrow_brace_{side}",outline,
                 -.135,-.085,"wood",root)
        api.box(f"portal_visible_tenon_{side}",(side*1.32,-.12,2.285),
                (.10,.040,.09),"wood_dark",parent=root,bevel=.006)
    api.box("portal_stacked_architrave",(0,.005,2.405),(2.8,.255,.055),
            "wood",parent=root,bevel=.008)
    _cuboids(api,"portal_plaque_hangers",
             [((x,-.22,2.37),(.065,.27,.075)) for x in (-.78,.78)],"wood",root)

    # A shaped, restrained dark timber tablet is attached to the beam; it is
    # high enough to keep the actual door clear and reads from the play camera.
    plaque=[(-1.04,2.16),(-.98,2.115),(.98,2.115),(1.04,2.16),
            (1.04,2.48),(.98,2.525),(-.98,2.525),(-1.04,2.48)]
    _profile(api,"portal_jiaozi_fang_tablet",plaque,-.405,-.34,"wood",root)
    inner=[(-.94,2.17),(.94,2.17),(.97,2.20),(.97,2.46),
           (.94,2.49),(-.94,2.49),(-.97,2.46),(-.97,2.20)]
    _profile(api,"portal_tablet_recessed_field",inner,-.414,-.404,"wood_dark",root)
    border=[]
    for sx in (-1,1):
        for sz in (-1,1):
            xx=sx*.90;zz=2.32+sz*.125
            border += _key_bars([(xx-sx*.14,zz),(xx,zz),
                                 (xx,zz-sz*.09),(xx-sx*.055,zz-sz*.09)],
                                thickness=.012,y=-.422,depth=.008)
    _cuboids(api,"portal_tablet_returning_key_border",border,"wood_light",root)
    api.text("portal_title_jiaozi_fang","交子坊",(0,-.427,2.373),.255,
             "paper",rotation=(pi/2,0,0),parent=root)
    api.text("portal_subtitle_chumo_shengxiang","楮 墨 生 香",(0,-.427,2.183),.066,
             "paper_edge",rotation=(pi/2,0,0),parent=root)
    return root


def _lantern(api,side):
    """A small octagonal folded-paper palace lantern, hung outside the opening."""
    name="decor_palace_lantern_%s" % ("left" if side < 0 else "right")
    root=_tag(api.empty(name,(6+side*1.57,7.53,1.87)),
              "decor_lantern",(.38,.54,.85),"noninteractive_decoration")
    root["non_interactive"]=True
    root["style"]="octagonal_folded_paper_palace_lantern"
    api.line(name+"_attached_timber_hook",[(0,.365,.38),(0,.20,.38),
                                         (0,.03,.34),(0,0,.30)],
             "wood_dark",radius=.018,parent=root)
    api.line(name+"_suspension",[(0,0,.34),(0,0,.265)],
             "paper_edge",radius=.006,parent=root)
    angles=[pi/8+k*pi/4 for k in range(8)]
    rings=[(.115,-.18),(.145,-.115),(.145,.115),(.115,.18)]
    vertices=[(radius*cos(a),radius*sin(a),z) for radius,z in rings for a in angles]
    faces=[tuple(range(7,-1,-1)),tuple(range(24,32))]
    faces += [(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i)
              for j in range(3) for i in range(8)]
    api.mesh(name+"_warm_paper_panels",vertices,faces,"paper",parent=root)
    for i,a in enumerate(angles):
        api.line(name+f"_folded_red_rib_{i}",
                 [(radius*cos(a),radius*sin(a),z) for radius,z in rings],
                 "red",radius=.006,parent=root)
    for zz,radius in ((-.18,.12),(.18,.12)):
        points=[(radius*cos(a),radius*sin(a),zz) for a in angles]
        api.line(name+f"_octagonal_rim_{zz}",points+[points[0]],
                 "red",radius=.014,parent=root)
    for suffix,levels in (("folded_roof",[(.18,.19),(.16,.215),(.048,.285)]),
                          ("folded_skirt",[(.12,-.18),(.16,-.215),(.065,-.235)])):
        vv=[(radius*cos(a),radius*sin(a),z) for radius,z in levels for a in angles]
        ff=[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i)
            for j in range(2) for i in range(8)]
        if suffix == "folded_skirt":
            ff = [tuple(reversed(face)) for face in ff]
        api.mesh(name+"_"+suffix,vv,ff,"red",parent=root)
    api.line(name+"_front_returning_key",[(-.044,-.138,-.06),(-.044,-.138,.06),
             (.044,-.138,.06),(.044,-.138,-.06),(-.014,-.138,-.06),
             (-.014,-.138,.025),(.016,-.138,.025),(.016,-.138,-.024)],
             "red",radius=.0045,parent=root)
    api.cyl(name+"_paper_tassel_knot",(0,0,-.255),.023,.045,
            "wood_light",parent=root,vertices=8)
    vv,ff=[],[]
    for i in range(3):
        x=(i-1)*.020;start=len(vv)
        vv += [(x-.006,-.008,-.274),(x+.006,-.008,-.274),
               (x+.009,-.016,-.43+(i%2)*.025),(x-.006,-.018,-.43+(i%2)*.025)]
        ff.append(tuple(start+j for j in range(4)))
    api.mesh(name+"_three_paper_tassel_strips",vv,ff,"red",parent=root)
    return root


def build_architecture(api,spec):
    """Build the 12 by 8 m open workshop; return modular root objects."""
    roots=[]
    floor=spec["base"]["floor"]
    if tuple(floor)!=(12,8):
        raise ValueError("This version is authored for the approved 12 x 8 m layout")

    api.collection("ENV_01_Floor_Modules")
    for iy in range(4):
        for ix in range(6):
            roots.append(_floor(api,ix,iy))
    foundation=_tag(api.empty("env_paper_foundation",(6,4,0)),
                    "env_foundation",(12,8,.18),"foundation")
    for i,(z,thick,mat) in enumerate([(-.13,.06,"paper_edge"),
                                    (-.19,.06,"paper"),
                                    (-.25,.06,"paper_edge")]):
        api.box(f"foundation_layer_{i}",(0,0,z),(12,8,thick),
                mat,parent=foundation,bevel=.025)
    roots.append(foundation)

    api.collection("ENV_02_Back_Walls")
    # Ordinary 2 m pieces plus explicitly tagged cut-to-length end fillers.
    for i,(a,b,win) in enumerate([(.4,2.4,False),(2.4,4.4,False),(4.4,4.6,False),
                                  (7.4,9.6,True)]):
        roots.append(_wall(api,f"wall_back_{i:02d}",((a+b)/2,7.9,0),
                           b-a,2.4,window=win))
    roots.append(_portal(api))
    roots.append(_corner(api,"corner_back_left",(.2,7.8,0),2.4,0))
    roots.append(_corner(api,"corner_back_right",(11.8,7.8,0),2.4,-pi/2))
    # The 2 m receiving-window gap (x=9.6..11.6) is filled by station_delivery.
    # No back panel is placed across the window aperture.

    api.collection("ENV_03_Low_Boundary")
    for i,(a,b) in enumerate([(.4,2.4),(2.4,4.4),(4.4,4.8),
                             (7.2,7.6),(7.6,9.6),(9.6,11.6)]):
        roots.append(_wall(api,f"wall_front_{i:02d}",((a+b)/2,.1,0),
                           b-a,.45,low=True))
    for side,x,angle in [("left",.1,pi/2),("right",11.9,-pi/2)]:
        for i,(a,b) in enumerate([(.4,2.4),(2.4,4.4),(4.4,6)]):
            roots.append(_wall(api,f"wall_{side}_low_{i}",(x,(a+b)/2,0),
                               b-a,.45,angle=angle,low=True))
        roots.append(_wall(api,f"wall_{side}_back",(x,6.8,0),1.6,2.4,
                           angle=angle,window=(side=="right")))
    roots.append(_corner(api,"corner_front_left",(.2,.2,0),.45,pi/2))
    roots.append(_corner(api,"corner_front_right",(11.8,.2,0),.45,pi))

    api.collection("ENV_04_Open_Eaves")
    for i,(a,b) in enumerate([(0,2),(2,4),(4,4.6),(7.4,9.6),(9.6,11.6),(11.6,12)]):
        roots.append(_eave(api,f"eave_rear_{i:02d}",((a+b)/2,7.82,2.35),b-a,
                           lift_left=(a==0),lift_right=(b==12)))
    roots.append(_eave(api,"eave_portal_attached",(6,7.85,2.43),2.8,
                       lift_left=True,lift_right=True))
    roots.append(_eave(api,"eave_left_back",(.18,7,2.32),2,angle=pi/2,
                       lift_left=True))
    roots.append(_eave(api,"eave_right_back",(11.82,7,2.32),2,angle=-pi/2,
                       lift_right=True))

    api.collection("ENV_05_Decoration")
    roots.append(_lantern(api,-1))
    roots.append(_lantern(api,1))
    return roots
