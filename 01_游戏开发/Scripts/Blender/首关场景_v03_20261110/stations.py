"""Editable papercraft station kit for Jiaozi level one.

All geometry uses Blender metres, XY ground and +Z up.  Each station is
an empty at its layout centre; all parts and anchors are local children.
The visible paper/engraving is a modelling preview, not a game-state system.
"""

import math


def _anchor(api, root, suffix, loc, role, slot=None):
    ob = api.empty(root.name + "__" + suffix, loc, parent=root, size=0.10)
    ob["role"] = role
    ob["export_helper"] = True
    if slot is not None:
        ob["slot_id"] = slot
    return ob


def _operation(api, root, depth, side=-1, x=0.0, suffix="main", slot=None):
    """Target is at the table edge; standing point is a distinct helper."""
    _anchor(api, root, "interaction_" + suffix,
            (x, side * (depth / 2 + 0.05), 0.48), "interaction_target", slot)
    _anchor(api, root, "standing_" + suffix,
            (x, side * (depth / 2 + 0.425), 0), "player_standing_point", slot)


def _rect(api, name, x, y, z, w, d, mat, parent, radius=.004):
    pts = [(x-w/2, y-d/2, z), (x+w/2, y-d/2, z),
           (x+w/2, y+d/2, z), (x-w/2, y+d/2, z),
           (x-w/2, y-d/2, z)]
    return api.line(name, pts, mat, radius=radius, parent=parent)


def _circle(api, name, center, radius, mat, parent, line_radius=.004, n=16):
    x, y, z = center
    pts = [(x+radius*math.cos(i*2*math.pi/n),
            y+radius*math.sin(i*2*math.pi/n), z) for i in range(n+1)]
    return api.line(name, pts, mat, radius=line_radius, parent=parent)


def _layered_top(api, name, parent, w, d, h=.65):
    """A single 0.10 m board made of broad, visible paper laminations."""
    api.box(name+"__core", (0,0,h-.069), (w-.014,d-.014,.062),
            "wood_light", parent=parent, bevel=.010)
    api.box(name+"__edge_shadow", (0,0,h-.036), (w-.010,d-.010,.004),
            "wood_dark", parent=parent, bevel=.001)
    api.box(name+"__paper_lamination", (0,0,h-.030), (w-.006,d-.006,.008),
            "paper_edge", parent=parent, bevel=.002)
    api.box(name+"__warm_lamination", (0,0,h-.021), (w-.008,d-.008,.010),
            "wood_light", parent=parent, bevel=.003)
    # Keep the named top's upper face at the original exact work height.
    api.box(name, (0,0,h-.008), (w,d,.016),
            "wood_light", parent=parent, bevel=.006)
    # Two small worn/folded corner facets reveal clean paper beneath the finish.
    for sign in (-1,1):
        x=sign*(w/2-.025)
        y=-d/2+.025
        verts=[(x,y,h+.0005),(x-sign*.075,y,h+.0005),
               (x-sign*.012,y+.055,h+.0015)]
        patch=api.mesh(name+"__paper_corner",verts,[(0,1,2)],"paper_edge",parent=parent)
        patch["role"]="surface_wear_detail"


def _table(api, root, w, d, h=.65):
    p = root.name
    _layered_top(api,p+"__tabletop",root,w,d,h)
    api.box(p+"__paper_lip", (0, 0, h-.113), (w-.08, d-.08, .026),
            "paper_edge", parent=root, bevel=.006)
    # An apron and low stretchers make the table a believable timber structure.
    for y in (-d/2+.10, d/2-.10):
        api.box(p+"__apron_y", (0, y, h-.18), (w-.18, .075, .15),
                "wood", parent=root, bevel=.012)
    for x in (-w/2+.12, w/2-.12):
        for y in (-d/2+.12, d/2-.12):
            api.box(p+"__leg", (x, y, .27), (.15, .15, .54),
                    "wood", parent=root, bevel=.015)
        api.box(p+"__stretcher_y", (x, 0, .18), (.065, d-.18, .07),
                "wood_dark", parent=root, bevel=.008)
    # Two large join lines, rather than noisy individual slivers.
    for y in (-d/6, d/6):
        api.line(p+"__top_join", [(-w/2+.04,y,h+.001), (w/2-.04,y,h+.001)],
                 "wood", radius=.002, parent=root)
    for x in (-w*.31, w*.31):
        api.box(p+"__teal_binding", (x, -d/2+.014, h-.035),
                (.065,.022,.065), "teal", parent=root, bevel=.004)
    # Paper wraps are limited to the two front feet; work surfaces stay clean.
    for x in (-w/2+.12,w/2-.12):
        api.box(p+"__foot_paper_wrap",(x,-d/2+.044,.055),(.115,.003,.038),
                "paper_edge",parent=root,bevel=.002)
    api.line(p+"__apron_edge_wear",[(-w/2+.22,-d/2+.060,.505),
                                   (-w/2+.31,-d/2+.060,.502),
                                   (-w/2+.37,-d/2+.060,.505)],
             "paper_edge",radius=.002,parent=root)


