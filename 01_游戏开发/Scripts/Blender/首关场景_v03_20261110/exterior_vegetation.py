"""Batched folded-paper ginkgo trees and non-interactive exterior planting.

Uses only the modelling API and Python's standard library.  The inner
12 x 8 m playfield, entrance axis and one-metre outer walk remain clear.
"""

import math
import random


GROUND_Z = -.14


def _add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def _sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _mul(a, k):
    return tuple(v * k for v in a)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _unit(v):
    length = math.sqrt(sum(x*x for x in v))
    return _mul(v, 1.0 / max(length, 1e-9))


class _Batch:
    """Accumulate all components of one material into one editable mesh."""

    def __init__(self):
        self.buffers = {}

    def add(self, mat, vertices, faces):
        verts, polys = self.buffers.setdefault(mat, ([], []))
        offset = len(verts)
        verts.extend(vertices)
        polys.extend(tuple(index + offset for index in face) for face in faces)

    def emit(self, api, root, prefix):
        result = []
        for mat, (verts, faces) in self.buffers.items():
            if not verts:
                continue
            ob = api.mesh(prefix + "__" + mat, verts, faces, mat, parent=root)
            ob["role"] = "exterior_vegetation_mesh"
            ob["non_interactive"] = True
            result.append(ob)
        return result


def _branch(batch, start, end, radius_a, radius_b, phase=0.0, sides=7):
    """A tapering polygonal paper branch, not a smooth cylindrical tube."""
    direction = _unit(_sub(end, start))
    reference = (0, 0, 1) if abs(direction[2]) < .93 else (0, 1, 0)
    u = _unit(_cross(direction, reference))
    v = _cross(direction, u)
    vertices = []
    for origin, radius in ((start, radius_a), (end, radius_b)):
        for i in range(sides):
            angle = phase + 2 * math.pi * i / sides
            radial = _add(_mul(u, math.cos(angle)*radius),
                          _mul(v, math.sin(angle)*radius))
            vertices.append(_add(origin, radial))
    faces = [tuple(reversed(range(sides))), tuple(range(sides, sides*2))]
    for i in range(sides):
        j = (i+1) % sides
        faces.append((i,j,sides+j,sides+i))
    batch.add("bark", vertices, faces)


def _leaf_axes(normal, roll):
    n = _unit(normal)
    reference = (0,0,1) if abs(n[2]) < .94 else (0,1,0)
    u = _unit(_cross(reference, n))
    v = _unit(_cross(n, u))
    uu = _add(_mul(u,math.cos(roll)),_mul(v,math.sin(roll)))
    vv = _add(_mul(v,math.cos(roll)),_mul(u,-math.sin(roll)))
    return uu, vv, n


def _fan_leaf(batch, center, width, normal, roll, mat, thin=False):
    """Broad fan blade, central notch, raised fold and an independent petiole.

    All parts are batched geometry of this single leaf.  The contour has a
    shallow centre notch, deliberately distinct from round or pointed foliage.
    """
    u, v, n = _leaf_axes(normal, roll)
    origin = _add(center, _mul(v, -.33*width))

    def pos(a, b, c=0.0):
        return _add(origin, _add(_mul(u,a*width),
                    _add(_mul(v,b*width),_mul(n,c*width))))

    contour = [(0,0),(-.50,.23),(-.48,.42),(-.36,.62),(-.17,.73),
               (-.035,.76),(0,.66),(.035,.76),(.17,.73),
               (.36,.62),(.48,.42),(.50,.23)]
    vertices = [pos(a,b) for a,b in contour]
    ridge = pos(0,.32,.065)
    vertices.append(ridge)
    ridge_index = len(vertices)-1
    faces = [(ridge_index,i,(i+1)%len(contour)) for i in range(len(contour))]
    batch.add(mat, vertices, faces)
    # A visible thin ochre paper edge also gives the leaf a tiny real thickness.
    thickness = .003 if thin else .005
    lower = [_add(q,_mul(n,-thickness)) for q in vertices[:-1]]
    edge_vertices = vertices[:-1] + lower
    size = len(contour)
    edge_faces = [(i,(i+1)%size,(i+1)%size+size,i+size) for i in range(size)]
    batch.add("ginkgo_ochre",edge_vertices,edge_faces)
    batch.add(mat,lower,[tuple(reversed(range(size)))])
    # Two broad folded planes meet on a short central crease, with no vein noise.
    fold_vertices = [pos(-.009,.03,.012),pos(.009,.03,.012),
                     pos(.008,.32,.069),pos(-.008,.32,.069),
                     pos(.003,.65,.005),pos(-.003,.65,.005)]
    batch.add("ginkgo_light",fold_vertices,[(0,1,2,3),(3,2,4,5)])
    stem_vertices = [pos(-.012,-.19,-.002),pos(.012,-.19,-.002),
                     pos(.010,.025,0),pos(-.010,.025,0)]
    batch.add("ginkgo_ochre",stem_vertices,[(0,1,2,3)])


