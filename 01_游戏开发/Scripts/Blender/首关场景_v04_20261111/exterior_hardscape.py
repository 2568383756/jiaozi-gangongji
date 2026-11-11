"""Exterior paper terrain, paving and quiet courtyard furnishings.

The original x=0..12 / y=0..8 floor is a void in the new terrain ring.
No production station, doorway or internal floor is modified by this module.
"""

from math import sin, cos, pi
from random import Random


def _root(api,name,loc=(0,0,0),role="exterior_dressing"):
    ob=api.empty(name,loc)
    ob["asset_id"]=name
    ob["role"]=role
    ob["task"]="F15"
    ob["non_interactive"]=True
    ob["version"]="v04_20261111"
    return ob


def _append_prism(vertices,faces,outline,bottom,top):
    start=len(vertices)
    n=len(outline)
    vertices.extend((x,y,bottom) for x,y in outline)
    vertices.extend((x,y,top) for x,y in outline)
    faces.append(tuple(start+i for i in range(n-1,-1,-1)))
    faces.append(tuple(start+n+i for i in range(n)))
    faces.extend((start+i,start+(i+1)%n,start+(i+1)%n+n,start+i+n) for i in range(n))


def _prism(api,name,outline,bottom,top,mat,parent):
    vv,ff=[],[]
    _append_prism(vv,ff,outline,bottom,top)
    return api.mesh(name,vv,ff,mat,parent=parent)


def _rect(a,b,c,d):
    return [(a,c),(b,c),(b,d),(a,d)]


def _clipped(cx,cy,w,d,rng):
    """A flat paper-stone polygon with deliberately non-identical clipped corners."""
    x0,x1=cx-w/2,cx+w/2
    y0,y1=cy-d/2,cy+d/2
    cuts=[rng.uniform(.035,.085)*min(w,d) for _ in range(4)]
    return [(x0+cuts[0],y0),(x1-cuts[1],y0),(x1,y0+cuts[1]),
            (x1,y1-cuts[2]),(x1-cuts[2],y1),(x0+cuts[3],y1),
            (x0,y1-cuts[3]),(x0,y0+cuts[0])]


def _ground(api):
    root=_root(api,"exterior_paper_ground",role="exterior_ground")
    root["outer_bounds"]=[-4,16,-3.5,11.5]
    root["inner_void"]=[0,12,0,8]
    root["top_z"]=-.14
    root["bottom_z"]=-.40
    root["reserved_tree_centers"]="(-2.35,6.7); (14.35,8.4); (1.5,10.1)"
    pieces=[
        [(-4,-2.75),(-3.25,-3.5),(15.25,-3.5),(16,-2.75),(16,0),(-4,0)],
        _rect(-4,0,0,8),_rect(12,16,0,8),
        [(-4,8),(16,8),(16,10.75),(15.25,11.5),(-3.25,11.5),(-4,10.75)]
    ]
    for layer,(bottom,top,mat) in enumerate([
            (-.40,-.285,"garden_edge"),(-.285,-.270,"paper_edge"),
            (-.270,-.190,"garden_edge"),(-.190,-.140,"garden_soil")]):
        vv,ff=[],[]
        for outline in pieces:
            _append_prism(vv,ff,outline,bottom,top)
        api.mesh(f"exterior_ground_paper_layer_{layer}",vv,ff,mat,parent=root)
    return root


def _paving(api,name,rectangles,tiles,seed):
    root=_root(api,name,role="exterior_path")
    root["tile_count"]=len(tiles)
    root["top_z"]=0.0
    root["underlay_z"]=-.14
    base_v,base_f=[],[]
    for a,b,c,d in rectangles:
        _append_prism(base_v,base_f,_rect(a,b,c,d),-.14,-.035)
    api.mesh(name+"_continuous_paper_underlay",base_v,base_f,"paper_edge",parent=root)
    rng=Random(seed)
    sets={"paving":[[],[]],"paving_light":[[],[]],"paper_edge":[[],[]]}
    for index,(cx,cy,w,d) in enumerate(tiles):
        outline=_clipped(cx,cy,w,d,rng)
        mat="paving_light" if index%4==1 else "paving"
        _append_prism(*sets[mat],outline,-.029,0)
        # Tiny exposed lamination underneath each separate paving slab.
        _append_prism(*sets["paper_edge"],outline,-.036,-.029)
    for mat,(vv,ff) in sets.items():
        if vv:
            api.mesh(name+"_slabs_"+mat,vv,ff,mat,parent=root)
    return root