def _folded_paper(api, name, parent, loc, wet=False, vertical=False):
    """One .42 x .60 m sheet with an actual folded corner and thin edge."""
    x, y, z = loc
    w, d, fold = .42, .60, .040 if wet else .055
    curl=.010 if wet else .024
    # Six coplanar perimeter vertices and a lifted fold tip.
    vv = [(-w/2,-d/2,0), (w/2-fold,-d/2,0), (w/2,-d/2+fold,0),
          (w/2,d/2,0), (-w/2,d/2,0), (w/2-fold,-d/2+fold,curl)]
    if vertical:
        verts = [(x+a, y-c, z+b) for a,b,c in vv]
    else:
        verts = [(x+a, y+b, z+c) for a,b,c in vv]
    ob = api.mesh(name, verts, [(0,1,2,3,4)],
                  "wet" if wet else "paper", parent=parent)
    solid = ob.modifiers.new("Single sheet fibre thickness", "SOLIDIFY")
    solid.thickness = .006
    solid.offset = 0
    api.mesh(name+"__fold", [verts[1], verts[2], verts[5]], [(0,1,2)],
             "paper_edge", parent=parent)
    # A deckled fibre edge belongs to this same sheet, not to another paper slot.
    edge=[(-w/2+.010,-d/2+.004,.0025),(-.10,-d/2+.006,.0025),
          (-.025,-d/2+.002,.0025),(.045,-d/2+.006,.0025),
          (w/2-fold-.008,-d/2+.004,.0025)]
    edge_world=[(x+a,y-c,z+b) if vertical else (x+a,y+b,z+c) for a,b,c in edge]
    api.line(name+"__deckled_fibre_edge",edge_world,"paper_edge",radius=.0015,parent=parent)
    ob["single_sheet_geometry"]=True
    ob["role"] = "material_state_preview"
    ob["material_state"] = "wet" if wet else "dry"
    ob["preview_only"] = True
    return ob


def _bowl(api, name, parent, loc, radius=.13, liquid="ink"):
    x, y, z = loc
    n = 12
    rings = [(radius*.76,0), (radius,.075), (radius*.77,.075), (radius*.62,.025)]
    verts = []
    for rr, zz in rings:
        verts.extend((x+rr*math.cos(i*2*math.pi/n),
                      y+rr*math.sin(i*2*math.pi/n), z+zz) for i in range(n))
    faces = []
    for ring in range(3):
        for i in range(n):
            j=(i+1)%n
            faces.append((ring*n+i,ring*n+j,(ring+1)*n+j,(ring+1)*n+i))
    faces.append(tuple(reversed(range(n))))
    api.mesh(name+"__hollow_bowl", verts, faces, "stone", parent=parent)
    api.cyl(name+"__liquid", (x,y,z+.045), radius*.72, .008,
            liquid, parent=parent, vertices=n)


def _coin(api, name, parent, x, y, z, r=.035, mat="paper_edge"):
    _circle(api,name+"__outer",(x,y,z),r,mat,parent,line_radius=.003,n=12)
    _rect(api,name+"__square_hole",x,y,z,r*.65,r*.65,mat,parent,radius=.002)