def _meta(root, asset_id, **values):
    root["role"] = "exterior_vegetation"
    root["non_interactive"] = True
    root["task"] = "F15"
    root["asset_id"] = asset_id
    root["version"] = "v03_20261110"
    root["collision"] = "none; exterior scenery only"
    for key, value in values.items():
        root[key] = value


def _ginkgo(api, name, xy, height, radius, leaf_count, seed):
    rng = random.Random(seed)
    root = api.empty(name,(xy[0],xy[1],GROUND_Z),size=.20)
    _meta(root,"env_ginkgo",leaf_count=leaf_count,height=height,
          crown_radius=radius,tree_count=1)
    batch = _Batch()
    trunk_points = [(0,0,0),(.035,-.015,height*.22),
                    (-.045,.025,height*.43),(.035,.005,height*.60),
                    (-.055,.05,height*.76)]
    trunk_radii = [.19,.145,.11,.075,.030]
    for index in range(len(trunk_points)-1):
        _branch(batch,trunk_points[index],trunk_points[index+1],
                trunk_radii[index],trunk_radii[index+1],phase=.16*index)
    # Three low paper roots tie the angular trunk visibly into the soil.
    for angle in (.1,2.4,4.5):
        end = (.34*math.cos(angle),.34*math.sin(angle),.025)
        _branch(batch,(0,0,.13),end,.095,.027,phase=angle,sides=6)

    # Offset branching lobes create a broad, asymmetric fan crown with air gaps.
    crowns = [(-.56*radius,-.10*radius,.64*height),
              (.53*radius,-.06*radius,.69*height),
              (-.24*radius,.47*radius,.76*height),
              (.32*radius,.37*radius,.84*height),
              (.04*radius,-.39*radius,.82*height),
              (-.10*radius,.02*radius,.90*height)]
    for index,target in enumerate(crowns):
        start = trunk_points[2 if index < 3 else 3]
        bend = (target[0]*.58,target[1]*.65,(start[2]+target[2])*.51)
        _branch(batch,start,bend,.085 if index<3 else .058,.044,phase=index*.37)
        _branch(batch,bend,target,.045,.017,phase=index*.49)
        for fork in (-1,1):
            twig = (target[0]+fork*.16,target[1]+.12,
                    min(height-.30,target[2]+.23))
            _branch(batch,target,twig,.022,.008,phase=fork*.25,sides=5)

    for index in range(leaf_count):
        cx,cy,cz = crowns[index % len(crowns)]
        width = rng.uniform(.28,.49) if radius > 1 else rng.uniform(.25,.42)
        center = [cx+rng.uniform(-.32,.32),cy+rng.uniform(-.30,.30),
                  cz+rng.uniform(-.22,.16)]
        # Reserve the full blade radius so the crown does not enter the playfield.
        max_center_radius = radius - .37
        length = math.hypot(center[0],center[1])
        if length > max_center_radius:
            center[0] *= max_center_radius/length
            center[1] *= max_center_radius/length
        center[2] = min(height-.255,max(height*.49,center[2]))
        radial = math.atan2(center[1],center[0])
        if index % 5 == 0:
            normal = (math.cos(radial)*.8,math.sin(radial)*.8,.62)
        else:
            # Front/up-facing fans read clearly from the fixed high game camera.
            normal = (rng.uniform(-.65,.65),rng.uniform(-1.0,-.3),rng.uniform(.35,.9))
        mat_roll = rng.random()
        mat = "ginkgo_gold" if mat_roll < .58 else "ginkgo_light" if mat_roll < .89 else "ginkgo_ochre" if mat_roll < .97 else "sage"
        _fan_leaf(batch,tuple(center),width,normal,rng.uniform(-.65,.65),mat)
    objects = batch.emit(api,root,name)
    root["mesh_batch_count"] = len(objects)
    root["branch_lobes"] = len(crowns)
    return root


