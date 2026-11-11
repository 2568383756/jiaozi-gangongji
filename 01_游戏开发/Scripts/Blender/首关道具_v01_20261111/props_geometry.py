"""Independent, metre-scale props for F04--F09; no gameplay logic."""
import math
import bpy

VERSION = "v01_20261111"
PAPER_W, PAPER_D = .42, .60
PAIR_IDS = ["yintao", "zhituan"]
PAIR_KEY = "|".join(PAIR_IDS)
# Exact source-image rectangles (top-left pixel coordinates, 1024 x 1536).
# Ink-layer geometry omits them; the single red overlay restores both at once.
RED_RECTS = ((832,435,958,553), (35,1357,160,1519))


def marker(api, root, name, xyz, role):
    ob=api.empty(root.name+"__"+name,xyz,parent=root,size=.025)
    ob["role"]=role
    ob["is_attachment_helper"]=True
    return ob


def asset(api, sid, label, task, role="fixed_station_tool", grip=(0,0,0)):
    api.collection("PROPS/"+sid)
    root=api.empty(sid,(0,0,0),size=.055)
    root["asset_id"]=sid;root["display_name"]=label;root["task"]=task
    root["version"]=VERSION;root["role"]=role
    root["carryable"]=role=="paper_material"
    root["inventory_units"]=1 if role=="paper_material" else 0
    root["unit_m"]=1.0;root["reference_character_height_m"]=1.2
    root["reference_table_height_m"]=.65
    root["forward"]="-Y";root["up"]="+Z"
    root["source_pose"]="asset origin on bottom plane; gallery translation is display only"
    marker(api,root,"placement_pivot",(0,0,0),"station_placement_pivot")
    marker(api,root,"attach_pivot",(0,0,0),"HoldPoint_attachment_pivot")
    marker(api,root,"grip_pivot",grip,"physical_grip_center")
    return root


def rect(api,name,root,x,y,z,w,d,mat="ink",r=.002):
    return api.line(name,[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),
                         (x+w/2,y+d/2,z),(x-w/2,y+d/2,z),(x-w/2,y-d/2,z)],
                    mat,radius=r,parent=root)


def circle(api,name,root,x,y,z,r,mat="wood_light",tube=.003):
    return api.line(name,[(x+r*math.cos(i*math.tau/24),y+r*math.sin(i*math.tau/24),z)
                         for i in range(25)],mat,radius=tube,parent=root)


def profile(api,name,root,xz,depth,mat):
    n=len(xz)
    vv=[(x,side*depth/2,z) for side in (-1,1) for x,z in xz]
    ff=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    ff.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return api.mesh(name,vv,ff,mat,parent=root)


def texture_material(path):
    mat=bpy.data.materials.new("MAT_first_pair_formal_reference")
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value=.92
    bsdf.inputs["Specular IOR Level"].default_value=.15
    image=bpy.data.images.load(str(path),check_existing=True);image.pack()
    tex=mat.node_tree.nodes.new("ShaderNodeTexImage");tex.image=image
    mat.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
    mat["artwork_source"]="08_组合交子_纸团印桃.png; untouched 1024x1536 reference"
    return mat


def uv_mesh(api,name,root,vertices,faces,uvs,material,layer):
    ob=api.mesh(name,vertices,faces,material,parent=root)
    uv=ob.data.uv_layers.new(name="SourceArtworkUV")
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv=uvs[ob.data.loops[li].vertex_index]
    ob["preserve_source_uv"]=True
    ob["ticket_layer"]=layer
    ob["open_art_surface"]=True
    return ob