def _portrait(api, name, parent, x, y, z, girl=False, scale=1.0):
    """Small relief engraving, kept deliberately simpler than final ticket art."""
    s=scale
    api.cyl(name+"__face", (x,y,z), .050*s, .004,
            "paper_edge", parent=parent, vertices=12)
    for ex in (-.018,.018):
        api.cyl(name+"__eye", (x+ex*s,y-.005*s,z+.004), .005*s,.003,
                "ink",parent=parent,vertices=8)
    api.line(name+"__smile",[(x-.012*s,y-.021*s,z+.005),
                            (x,y-.027*s,z+.005),(x+.012*s,y-.021*s,z+.005)],
             "ink",radius=.002,parent=parent)
    if girl:
        for bx in (-.054,.054):
            api.cyl(name+"__bun",(x+bx*s,y+.035*s,z+.003),.023*s,.005,
                    "paper_edge",parent=parent,vertices=8)
        api.line(name+"__hair",[(x-.045*s,y+.01*s,z+.005),
                               (x-.025*s,y+.045*s,z+.005),
                               (x+.03*s,y+.038*s,z+.005),
                               (x+.047*s,y+.005*s,z+.005)],
                 "ink",radius=.003,parent=parent)
    else:
        verts=[(x-.065*s,y+.018*s,z+.006),(x+.065*s,y+.018*s,z+.006),
               (x+.036*s,y+.076*s,z+.006),(x-.032*s,y+.076*s,z+.006)]
        api.mesh(name+"__folded_hat",verts,[(0,1,2,3)],"paper_edge",parent=parent)
        api.line(name+"__hat_fold",[verts[0],(x,y+.064*s,z+.008),verts[1]],
                 "ink",radius=.002,parent=parent)


def _note_art(api, root, loc, sealed=False):
    """A single modelled sample ticket; not a replacement for the source artwork."""
    x,y,z=loc
    paper=_folded_paper(api,root.name+"__sample_ticket",root,loc)
    paper["material_state"]="red_jiaozi" if sealed else "black_jiaozi"
    _rect(api,root.name+"__note_border",x,y,z+.008,.37,.53,"ink",root,.0025)
    for i in range(3):
        _coin(api,root.name+"__note_coin",root,x+(i-1)*.1,y+.195,z+.009,.032,"ink")
    # Two recognizable craftsperson silhouettes are separate relief geometry.
    _portrait(api,root.name+"__note_zhituan",root,x-.083,y-.14,z+.009,False,.88)
    _portrait(api,root.name+"__note_yintao",root,x+.083,y-.14,z+.009,True,.88)
    for i in range(4):
        xx=x-.13+i*.085
        api.line(root.name+"__note_script",[(xx,y-.025,z+.009),(xx,y+.11,z+.009)],
                 "ink",radius=.0025,parent=root)
    if sealed:
        _rect(api,root.name+"__note_redseal",x+.12,y-.22,z+.012,.075,.075,"red",root,.004)
    return paper


def _pulp(api, root):
    p=root.name
    api.box(p+"__bottom",(0,0,.14),(1.82,1.02,.15),"wood_dark",parent=root,bevel=.02)
    for x in (-.93,.93):
        api.box(p+"__side_x",(x,0,.37),(.14,1.2,.50),"wood",parent=root,bevel=.018)
    for y in (-.53,.53):
        api.box(p+"__side_y",(0,y,.37),(1.85,.14,.50),"wood",parent=root,bevel=.018)
    for x in (-.895,.895):
        for y in (-.495,.495):
            api.box(p+"__corner_post",(x,y,.325),(.20,.20,.65),"wood_light",parent=root,bevel=.02)
            api.box(p+"__post_binding",(x,y,.43),(.205,.205,.055),"teal",parent=root,bevel=.005)
    # Interior liner and water remain independent so the water can animate later.
    api.box(p+"__inner_liner",(0,0,.34),(1.68,.88,.20),"paper_edge",parent=root,bevel=.025)
    api.box(p+"__water",(0,0,.495),(1.69,.89,.012),"water",parent=root,bevel=.008)
    # A handful of floating paper fibres, not dense speckles or a new resource.
    for index,(x,y,angle) in enumerate(((-.66,-.23,.3),(-.34,.28,-.4),
                                        (-.61,.16,.7),(.02,-.29,.2),(.62,.27,-.5))):
        dx,dy=.032*math.cos(angle),.032*math.sin(angle)
        api.line(p+"__pulp_fibre_"+str(index),
                 [(x-dx,y-dy,.503),(x,y+.005,.504),(x+dx,y+dy,.503)],
                 "paper_edge",radius=.0018,parent=root)
    for y in (-.590,.590):
        api.line(p+"__vat_layer_seam",[(-.76,y,.55),(.76,y,.55)],
                 "paper_edge",radius=.002,parent=root)
    for n,r in enumerate((.25,.42)):
        pts=[(-.45+r*math.cos(i*2*math.pi/24), .22*r*math.sin(i*2*math.pi/24), .504)
             for i in range(25)]
        api.line(p+"__water_ring_"+str(n),pts,"paper",radius=.003,parent=root)
    screen=_anchor(api,root,"screen_pivot",(.27,0,.536),"movable_screen_pivot")
    for x in (-.24,.24):
        api.box(p+"__screen_side",(x,0,0),(.04,.70,.035),"wood_light",parent=screen,bevel=.006)
    for y in (-.33,.33):
        api.box(p+"__screen_end",(0,y,0),(.52,.04,.035),"wood_light",parent=screen,bevel=.006)
    api.box(p+"__screen_mesh",(0,0,-.009),(.44,.62,.008),"wet",parent=screen,bevel=.003)
    for i in range(9):
        api.box(p+"__screen_bamboo",(0,-.27+i*.067,0),(.44,.010,.012),"wood",parent=screen,bevel=.002)
    for x in (-.24,.24):
        for y in (-.25,.25):
            api.box(p+"__screen_tie",(x,y,.004),(.045,.025,.039),"teal",parent=screen,bevel=.002)
    _anchor(api,root,"slot_0",(.27,0,.56),"paper_anchor","0")
    _operation(api,root,1.2,side=1)
    root["default_preview_state"]="pulp_with_empty_screen"