def _grass_blade(batch, base, angle, height, width, lean, mat):
    """A folded ribbon with a wide middle and a tapered end, never a cylinder."""
    dx,dy = math.cos(angle),math.sin(angle)
    lateral = (-dy,dx,0)
    vertices = []
    for fraction,halfwidth in ((0,width*.26),(.42,width*.50),(.76,width*.30),(1,0)):
        center = (base[0]+dx*lean*fraction*fraction,
                  base[1]+dy*lean*fraction*fraction,
                  base[2]+height*fraction)
        for side in (-1,0,1):
            ridge = width*.13*(1-fraction) if side==0 else 0
            vertices.append((center[0]+lateral[0]*halfwidth*side,
                             center[1]+lateral[1]*halfwidth*side,
                             center[2]+ridge))
    faces = []
    for row in range(3):
        i = row*3
        faces.extend(((i,i+1,i+4,i+3),(i+1,i+2,i+5,i+4)))
    batch.add(mat,vertices,faces)


def _shrub_leaf(batch, base, angle, length, mat):
    dx,dy = math.cos(angle),math.sin(angle)
    u=(-dy,dx,0)
    tip=(base[0]+dx*length*.8,base[1]+dy*length*.8,base[2]+length*.55)
    middle=(base[0]+dx*length*.42,base[1]+dy*length*.42,base[2]+length*.49)
    vertices=[base,_add(middle,_mul(u,-length*.25)),tip,
              _add(middle,_mul(u,length*.25)),_add(middle,(0,0,.023))]
    batch.add(mat,vertices,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)])


def _seed_head(batch, base, angle, height):
    dx,dy=math.cos(angle),math.sin(angle)
    tip=(base[0]+dx*.06,base[1]+dy*.06,height)
    lateral=(-dy*.003,dx*.003,0)
    batch.add("grass",[_add(base,lateral),_sub(base,lateral),
                       _sub(tip,lateral),_add(tip,lateral)],[(0,1,2,3)])
    # A few pale paper seed scales, rather than an opaque cream blob.
    u=(-dy,dx,0)
    for i in range(5):
        zz=height-.085+i*.017
        side=-1 if i%2 else 1
        center=(tip[0],tip[1],zz)
        points=[center,_add(center,_add(_mul(u,side*.020),(0,0,.008))),
                _add(center,(0,0,.024)),_add(center,_mul(u,-side*.006))]
        batch.add("paper_edge",points,[(0,1,2,3)])


def _rounded_paper_leaf(batch, base, angle, tilt, width, length, mat):
    """One broad round-ended petal cut from 6 mm paper, with a small fold.

    Twenty-four contour segments keep the silhouette rounded.  A very low
    central ridge bends a thin sheet; it is not a swollen or spherical leaf.
    """
    dx,dy=math.cos(angle),math.sin(angle)
    u=(dy,-dx,0)
    v=(dx*math.cos(tilt),dy*math.cos(tilt),math.sin(tilt))
    n=(-dx*math.sin(tilt),-dy*math.sin(tilt),math.cos(tilt))

    def pos(a,b,c=0):
        return _add(base,_add(_mul(u,a),_add(_mul(v,b),_mul(n,c))))

    count=24
    contour=[]
    for i in range(count):
        theta=2*math.pi*i/count
        # A softly obovate, almost circular lobe: broad free end, hidden base.
        xx=width*.5*math.sin(theta)*(.88+.12*math.cos(theta))
        yy=length*.5*(1+math.cos(theta))
        contour.append(pos(xx,yy))
    fold=.0065
    ridge=pos(0,length*.52,fold)
    batch.add(mat,contour+[ridge],[(count,i,(i+1)%count) for i in range(count)])
    lower=[_add(q,_mul(n,-.006)) for q in contour]
    batch.add(mat,lower,[tuple(reversed(range(count)))])
    batch.add("moss",contour+lower,
              [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)])
    # A narrow subdued crease, with no veins, grass tips or high seed stems.
    crease_mat="sage" if mat in ("moss","grass") else "grass"
    strip=[pos(-.0009,length*.12,fold*.23+.0004),
           pos(.0009,length*.12,fold*.23+.0004),
           pos(.0009,length*.52,fold+.0004),
           pos(-.0009,length*.52,fold+.0004),
           pos(.0006,length*.82,fold*.375+.0004),
           pos(-.0006,length*.82,fold*.375+.0004)]
    batch.add(crease_mat,strip,[(0,1,2,3),(3,2,4,5)])