def ticket_layer(api,root,name,material,width,depth,z,red=False):
    """Keep source RGB untouched; split physical UV patches around red seals."""
    regions=[(x0/1024,1-y1/1536,x1/1024,1-y0/1536) for x0,y0,x1,y1 in RED_RECTS]
    if red:
        rectangles=regions
    else:
        xs=sorted({0.,1.,*[v for r in regions for v in (r[0],r[2])]})
        ys=sorted({0.,1.,*[v for r in regions for v in (r[1],r[3])]})
        rectangles=[]
        for a,b in zip(xs,xs[1:]):
            for c,d in zip(ys,ys[1:]):
                u,v=(a+b)/2,(c+d)/2
                if not any(x0<u<x1 and y0<v<y1 for x0,y0,x1,y1 in regions):
                    rectangles.append((a,c,b,d))
    verts,faces,uvs=[],[],[]
    for x0,y0,x1,y1 in rectangles:
        start=len(verts)
        patch=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        verts.extend(((u-.5)*width,(v-.5)*depth,z) for u,v in patch)
        uvs.extend(patch);faces.append(tuple(start+i for i in range(4)))
    ob=uv_mesh(api,name,root,verts,faces,uvs,material,"red_seal" if red else "black_ink")
    ob["pair_key"]=PAIR_KEY
    ob["red_regions_omitted"]=not red
    ob["single_toggle_group"]=red
    ob["red_mark_count"]=2 if red else 0
    return ob


def sheet_geometry(api,root,wet=False):
    w,d=PAPER_W,PAPER_D
    c=.028
    ring=[(-w/2,-d/2),(w/2-c,-d/2),(w/2,-d/2+c),(w/2,d/2),(-w/2,d/2)]
    verts=[(x,y,z) for z in (0,.006) for x,y in ring]
    faces=[(4,3,2,1,0),(5,6,7,8,9)]
    faces.extend((i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5))
    body=api.mesh(root.name+"__paper_body",verts,faces,"wet" if wet else "paper",parent=root)
    body["shared_geometry_key"]="paper_sheet_042x060_6mm"
    fold=api.mesh(root.name+"__folded_corner",[(w/2-c,-d/2,.006),(w/2,-d/2+c,.006),
                 (w/2-c,-d/2+c,.023)],[(0,1,2)],"paper_edge",parent=root)
    mod=fold.modifiers.new("Folded paper thickness","SOLIDIFY");mod.thickness=.003;mod.offset=-1
    api.line(root.name+"__deckled_edge",[(-.20,-.298,.004),(-.10,-.296,.004),
             (0,-.298,.004),(.09,-.297,.004),(.175,-.298,.004)],
             "paper_edge",radius=.001,parent=root)


def make_paper(api,state,art_material):
    ids={"wet":("湿纸","F04,F05,F06"),"dry":("干纸","F04,F06,F07"),
         "black":("黑墨交子","F04,F07,F08"),"red":("朱印交子","F04,F08,F09")}
    label,task=ids[state]
    root=asset(api,"paper_"+state,label,task,"paper_material",(0,.21,.006))
    root["material_state"]=state;root["capacity_units"]=1
    root["paper_width_m"]=PAPER_W;root["paper_depth_m"]=PAPER_D
    root["pair_key"]=PAIR_KEY if state in ("black","red") else ""
    root["state_transition"]=dict(wet="dry",dry="black",black="red",red="consumed")[state]
    marker(api,root,"palm_contact_L",(-.19,.21,.006),"left_palm_contact")
    marker(api,root,"palm_contact_R",(.19,.21,.006),"right_palm_contact")
    marker(api,root,"hang_pivot",(0,.27,.006),"rack_clip_line")
    marker(api,root,"surface_anchor",(0,0,.006),"ticket_art_surface")
    sheet_geometry(api,root,state=="wet")
    if state=="wet":
        for xx,yy,rr in ((.10,-.19,.028),(.15,-.22,.017)):
            pts=[(xx,yy+rr*1.6,.007),(xx-rr*.72,yy+.003,.007),
                 (xx-rr*.65,yy-rr*.65,.007),(xx,yy-rr,.007),
                 (xx+rr*.65,yy-rr*.65,.007),(xx+rr*.72,yy+.003,.007)]
            ob=api.mesh(root.name+"__water_drop_mark",pts,[(0,1,2,3,4,5)],"teal",parent=root)
            ob["open_art_surface"]=True
    if state in ("black","red"):
        ticket_layer(api,root,root.name+"__black_ink_layer",art_material,.36,.54,.007)
        root["artwork_status"]="formal_first_pair_reference_uv_separated; not a 15-pair compositor"
    if state=="red":
        ticket_layer(api,root,root.name+"__red_seal_layer",art_material,.36,.54,.0073,True)
    return root


