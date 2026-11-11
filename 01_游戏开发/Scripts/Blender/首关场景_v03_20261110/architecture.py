"""First-level papercraft architecture, metre scale, Blender XY floor / Z up.

This builder uses only the narrow API passed by the scene assembly script.  It
does not clear the scene, save files, configure a renderer, or run on import.
The two workshop zones have no divider.  Length-adjusted wall ends close the
2 m modular grid around the separately specified 2.8 m rear portal.
"""

from math import pi, sin


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


def _tiles(api, name, width, depth, height, parent, z0=0):
    """Closed low-poly paper-tile strips, all pieces in a single mesh.

    Their front-to-back incline and six-sided arc are geometry, not normal-map
    decoration.  All vertices stay within the declared strip bounding box.
    """
    vertices, faces = [], []
    count = max(2, round(width / .24))
    step = width / count
    thickness = min(.025, height * .22)
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
            seams.append(((0,yy,.0008),(1.965,.008,.0015)))
        for row, yy in enumerate((-.666,0,.666)):
            offsets = (-.50,.48) if (ix+iy+row)%2 else (-.28,.68)
            for xx in offsets:
                seams.append(((xx,yy,.0008),(.008,.654,.0015)))
    else:
        for yy in (-.60,-.20,.20,.60):
            seams.append(((0,yy,.0008),(1.965,.010,.0015)))
        for row in range(5):
            xx = -.50 if (row+ix+iy)%2 else .50
            seams.append(((xx,-.80+row*.4,.0008),(.010,.385,.0015)))
    _cuboids(api,root.name+"_joints",seams,
             "paper_edge" if yard else "wood", root)
    if (ix+iy)%3==0:
        # Sparse lifted sheet corners reveal the floor's folded-paper construction.
        sign=-1 if ix%2 else 1
        xx=sign*.95;yy=.94;ss=.15
        api.mesh(root.name+'_paper_corner',
                 [(xx,yy,.003),(xx-sign*ss,yy,.003),(xx,yy-ss,.003),
                  (xx-sign*.035,yy-.035,.024)],
                 [(0,1,3),(0,3,2)],'paper_edge' if yard else 'paper',parent=root)
        api.line(root.name+'_fold_score',[(xx-sign*ss,yy,.005),(xx,yy-ss,.005)],
                 'paper_edge',radius=.0015,parent=root)
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
    api.box(name+"_paper_panel", (0,0,(base_h+top)/2),
            (width,.115,top-base_h), "paper", parent=root, bevel=.013)
    api.box(name+"_stone_foot", (0,0,base_h/2), (width,.2,base_h),
            "stone", parent=root, bevel=.012)
    frame = [((-width/2+.055,0,(base_h+top)/2),(.11,.2,top-base_h)),
             (( width/2-.055,0,(base_h+top)/2),(.11,.2,top-base_h)),
             ((0,0,top-.055),(width,.2,.11))]
    _cuboids(api,name+"_timber_frame",frame,"wood",root)
    if low:
        _tiles(api,name+"_tile_coping",width,.20,.08,root,z0=height-.08)
    elif not window and width>1.0:
        # A modest pasted repair and lifted corner, confined to the lower wall.
        px=-width*.24;pz=.42
        api.mesh(name+'_aged_paper_patch',
                 [(px-.18,-.061,pz-.14),(px+.17,-.061,pz-.14),
                  (px+.18,-.061,pz+.10),(px+.12,-.064,pz+.16),
                  (px-.18,-.061,pz+.14)],[(0,1,2,3,4)],'paper_edge',parent=root)
        api.mesh(name+'_repair_fold',
                 [(px+.18,-.063,pz+.10),(px+.12,-.064,pz+.16),(px+.11,-.09,pz+.10)],
                 [(0,1,2)],'paper',parent=root)
    elif window and width >= 1.1:
        ww = min(1.45,width-.40)
        wh, wz = .83, 1.62
        api.box(name+"_window_recess", (0,-.062,wz), (ww,.018,wh),
                "paper_edge",parent=root,bevel=.005)
        bars = []
        for xx in (-ww/2,ww/2):
            bars.append(((xx,-.083,wz),(.065,.033,wh+.065)))
        for zz in (wz-wh/2,wz+wh/2):
            bars.append(((0,-.083,zz),(ww,.033,.065)))
        for xx in (-ww/6,ww/6):
            bars.append(((xx,-.083,wz),(.04,.033,wh)))
        bars.append(((0,-.083,wz),(ww,.033,.04)))
        _cuboids(api,name+"_window_lattice",bars,"wood_dark",root)
        # Broad triangular paper/wood corner braces, inside the wall thickness.
        for side in (-1,1):
            x0=side*(width/2-.12)
            points=[(x0,-.083,top-.12),(x0-side*.35,-.083,top-.12),
                    (x0,-.083,top-.47)]
            points += [(x,y+.025,z) for x,y,z in points]
            api.mesh(name+f"_brace_{side}",points,
                     [(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],
                     "wood",parent=root)
    return root


def _eave(api, name, center, width, angle=0):
    root = _tag(api.empty(name,center),"env_eave",(width,.6,.4))
    root.rotation_euler.z=angle
    root["nominal_module_width"] = 2.0
    root["length_variant"] = abs(width-2.0) > .001
    api.box(name+"_support",(0,.03,.075),(width,.48,.10),
            "wood",parent=root,bevel=.018)
    _tiles(api,name+"_paper_tiles",width,.6,.4,root)
    braces=[((xx,-.10,.015),(.09,.36,.03))
            for xx in (-width*.35,0,width*.35)]
    _cuboids(api,name+"_rafter_ends",braces,"wood_light",root)
    return root


def _corner(api,name,center,height,angle):
    """Actual L cross-section; no overlapping two-wall approximation."""
    root=_tag(api.empty(name,center),"env_wall_corner",(.4,.4,height))
    root.rotation_euler.z=angle
    root["wall_thickness"] = .2
    # Default outside faces are left (-X) and back (+Y).
    outline=[(-.2,-.2),(0,-.2),(0,0),(.2,0),(.2,.2),(-.2,.2)]
    def extrusion(suffix,z0,z1,mat):
        verts=[(x,y,z) for z in (z0,z1) for x,y in outline]
        faces=[(5,4,3,2,1,0),(6,7,8,9,10,11)]
        faces += [(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
        return api.mesh(name+suffix,verts,faces,mat,parent=root)
    extrusion("_paper_L",.12,height-.065,"paper")
    extrusion("_foot_L",0,.12,"stone")
    extrusion("_cap_L",height-.065,height,"roof")
    # Keep the warm outer corner stitch within the L's actual envelope.
    api.box(name+"_vertical_stitch",(-.155,.155,(height+.12)/2),
            (.09,.09,height-.12),"wood",parent=root,bevel=.006)
    return root


def _portal(api):
    root = _tag(api.empty("env_portal_rear_attached",(6,7.9,0)),
                "env_portal",(2.8,.2,2.4))
    root["clear_width"], root["clear_height"] = 2.4,2.1
    for side in (-1,1):
        api.box(f"portal_post_{side}",(side*1.3,0,1.2),(.2,.2,2.4),
                "wood",parent=root,bevel=.012)
        api.box(f"portal_foot_{side}",(side*1.3,0,.08),(.2,.2,.16),
                "stone",parent=root,bevel=.010)
    api.box("portal_header",(0,0,2.25),(2.8,.2,.3),
            "wood_light",parent=root,bevel=.015)
    # No braces inside the opening: declared clear rectangle is really clear.
    return root


def _lantern(api):
    root = _tag(api.empty("decor_lantern_rear",(4.7,7.55,1.72)),
                "decor_lantern",(.32,.30,.64),"noninteractive_decoration")
    api.line("lantern_support",[(0,.35,.36),(0,0,.36),(0,0,.26)],
             "wood_dark",radius=.022,parent=root)
    api.box("lantern_paper_body",(0,0,0),(.28,.22,.34),
            "red",parent=root,bevel=.025)
    for zz in (-.18,.18):
        api.box(f"lantern_rim_{zz}",(0,0,zz),(.32,.26,.045),
                "wood_light",parent=root,bevel=.009)
    top=[(-.16,-.13,.20),(.16,-.13,.20),(.16,.13,.20),
         (-.16,.13,.20),(0,0,.29)]
    api.mesh("lantern_folded_cap",top,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(3,2,1,0)],
             "red",parent=root)
    api.line("lantern_paper_seal",[(-.075,-.115,-.09),(-.075,-.115,.09),
             (.075,-.115,.09),(.075,-.115,-.09),(-.03,-.115,-.09),
             (-.03,-.115,.035),(.03,-.115,.035),(.03,-.115,-.035)],
             "paper",radius=.009,parent=root)
    api.cyl("lantern_tassel",(0,0,-.28),.018,.16,"red",parent=root,vertices=6)
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
        roots.append(_eave(api,f"eave_rear_{i:02d}",((a+b)/2,7.75,2.35),b-a))
    roots.append(_eave(api,"eave_left_back",(.25,7,2.35),2,angle=pi/2))
    roots.append(_eave(api,"eave_right_back",(11.75,7,2.35),2,angle=-pi/2))

    api.collection("ENV_05_Decoration")
    roots.append(_lantern(api))
    return roots