def _entry_tiles(y0,y1):
    tiles=[]
    for row in range(5):
        for col in range(4):
            tiles.append((4.8+(col+.5)*.6,y0+(row+.5)*(y1-y0)/5,
                          .579,(y1-y0)/5-.021))
    return tiles


def _ring_tiles():
    spans=[]
    for y0,y1 in [(-.9,-.15),(8.15,8.9)]:
        spans.extend([(-.9,4.8,y0,y1),(7.2,12.9,y0,y1)])
    spans.extend([(-.9,-.15,-.15,8.15),(12.15,12.9,-.15,8.15)])
    tiles=[]
    for a,b,c,d in spans:
        horizontal=(b-a)>(d-c)
        length=(b-a) if horizontal else (d-c)
        count=max(1,round(length/.68))
        step=length/count
        for i in range(count):
            if horizontal:
                tiles.append((a+(i+.5)*step,(c+d)/2,step-.024,d-c-.018))
            else:
                tiles.append(((a+b)/2,c+(i+.5)*step,b-a-.018,step-.024))
    return spans,tiles


def _stone_lamp(api,name,xy):
    root=_root(api,name,(*xy,-.14))
    root["decor_class"]="small_stone_lantern"
    rng=Random(73)
    _prism(api,name+"_base",_clipped(0,0,.46,.46,rng),0,.10,"stone",root)
    _prism(api,name+"_second_step",_clipped(0,0,.31,.31,rng),.10,.145,"paving",root)
    api.box(name+"_stem",(0,0,.24),(.14,.14,.20),"stone",parent=root,bevel=.017)
    api.box(name+"_chamber_bottom",(0,0,.36),(.35,.35,.055),"paving",parent=root,bevel=.018)
    for xx in (-.14,.14):
        for yy in (-.14,.14):
            api.box(name+f"_corner_{xx}_{yy}",(xx,yy,.49),(.045,.045,.23),
                    "stone",parent=root,bevel=.007)
    # Recessed muted paper screens, with no emissive or bright gameplay colour.
    for yy in (-.132,.132):
        api.box(name+f"_paper_screen_y_{yy}",(0,yy,.49),(.215,.012,.17),
                    "paper_edge",parent=root,bevel=.003)
    for xx in (-.132,.132):
        api.box(name+f"_paper_screen_x_{xx}",(xx,0,.49),(.012,.215,.17),
                    "paper_edge",parent=root,bevel=.003)
    api.box(name+"_lintel",(0,0,.615),(.36,.36,.045),"paving",parent=root,bevel=.01)
    vv=[(-.28,-.28,.645),(.28,-.28,.645),(.28,.28,.645),(-.28,.28,.645),
        (0,0,.79),(-.28,-.28,.615),(.28,-.28,.615),(.28,.28,.615),(-.28,.28,.615)]
    ff=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(8,7,6,5),
        (0,5,6,1),(1,6,7,2),(2,7,8,3),(3,8,5,0)]
    api.mesh(name+"_folded_stone_cap",vv,ff,"paving_light",parent=root)
    api.cyl(name+"_finial",(0,0,.82),.035,.075,"stone",parent=root,vertices=6)
    return root


def _bench(api):
    root=_root(api,"exterior_front_left_bench",(1.45,-2.15,-.14))
    root["decor_class"]="courtyard_bench"
    # A visible backrest prevents confusion with the single-slot shared table.
    for yy in (-.155,.155):
        api.box(f"bench_seat_plank_{yy}",(0,yy,.43),(1.90,.29,.07),
                "wood",parent=root,bevel=.025)
    for xx in (-.70,.70):
        for yy in (-.19,.19):
            api.box(f"bench_leg_{xx}_{yy}",(xx,yy,.21),(.115,.115,.42),
                    "wood_dark",parent=root,bevel=.015)
        api.box(f"bench_back_post_{xx}",(xx,.22,.59),(.075,.07,.58),
                "wood_dark",parent=root,bevel=.01)
    api.box("bench_under_stretcher",(0,0,.18),(1.45,.07,.075),
            "wood_dark",parent=root,bevel=.01)
    for zz in (.63,.79):
        api.box(f"bench_back_slats_{zz}",(0,.22,zz),(1.84,.06,.115),
                "wood",parent=root,bevel=.017)
    # A few thin darker paper grain marks instead of dense procedural detail.
    for i,xx in enumerate((-.45,.16,.62)):
        api.line(f"bench_worn_seat_fold_{i}",[(xx-.10,-.08,.466),(xx+.10,-.077,.466)],
                 "paper_edge",radius=.002,parent=root)
    return root