def _dry(api, root):
    p=root.name
    for x in (-.88,.88):
        api.box(p+"__foot",(x,0,.07),(.24,.80,.14),"wood_light",parent=root,bevel=.018)
        api.box(p+"__upright",(x,0,.83),(.12,.14,1.46),"wood",parent=root,bevel=.012)
        api.box(p+"__post_cap",(x,0,1.55),(.20,.20,.10),"wood_light",parent=root,bevel=.012)
        for z in (.20,1.45):
            api.box(p+"__post_binding",(x,0,z),(.132,.152,.055),"teal",parent=root,bevel=.004)
    api.box(p+"__crossbar",(0,0,1.47),(1.98,.13,.12),"wood_light",parent=root,bevel=.015)
    for index, x in enumerate((-.5,.5)):
        slot="A" if index==0 else "B"
        _anchor(api,root,"slot_"+slot,(x,-.085,1.00),"paper_anchor",slot)
        sheet=_folded_paper(api,p+"__preview_"+slot,root,(x,-.085,1.00),wet=index==0,vertical=True)
        sheet["slot_id"]=slot
        if index==0:
            # Two small drops communicate the wet state without a third sheet.
            for offset in (-.11,.10):
                xx=x+offset
                verts=[(xx,-.091,.681),(xx-.010,-.091,.652),
                       (xx,-.091,.644),(xx+.010,-.091,.652)]
                drop=api.mesh(p+"__wet_drop",verts,[(0,1,2,3)],"teal",parent=root)
                drop["role"]="wet_state_visual"
                drop["slot_id"]=slot
        else:
            # The dry sheet stays pale, with one subtle fold rather than stains.
            api.line(p+"__dry_corner_crease",[(x+.15,-.089,.75),
                                             (x+.182,-.089,.783)],
                     "paper_edge",radius=.0013,parent=root)
        for xx in (x-.14,x+.14):
            api.box(p+"__clip_"+slot,(xx,-.08,1.335),(.035,.055,.19),"wood_light",parent=root,bevel=.004)
            api.box(p+"__clip_back_"+slot,(xx,.04,1.445),(.035,.04,.15),"wood",parent=root,bevel=.003)
            api.box(p+"__clip_bridge_"+slot,(xx,-.01,1.505),(.035,.14,.026),"wood_light",parent=root,bevel=.003)
        _operation(api,root,.8,side=-1,x=x,suffix=slot,slot=slot)
    root["slot_count"]=2
    root["slot_center_distance"]=1.0
    root["default_preview_state"]="A_wet_B_dry"