def make_screen(api):
    root=asset(api,"tool_papermaking_screen","抄纸帘框","F05",grip=(0,0,.055))
    for x in (-.24,.24):
        api.box(root.name+"__bamboo_side",(x,0,.020),(.04,.70,.04),"wood_light",root,.006)
        api.line(root.name+"__lift_handle",[(x,-.10,.038),(x,-.06,.082),
                 (x,.06,.082),(x,.10,.038)],"wood_light",radius=.010,parent=root)
    for y in (-.33,.33):
        api.box(root.name+"__bamboo_end",(0,y,.020),(.52,.04,.04),"wood_light",root,.006)
    for i in range(13):
        api.box(root.name+"__bamboo_rib",(0,-.282+i*.047,.018),(.44,.009,.009),"wood",root,.001)
    for x in (-.16,-.08,0,.08,.16):
        api.line(root.name+"__woven_thread",[(x,-.308,.022),(x,.308,.022)],"paper_edge",.0015,root)
    for x in (-.24,.24):
        for y in (-.27,.27):
            api.box(root.name+"__bound_cord",(x,y,.022),(.040,.024,.044),"teal",root,.003)
    marker(api,root,"animation_pivot",(0,0,.02),"screen_lift_pivot")
    marker(api,root,"paper_output_anchor",(0,0,.042),"single_wet_paper_output")
    return root


def make_brush(api):
    root=asset(api,"tool_print_brush","印刷刷帚","F07",grip=(0,.13,.044))
    vv=[(-.135,-.115,0),(.135,-.115,0),(.105,.055,.012),(-.105,.055,.012),
        (-.11,-.115,.026),(.11,-.115,.026),(.078,.055,.046),(-.078,.055,.046)]
    ff=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    api.mesh(root.name+"__bound_paper_bristles",vv,ff,"paper_edge",root)
    for i in range(11):
        xx=-.1+i*.02
        api.line(root.name+"__fibre",[(xx,-.114,.027),(xx*.74,.047,.047)],"wood_light",.0018,root)
    api.box(root.name+"__teal_binding",(0,.045,.03),(.205,.038,.050),"teal",root,.005)
    api.cyl(root.name+"__bamboo_handle",(0,.13,.045),.026,.18,"wood_light",root,8,(math.pi/2,0,0))
    api.cyl(root.name+"__bamboo_node",(0,.175,.045),.029,.012,"wood",root,8,(math.pi/2,0,0))
    marker(api,root,"animation_pivot",(0,.13,.044),"brush_stroke_pivot")
    marker(api,root,"contact_point",(0,-.07,0),"paper_contact")
    return root