def _jar_and_broom(api):
    root=_root(api,"exterior_water_jar_and_broom",(-2.10,1.35,-.14))
    root["decor_class"]="earthen_jar_and_bamboo_broom"
    n=14
    profile=[(.20,0),(.27,.06),(.33,.23),(.31,.41),(.24,.54),
             (.24,.59),(.213,.59),(.213,.53),(.265,.40),(.24,.30)]
    vv=[(r*cos(2*pi*i/n),r*sin(2*pi*i/n),z) for r,z in profile for i in range(n)]
    ff=[]
    for j in range(len(profile)-1):
        for i in range(n):
            ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    ff.append(tuple(range(n-1,-1,-1)))
    api.mesh("earthen_jar_folded_body",vv,ff,"garden_edge",parent=root)
    api.cyl("earthen_jar_dark_interior",(0,0,.30),.235,.012,"wood_dark",parent=root,vertices=n)
    for z,r in [(.08,.28),(.54,.241),(.588,.241)]:
        api.line(f"earthen_jar_layer_edge_{z}",
                 [(r*cos(2*pi*i/n),r*sin(2*pi*i/n),z) for i in range(n+1)],
                 "paper_edge",radius=.006,parent=root)
    # Leaning broom is supported by the jar. All of it stays off the stone walk.
    api.line("broom_bamboo_handle",[(-.48,.06,.14),(-.28,.07,1.10)],
             "wood",radius=.017,parent=root)
    vv=[(-.64,.015,.025),(-.33,.015,.025),(-.44,.02,.27),
        (-.64,.095,.025),(-.33,.095,.025),(-.44,.09,.27)]
    api.mesh("broom_folded_straw",vv,[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],
             "paper_edge",parent=root)
    for i in range(6):
        xx=-.62+i*.052
        api.line(f"broom_straw_ridge_{i}",[(xx,.009,.03),(-.44+(xx+.48)*.15,.016,.245)],
                 "wood",radius=.003,parent=root)
    api.box("broom_binding",(-.44,.052,.235),(.09,.095,.035),
            "wood_dark",parent=root,bevel=.004)
    return root


def _scattered_stones(api):
    root=_root(api,"exterior_small_paper_stones")
    root["decor_class"]="small_flat_stones"
    locations=[(-3.25,3.4),(-1.7,9.45),(3.5,9.8),(10.2,10.2),
               (14.7,4.0),(13.55,-2.55),(2.6,-3.0),(-2.65,-2.65)]
    rng=Random(11103)
    vv,ff=[],[]
    for x,y in locations:
        w,d=rng.uniform(.25,.43),rng.uniform(.17,.31)
        outline=_clipped(x,y,w,d,rng)
        _append_prism(vv,ff,outline,-.14,-.14+rng.uniform(.035,.065))
    root["stone_count"]=len(locations)
    api.mesh("exterior_scattered_flat_stone_mesh",vv,ff,"paving",parent=root)
    return root


def build_exterior_hardscape(api,spec):
    if tuple(spec["base"]["floor"])!=(12,8):
        raise ValueError("Exterior v03 expects the unchanged 12 x 8 m inner level")
    api.collection("EXTERIOR_01_Paper_Ground")
    roots=[_ground(api)]
    api.collection("EXTERIOR_02_Paving")
    roots.append(_paving(api,"exterior_path_front_entry",[(4.8,7.2,-3.5,0)],
                         _entry_tiles(-3.5,0),11031))
    roots.append(_paving(api,"exterior_path_rear_entry",[(4.8,7.2,8,11.5)],
                         _entry_tiles(8,11.5),11032))
    spans,tiles=_ring_tiles()
    roots.append(_paving(api,"exterior_path_perimeter",spans,tiles,11033))
    api.collection("EXTERIOR_03_Courtyard_Props")
    roots.append(_stone_lamp(api,"exterior_stone_lamp_front_left",(-2.6,-1.75)))
    roots.append(_stone_lamp(api,"exterior_stone_lamp_front_right",(14.45,-1.60)))
    roots.append(_bench(api))
    roots.append(_jar_and_broom(api))
    roots.append(_scattered_stones(api))
    return roots