def _printing(api, root):
    p=root.name
    _table(api,root,1.6,1.0)
    api.box(p+"__print_block_base",(-.23,0,.677),(.88,.80,.054),"wood_dark",parent=root,bevel=.014)
    for z in (.671,.684):
        api.line(p+"__print_block_paper_layer",[(-.62,-.401,z),(.16,-.401,z)],
                 "paper_edge",radius=.002,parent=root)
    api.box(p+"__print_ink_surface",(-.23,0,.708),(.81,.73,.012),"ink",parent=root,bevel=.006)
    _rect(api,p+"__block_border",-.23,0,.718,.75,.67,"paper_edge",root,.006)
    for row in range(2):
        for col in range(5):
            _coin(api,p+"__engraved_coin",root,-.51+col*.14,.15+row*.12,.72,.046)
    _portrait(api,p+"__engraved_zhituan",root,-.40,-.22,.721,False,1.6)
    _portrait(api,p+"__engraved_yintao",root,-.08,-.22,.721,True,1.6)
    for xx in (-.51,-.37,-.23,-.09,.05):
        api.line(p+"__engraved_rule",[(xx,-.04,.72),(xx,.07,.72)],"paper_edge",radius=.004,parent=root)
    api.box(p+"__tool_tray",(.52,.02,.666),(.39,.82,.032),"paper_edge",parent=root,bevel=.025)
    _bowl(api,p+"__ink",root,(.52,.23,.682))
    api.cyl(p+"__rubbing_pad_base",(.52,-.19,.71),.14,.055,"red",parent=root,vertices=12)
    api.cyl(p+"__rubbing_pad_body",(.52,-.19,.755),.13,.055,"paper",parent=root,vertices=12)
    api.cyl(p+"__rubbing_pad_handle",(.52,-.19,.812),.04,.06,"wood_light",parent=root,vertices=8)
    api.cyl(p+"__rubbing_pad_tie",(.52,-.19,.788),.047,.025,"teal",parent=root,vertices=8)
    _anchor(api,root,"slot_0",(-.23,0,.725),"paper_anchor","0")
    _operation(api,root,1.0,side=-1)
    root["default_preview_state"]="empty_print_block"
    root["engraving_is_placeholder"]=True


def _stamping(api, root):
    p=root.name
    _table(api,root,1.6,1.0)
    api.box(p+"__paper_mat",(-.21,0,.657),(.74,.82,.014),"paper_edge",parent=root,bevel=.018)
    _note_art(api,root,(-.21,0,.669),sealed=True)
    # The whole seal has a dedicated pivot and can later animate independently.
    seal=_anchor(api,root,"seal_pivot",(.53,.16,.67),"movable_stamp_pivot")
    api.box(p+"__seal_body",(0,0,.105),(.22,.22,.21),"red",parent=seal,bevel=.022)
    api.box(p+"__seal_sole",(0,0,.018),(.235,.235,.036),"wood_dark",parent=seal,bevel=.008)
    api.line(p+"__seal_handle",[(-.065,0,.21),(-.07,0,.29),(-.04,0,.34),
                               (.04,0,.34),(.07,0,.29),(.065,0,.21)],
             "paper_edge",radius=.018,parent=seal)
    # Hand-cut square seal outline on its front-facing surface.
    api.line(p+"__seal_front_mark",[(-.07,-.112,.05),(.07,-.112,.05),(.07,-.112,.16),
                                   (-.07,-.112,.16),(-.07,-.112,.05)],
             "paper_edge",radius=.006,parent=seal)
    api.line(p+"__seal_inner_mark",[(-.035,-.114,.08),(.035,-.114,.08),
                                   (.035,-.114,.13),(-.005,-.114,.13),(-.005,-.114,.105)],
             "paper_edge",radius=.006,parent=seal)
    api.box(p+"__inkpad_tray",(.52,-.22,.674),(.29,.26,.048),"wood_dark",parent=root,bevel=.016)
    api.box(p+"__red_inkpad",(.52,-.22,.702),(.23,.20,.016),"red",parent=root,bevel=.010)
    _anchor(api,root,"slot_0",(-.21,0,.674),"paper_anchor","0")
    _anchor(api,root,"seal_contact",(-.10,-.18,.678),"stamp_contact_point")
    _operation(api,root,1.0,side=1)
    root["default_preview_state"]="single_red_ticket_demonstration"