def _grass_cluster(api, name, xy, index):
    rng=random.Random(8000+index)
    root=api.empty(name,(xy[0],xy[1],GROUND_Z),size=.10)
    leaf_count=12+index%5
    _meta(root,"env_grass_cluster",cluster_count=1,blade_count=0,
          leaf_count=leaf_count,foliage_style="rounded_folded_paper")
    batch=_Batch()
    # Five overlapping dark low lobes, five greener middle lobes, then a few
    # pale upper petals reproduce the reference's layered round-paper clump.
    ring_counts=(5,5,leaf_count-10)
    for ring,count in enumerate(ring_counts):
        phase=.33+ring*.67+index*.21
        for i in range(count):
            angle=phase+i*2*math.pi/count+rng.uniform(-.13,.13)
            if ring==0:
                width,length=rng.uniform(.23,.28),rng.uniform(.24,.27)
                tilt=rng.uniform(.27,.40)
                rr,z=.012,.013
                mat="grass"
            elif ring==1:
                width,length=rng.uniform(.20,.25),rng.uniform(.22,.25)
                tilt=rng.uniform(.56,.77)
                rr,z=.014,.043
                mat="moss"
            else:
                width,length=rng.uniform(.17,.23),rng.uniform(.18,.22)
                tilt=rng.uniform(.75,1.10)
                rr,z=.009,.069
                mat="sage"
            base=(rr*math.cos(angle),rr*math.sin(angle),z)
            _rounded_paper_leaf(batch,base,angle,tilt,width,length,mat)
    root["pale_seed_heads"]=0
    root["height_limit"] = .28
    root["footprint_radius_max"] = .29
    root["paper_thickness"] = .006
    batch.emit(api,root,name)
    return root


def _fallen(api):
    root=api.empty("env_fallen_ginkgo_leaves",(0,0,GROUND_Z),size=.15)
    _meta(root,"env_fallen_leaves",leaf_count=30,cluster_count=1)
    batch=_Batch()
    rng=random.Random(1030)
    for i in range(30):
        region=i%4
        if region==0:
            x,y=rng.uniform(-3.5,-1.45),rng.uniform(-2.9,10.8)
        elif region==1:
            x,y=rng.uniform(13.45,15.5),rng.uniform(-2.9,10.8)
        else:
            x=rng.uniform(-2.8,3.9) if i%3 else rng.uniform(8.2,15.0)
            y=rng.uniform(-3.1,-1.55) if region==2 else rng.uniform(9.45,11.05)
        _fan_leaf(batch,(x,y,.016),rng.uniform(.18,.31),(0,0,1),
                  rng.uniform(0,2*math.pi),"ginkgo_gold" if i%3 else "ginkgo_light",thin=True)
    batch.emit(api,root,"env_fallen_ginkgo_leaves")
    return root


def build_exterior_vegetation(api, spec):
    """Create three trees, 22 planting clusters and 30 scattered exterior leaves."""
    roots=[]
    api.collection("Exterior/Vegetation/Ginkgo")
    trees=[("env_ginkgo_west",(-2.35,6.7),3.6,1.25,140,3301),
           ("env_ginkgo_east",(14.35,8.4),4.0,1.35,170,3302),
           ("env_ginkgo_north",(1.5,10.1),2.7,.95,110,3303)]
    for name,xy,height,radius,count,seed in trees:
        roots.append(_ginkgo(api,name,xy,height,radius,count,seed))
    api.collection("Exterior/Vegetation/Grasses")
    placements=[(-2.9,-.4),(-1.65,1.7),(-3.1,3.6),(-1.7,5.0),(-3.3,8.7),
                (13.6,.0),(15.1,1.9),(13.65,4.7),(15.2,6.4),(15.0,9.9),
                (-2.9,-2.75),(.1,-2.15),(2.7,-2.8),(8.7,-2.3),(11.5,-2.8),(14.6,-2.3),
                (-2.8,10.3),(3.6,10.4),(8.7,10.1),(10.8,10.6),(13.2,10.8),(15.3,10.6)]
    for index,xy in enumerate(placements):
        roots.append(_grass_cluster(api,"env_grass_cluster_%02d"%(index+1),xy,index))
    api.collection("Exterior/Vegetation/FallenLeaves")
    roots.append(_fallen(api))
    return roots