def make_dish(api):
    root=asset(api,"tool_ink_dish","浅墨碟","F07",grip=(0,0,.025))
    n=16;vv=[]
    for r,z in ((.100,0),(.130,.047),(.105,.047),(.080,.011)):
        vv.extend((r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for i in range(n))
    ff=[tuple(reversed(range(n)))]
    for ring in range(3):
        ff.extend((ring*n+i,ring*n+(i+1)%n,(ring+1)*n+(i+1)%n,(ring+1)*n+i) for i in range(n))
    ff.append(tuple(3*n+i for i in range(n)))
    api.mesh(root.name+"__faceted_dish",vv,ff,"wood_light",root)
    api.cyl(root.name+"__ink_surface",(0,0,.029),.096,.008,"ink",root,16)
    circle(api,root.name+"__paper_rim",root,0,0,.048,.117,"paper_edge",.004)
    marker(api,root,"contact_point",(0,0,.033),"brush_ink_contact")
    return root


def make_pad(api):
    root=asset(api,"tool_rubbing_pad","擦印包","F07",grip=(0,0,.133))
    n=12;vv=[]
    for rr,z in ((.115,0),(.115,.025),(.095,.064),(.032,.092)):
        vv.extend((rr*math.cos(i*math.tau/n),rr*math.sin(i*math.tau/n),z) for i in range(n))
    ff=[tuple(reversed(range(n))),tuple(3*n+i for i in range(n))]
    for ring in range(3):
        ff.extend((ring*n+i,ring*n+(i+1)%n,(ring+1)*n+(i+1)%n,(ring+1)*n+i) for i in range(n))
    api.mesh(root.name+"__folded_paper_wrap",vv,ff,"paper",root)
    api.cyl(root.name+"__rubbing_sole",(0,0,.008),.116,.016,"ink",root,12)
    for i in range(12):
        a=i*math.tau/12
        api.line(root.name+"__wrap_fold",[(.03*math.cos(a),.03*math.sin(a),.093),
                 (.095*math.cos(a),.095*math.sin(a),.065),(.114*math.cos(a),.114*math.sin(a),.028)],
                 "paper_edge",.0016,root)
    api.cyl(root.name+"__handle",(0,0,.125),.037,.075,"wood_light",root,10)
    api.cyl(root.name+"__tie",(0,0,.098),.041,.019,"teal",root,10)
    marker(api,root,"animation_pivot",(0,0,.125),"rubbing_pivot")
    marker(api,root,"contact_point",(0,0,0),"paper_contact")
    return root


def make_stamp(api):
    root=asset(api,"tool_stamp","云钮朱印章","F08",grip=(0,0,.235))
    api.box(root.name+"__seal_sole",(0,0,.018),(.235,.235,.036),"wood_dark",root,.008)
    api.box(root.name+"__seal_body",(0,0,.098),(.22,.22,.15),"red",root,.012)
    api.box(root.name+"__carved_shoulder",(0,0,.178),(.232,.232,.024),"wood_light",root,.008)
    knob=[(-.090,.190),(.090,.190),(.098,.212),(.088,.238),(.065,.249),(.047,.246),
          (.040,.275),(.020,.290),(-.020,.290),(-.040,.275),(-.047,.246),(-.065,.249),(-.088,.238),(-.098,.212)]
    profile(api,root.name+"__cloud_button",root,knob,.085,"red")
    api.line(root.name+"__front_frame",[(-.087,-.112,.045),(.087,-.112,.045),(.087,-.112,.151),
             (-.087,-.112,.151),(-.087,-.112,.045)],"paper_edge",.0035,root)
    for side in (-1,1):
        motif=[(.068,.060),(.068,.136),(.018,.136),(.018,.103),(.048,.103),(.048,.120),(.033,.120)]
        api.line(root.name+"__square_scroll",[(side*x,-.114,z) for x,z in motif],"paper_edge",.0035,root)
    api.line(root.name+"__cloud_carving",[(-.078,-.044,.217),(-.06,-.044,.237),(-.038,-.044,.222),
             (0,-.044,.210),(.038,-.044,.222),(.06,-.044,.237),(.078,-.044,.217)],"paper_edge",.003,root)
    api.line(root.name+"__silk_loop",[(0,.045,.266),(.043,.082,.252),(.058,.09,.215),
             (.027,.082,.193),(0,.045,.266)],"teal",.004,root)
    marker(api,root,"animation_pivot",(0,0,.235),"stamp_handle_pivot")
    marker(api,root,"contact_point",(0,0,0),"stamp_sole_contact")
    return root


def make_inkpad(api):
    root=asset(api,"tool_ink_pad","朱砂印泥","F08",grip=(0,0,.025))
    api.box(root.name+"__tray",(0,0,.024),(.29,.26,.048),"wood_dark",root,.012)
    api.box(root.name+"__red_cushion",(0,0,.052),(.23,.20,.016),"red",root,.008)
    rect(api,root.name+"__rim",root,0,0,.05,.266,.236,"wood_light",.003)
    marker(api,root,"contact_point",(0,0,.06),"stamp_ink_contact")
    return root


def make_block(api,art):
    root=asset(api,"tool_print_block","首款双人工坊雕版","F07",grip=(0,0,.035))
    api.box(root.name+"__block",(0,0,.031),(.51,.69,.062),"wood_dark",root,.012)
    api.box(root.name+"__carved_face",(0,0,.065),(.46,.64,.010),"wood_light",root,.004)
    ticket_layer(api,root,root.name+"__first_pair_engraving",art,.40,.60,.071)
    rect(api,root.name+"__outer_rule",root,0,0,.072,.478,.658,"paper_edge",.003)
    for sx in (-1,1):
        for sy in (-1,1):
            xx,yy=sx*.232,sy*.322
            pts=[(0,.04),(0,0),(.04,0),(.04,.026),(.015,.026),(.015,.013)]
            api.line(root.name+"__square_scroll_corner",[(xx-sx*x,yy-sy*y,.073) for x,y in pts],
                     "paper_edge",.0022,root)
    marker(api,root,"paper_anchor",(0,0,.075),"single_dry_paper_mount")
    root["pair_key"]=PAIR_KEY
    root["engraving_status"]="formal reference image mapped onto independent carved board; not sculpted glyph relief"
    return root


def make_woodcut(api,character,art):
    root=asset(api,"woodcut_"+character,"纸团木刻" if character=="zhituan" else "印桃木刻","F07",role="replaceable_engraving_layer")
    api.box(root.name+"__wood_plate",(0,0,.009),(.17,.17,.018),"wood_dark",root,.005)
    circle(api,root.name+"__medallion",root,0,0,.021,.073,"wood_light",.003)
    # Head portrait inside its original top circular medallion; original UVs preserved.
    cx,cy,rr=(321,148,86) if character=="zhituan" else (702,148,86)
    verts=[(0,0,.022)];uvs=[(cx/1024,1-cy/1536)]
    for i in range(32):
        a=i*math.tau/32
        verts.append((.068*math.cos(a),.068*math.sin(a),.022))
        uvs.append(((cx+rr*math.cos(a))/1024,1-(cy-rr*math.sin(a))/1536))
    faces=[(0,i+1,(i+1)%32+1) for i in range(32)]
    uv_mesh(api,root.name+"__formal_portrait",root,verts,faces,uvs,art,"character_woodcut")
    root["character_id"]=character;root["compositor_ready"]=False
    root["scope"]="standalone first-pair portrait plate; remaining four characters not supplied"
    return root


def make_red_layer(api,art):
    root=asset(api,"layer_red_seal","首款朱印覆盖层","F08",role="ticket_overlay_layer")
    ticket_layer(api,root,root.name+"__red_marks",art,.36,.54,0,True)
    root["pair_key"]=PAIR_KEY;root["activation"]="toggle this group once after black -> red succeeds"
    root["mount_height_above_paper_root_m"]=.0073
    return root


def make_receipt(api):
    root=asset(api,"marker_delivery_receipt","交付回执标记","F09",role="fixed_feedback_marker")
    api.box(root.name+"__base",(0,0,.012),(.17,.13,.024),"teal",root,.007)
    api.box(root.name+"__wood_spine",(0,.018,.135),(.022,.025,.24),"wood_light",root,.003)
    api.box(root.name+"__red_paper_tag",(0,0,.17),(.14,.012,.20),"red",root,.004)
    api.text(root.name+"__receipt_character","收",(0,-.009,.17),.085,"paper",(math.pi/2,0,0),root)
    marker(api,root,"feedback_anchor",(0,0,.28),"success_feedback_origin")
    root["inventory_units"]=0;root["new_gameplay_step"]=False
    return root


def build_props(api,art_path):
    art=texture_material(art_path)
    roots=[make_paper(api,state,art) for state in ("wet","dry","black","red")]
    roots += [make_screen(api),make_brush(api),make_dish(api),make_pad(api),
              make_stamp(api),make_inkpad(api),make_block(api,art),
              make_woodcut(api,"zhituan",art),make_woodcut(api,"yintao",art),
              make_red_layer(api,art),make_receipt(api)]
    return roots