def _delivery(api, root):
    p=root.name
    # The top/back of this window joins the building; the middle stays OPEN.
    for x in (-.895,.895):
        api.box(p+"__upright",(x,.12,1.15),(.20,.20,2.30),"wood",parent=root,bevel=.018)
        api.box(p+"__base_binding",(x,.12,.20),(.204,.204,.09),"teal",parent=root,bevel=.005)
    api.box(p+"__lower_panel",(0,.20,.29),(1.60,.10,.58),"paper",parent=root,bevel=.010)
    _layered_top(api,p+"__counter",root,1.96,.60,.65)
    api.box(p+"__counter_apron",(0,.13,.48),(1.80,.14,.14),"wood",parent=root,bevel=.012)
    api.box(p+"__header",(0,.15,2.13),(2.0,.22,.18),"wood",parent=root,bevel=.014)
    # Compact folded tile strips fill the eave envelope, not a solid roof slab.
    for i in range(10):
        left=-1.0+i*.2
        verts=[(left,-.30,2.12),(left+.10,-.30,2.16),(left+.20,-.30,2.12),
               (left,.30,2.35),(left+.10,.30,2.40),(left+.20,.30,2.35)]
        tile=api.mesh(p+"__roof_tile_"+str(i),verts,[(0,1,4,3),(1,2,5,4)],"roof",parent=root)
        solid=tile.modifiers.new("Folded tile thickness", "SOLIDIFY")
        solid.thickness=.018
        solid.offset=-1
    api.box(p+"__sign",(0,-.23,1.83),(.83,.045,.32),"paper",parent=root,bevel=.02)
    api.text(p+"__sign_text","交付",(0,-.256,1.83),.22,"ink",
             rotation=(math.pi/2,0,0),parent=root)
    for x in (-.38,.38):
        api.box(p+"__sign_hanger",(x,-.23,2.0),(.025,.03,.14),"wood_dark",parent=root,bevel=.003)
    # Open tray: separate base and walls, not a solid cuboid receiving surface.
    api.box(p+"__tray_base",(-.15,-.065,.67),(.68,.36,.04),"teal",parent=root,bevel=.016)
    for x in (-.47,.17):
        api.box(p+"__tray_side",(x,-.065,.704),(.04,.36,.07),"teal",parent=root,bevel=.010)
    for y in (-.225,.095):
        api.box(p+"__tray_end",(-.15,y,.704),(.64,.04,.07),"teal",parent=root,bevel=.010)
    api.box(p+"__receipt_tag",(.54,.04,.78),(.16,.04,.26),"red",parent=root,bevel=.009)
    api.text(p+"__receipt_text","收",(.54,.016,.78),.10,"paper",
             rotation=(math.pi/2,0,0),parent=root)
    _anchor(api,root,"receiving_slot",(-.15,-.065,.70),"paper_anchor","0")
    _anchor(api,root,"receipt_anchor",(.54,.04,.78),"receipt_feedback_anchor")
    _operation(api,root,.60,side=-1)
    root["default_preview_state"]="empty_receiving_tray"
    root["requires_adjacent_wall_join"]=True


def _shared(api, root):
    _table(api,root,1.0,1.0)
    _rect(api,root.name+"__single_slot_outline",0,0,.654,.50,.68,"paper_edge",root,.006)
    for x in (-.25,.25):
        for y in (-.34,.34):
            api.box(root.name+"__slot_corner",(x,y,.654),(.045,.045,.006),"teal",parent=root,bevel=.003)
    _anchor(api,root,"slot_0",(0,0,.662),"paper_anchor","0")
    _operation(api,root,1.0,side=1)
    root["default_preview_state"]="empty_single_slot"


def build_stations(api, spec):
    """Build six root assemblies and return the roots in specification order."""
    builders={"station_pulp":_pulp,"station_dry":_dry,"station_print":_printing,
              "station_stamp":_stamping,"station_delivery":_delivery,"station_shared":_shared}
    roots=[]
    for item in spec["stations"]:
        sid=item["id"]
        api.collection("Stations/"+sid)
        x,y=item["center_xz"]
        root=api.empty(sid,(x,y,0),size=.2)
        root["task"]=item["task"]
        root["asset_id"]=sid
        root["role"]="station_root"
        root["width"],root["depth"],root["height"]=item["dimensions"]
        root["desired_size"]=item["dimensions"]
        root["slot_count"]=1
        root["version"]="v03_20261110"
        root["surface_finish"]="light_paper_lamination_and_restrained_edge_wear"
        root["preview_only"]=True
        root["coordinate_convention"]="Blender XY ground, Z up; local origin on ground"
        builders[sid](api,root)
        roots.append(root)
    return roots
