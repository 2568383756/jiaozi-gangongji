"""Three sculpted paper ginkgo trees and clustered fallen leaves, level 01 v05.

The canopy uses large rounded fan sheets spreading from four offset branch
tips. This module deliberately creates no grass or rosette roots.
"""

import math
import random

GROUND_Z = -.14


def _add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def _sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _mul(a, k):
    return tuple(value*k for value in a)


def _dot(a, b):
    return sum(a[i]*b[i] for i in range(3))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _unit(v):
    return _mul(v, 1.0/max(math.sqrt(_dot(v, v)), 1e-9))


class _Batch:
    def __init__(self):
        self.buffers = {}

    def add(self, material, vertices, faces):
        vv, ff = self.buffers.setdefault(material, ([], []))
        offset = len(vv)
        vv.extend(vertices)
        ff.extend(tuple(offset+i for i in face) for face in faces)

    def emit(self, api, root, prefix):
        result = []
        for material, (vertices, faces) in self.buffers.items():
            if vertices:
                ob = api.mesh(prefix+'__'+material, vertices, faces, material,
                              parent=root)
                ob['role'] = 'exterior_vegetation_mesh'
                ob['non_interactive'] = True
                result.append(ob)
        return result


def _meta(root, asset_id, **values):
    root['role'] = 'exterior_vegetation'
    root['non_interactive'] = True
    root['task'] = 'F15'
    root['asset_id'] = asset_id
    root['version'] = 'v05_20261111'
    root['collision'] = 'none; exterior scenery only'
    for key, value in values.items():
        root[key] = value


def _bezier(control, count=11):
    points = []
    for i in range(count):
        t = i/(count-1)
        factors = ((1-t)**3, 3*(1-t)**2*t, 3*(1-t)*t*t, t**3)
        points.append(tuple(sum(control[j][k]*factors[j] for j in range(4))
                            for k in range(3)))
    return points


def _swept_branch(batch, points, radii, sides=9, phase=.1):
    """Continuous tapered paper loft; parallel-transported rings avoid seams."""
    vertices, frames = [], []
    previous_u = None
    for index, (point, radius) in enumerate(zip(points, radii)):
        direction = _unit(_sub(points[min(index+1, len(points)-1)],
                               points[max(index-1, 0)]))
        if previous_u is None:
            u = _unit(_cross(direction, (0, 1, 0)))
        else:
            u = _unit(_sub(previous_u, _mul(direction, _dot(previous_u, direction))))
        v = _cross(direction, u)
        frames.append((point, radius, u, v))
        previous_u = u
        for k in range(sides):
            angle = phase+2*math.pi*k/sides
            # Broad flat paper facets, not rough radial noise.
            radial = _add(_mul(u, radius*math.cos(angle)),
                          _mul(v, radius*math.sin(angle)))
            vertices.append(_add(point, radial))
    faces = [tuple(range(sides-1, -1, -1)),
             tuple(range((len(points)-1)*sides, len(points)*sides))]
    for row in range(len(points)-1):
        for k in range(sides):
            a = row*sides+k
            b = row*sides+(k+1) % sides
            faces.append((a, b, b+sides, a+sides))
    batch.add('bark', vertices, faces)
    return frames


def _bark_folds(batch, frames):
    """Four quiet raised paper folds follow the curved trunk surface."""
    for angle in (.15, 1.85, 3.45, 5.05):
        vertices = []
        for point, radius, u, v in frames[1:-1]:
            radial = _add(_mul(u, math.cos(angle)), _mul(v, math.sin(angle)))
            across = _add(_mul(u, -math.sin(angle)), _mul(v, math.cos(angle)))
            center = _add(point, _mul(radial, radius+.002))
            half_width = min(.014, radius*.10)
            vertices.extend([_sub(center, _mul(across, half_width)),
                             _add(center, _mul(radial, .006)),
                             _add(center, _mul(across, half_width))])
        faces = []
        for i in range(len(frames)-3):
            a = i*3
            faces += [(a, a+1, a+4, a+3), (a+1, a+2, a+5, a+4)]
        batch.add('bark', vertices, faces)


def _leaf_axes(normal, roll):
    n = _unit(normal)
    reference = (0, 0, 1) if abs(n[2]) < .96 else (0, 1, 0)
    u = _unit(_cross(reference, n))
    v = _cross(n, u)
    return (_add(_mul(u, math.cos(roll)), _mul(v, math.sin(roll))),
            _add(_mul(v, math.cos(roll)), _mul(u, -math.sin(roll))), n)


def _fan_leaf(batch, center, width, normal, roll, material,
              thin=False, crown_bounds=None):
    """One complete rounded fan sheet with shallow notch and a gentle fold.

    Top and underside share the same triangulation, with closed edge faces.
    All normals use a counterclockwise contour in the right-handed leaf basis.
    Crown limits translate an intact leaf inward; they never clip its outline.
    """
    u, v, n = _leaf_axes(normal, roll)
    thickness = .003 if thin else .005

    def position(a, b, fold=0.0):
        return _add(_mul(u, a*width),
                    _add(_mul(v, (b-.34)*width), _mul(n, fold*width)))

    contour = [(0.0, 0.0)]
    # A long circular free edge with only a shallow central ginkgo cleft.
    # Right edge -> crown -> left edge gives a CCW sheet outline.
    for index in range(25):
        theta = math.radians(88-176*index/24)
        a = .50*math.sin(theta)
        b = .17+.57*math.cos(theta)
        if index == 12:
            b -= .045
        contour.append((a, b))
    upper = []
    for a, b in contour:
        curl = .010*(b/.74)**2-.005*(abs(a)/.5)**2
        upper.append(position(a, b, curl))
    upper.append(position(0, .34, .014))
    count = len(contour)
    top_faces = [(count, i, (i+1) % count) for i in range(count)]
    lower = [_sub(point, _mul(n, thickness)) for point in upper]
    stem_top = [position(-.008, -.115, -.002), position(.008, -.115, -.002),
                position(.008, .025, -.002), position(-.008, .025, -.002)]
    stem_bottom = [_sub(point, _mul(n, thickness)) for point in stem_top]
    all_relative = upper+lower+stem_top+stem_bottom
    cx, cy, cz = center
    if crown_bounds is not None:
        radius, height = crown_bounds
        limit = radius-.006
        a = cx*cx+cy*cy
        factor = 1.0
        if a > 1e-10:
            for x, y, _ in all_relative:
                b = 2*(cx*x+cy*y)
                c = x*x+y*y-limit*limit
                allowed = (-b+math.sqrt(max(0, b*b-4*a*c)))/(2*a)
                factor = min(factor, max(0, allowed))
        cx *= factor
        cy *= factor
        cz = min(cz, height-.006-max(point[2] for point in all_relative))

    def world(points):
        return [(x+cx, y+cy, z+cz) for x, y, z in points]

    offset = len(upper)
    underside_faces = [tuple(offset+i for i in reversed(face)) for face in top_faces]
    batch.add(material, world(upper+lower), top_faces+underside_faces)
    edges = [(i, i+count, (i+1) % count+count, (i+1) % count)
             for i in range(count)]
    # Edges use only contour vertices; the crease vertices are not part of rim.
    batch.add('ginkgo_ochre', world(upper[:count]+lower[:count]), edges)
    batch.add('ginkgo_ochre', world(stem_top+stem_bottom),
              [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
               (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])


def _ginkgo(api, name, xy, height, radius, cluster_counts, seed):
    rng = random.Random(seed)
    count = sum(cluster_counts)
    root = api.empty(name, (xy[0], xy[1], GROUND_Z), size=.20)
    _meta(root, 'env_ginkgo', leaf_count=count, height=height, crown_radius=radius,
          tree_count=1, foliage_style='large_rounded_ginkgo_fans',
          trunk_style='curved_tapered_paper_forks', crown_style='overlapping_staggered_fan_canopy',
          paper_thickness=.005, crown_cluster_count=len(cluster_counts),
          bark_fold_count=4)
    batch = _Batch()

    # A smooth S bend is lofted as one continuous tapered trunk, with the main
    # fork exposed below the umbrella instead of a straight vertical pole.
    control = [(0, 0, 0), (-.70*radius, -.055*radius, .30*height),
               (.50*radius, .035*radius, .48*height),
               (.20*radius, .035*radius, .80*height)]
    trunk = _bezier(control, 13)
    radii = [radius*(.17*(1-i/12)**1.18+.024) for i in range(13)]
    frames = _swept_branch(batch, trunk, radii, sides=10)
    _bark_folds(batch, frames)
    for angle in (.1, 1.8, 3.6, 5.1):
        end = (.31*math.cos(angle), .31*math.sin(angle), .024)
        points = _bezier([(0, 0, .15), (.08*math.cos(angle), .08*math.sin(angle), .07),
                          (.24*math.cos(angle), .24*math.sin(angle), .025), end], 5)
        _swept_branch(batch, points, [.072, .065, .048, .028, .014], sides=7)

    # Four genuinely separate branch-tip hubs, with different heights/depths.
    # The open space below/between the two lower hubs reveals the main fork.
    targets = [(-.58*radius, -.06*radius, .680*height),
               (.58*radius, .10*radius, .745*height),
               (-.25*radius, .27*radius, .887*height),
               (.23*radius, -.30*radius, .830*height)]
    for index, target in enumerate(targets):
        start = trunk[6 if index < 2 else 8]
        elbow = (target[0]*.40, target[1]*.36, start[2]+height*.10)
        shoulder = (target[0]*.82, target[1]*.80, target[2]-height*.04)
        points = _bezier([start, elbow, shoulder, target], 8)
        start_r = radius*(.076 if index < 2 else .057)
        _swept_branch(batch, points,
                      [start_r*(1-i/7)**1.2+.014 for i in range(8)], sides=8,
                      phase=.18*index)
        for fork in (-1, 1):
            end = (target[0]+fork*.12*radius, target[1]+.08*radius,
                   target[2]+.07*height)
            midpoint = _add(target, _mul(_sub(end, target), .55))
            points = _bezier([target, _add(target, (0, 0, .04)), midpoint, end], 5)
            _swept_branch(batch, points, [.026, .022, .017, .012, .006], sides=6)

    # Offset sheets overlap across branch-tip regions. Their bases do not
    # converge into radial flowers; rounded free edges stagger over the crown.
    leaf_scales = (.59, .61, .60, .60)
    for cluster_index, (hub, number) in enumerate(zip(targets, cluster_counts)):
        for index in range(number):
            turn = index*2.399963+cluster_index*.68
            spread = math.sqrt((index+.5)/number)
            offset_x = radius*.40*spread*math.cos(turn)
            offset_y = radius*.31*spread*math.sin(turn)
            offset_z = height*rng.uniform(-.045,.055)
            center = (hub[0]+offset_x,hub[1]+offset_y,hub[2]+offset_z)
            width = radius*leaf_scales[cluster_index]*rng.uniform(.84,1.06)
            normal = (rng.uniform(-.24,.24),rng.uniform(-.73,-.40),rng.uniform(.68,.95))
            roll = rng.uniform(-.72,.72)
            if offset_z < -.012*height and offset_y < .06*radius:
                roll += math.pi
            choice = rng.random()
            material = 'ginkgo_gold' if choice < .69 else 'ginkgo_light'
            if cluster_index < 2 and choice > .94:
                material = 'ginkgo_ochre'
            _fan_leaf(batch,center,width,normal,roll,material,
                      crown_bounds=(radius,height))
    objects = batch.emit(api, root, name)
    root['mesh_batch_count'] = len(objects)
    root['branch_lobes'] = len(targets)
    root['major_fork_count'] = len(targets)
    return root


def _fallen(api):
    root = api.empty('env_fallen_ginkgo_leaves', (0, 0, GROUND_Z), size=.15)
    _meta(root, 'env_fallen_leaves', leaf_count=18, cluster_count=3,
          foliage_style='large_rounded_ginkgo_fans', paper_thickness=.003)
    batch = _Batch()
    rng = random.Random(50318)
    for tree_index, (cx, cy, radius) in enumerate(((-2.35, 6.7, 1.25),
                                                  (14.35, 8.4, 1.35),
                                                  (1.5, 10.1, .95))):
        phase = (-1.8, -.6, 2.0)[tree_index]
        for index in range(6):
            angle = phase+(index//3)*1.9+rng.uniform(-.27, .27)
            distance = radius*rng.uniform(.48, .85)
            center = (cx+math.cos(angle)*distance,
                      cy+math.sin(angle)*distance, .014)
            _fan_leaf(batch, center, rng.uniform(.17, .235), (0, 0, 1),
                      rng.uniform(-math.pi, math.pi),
                      'ginkgo_gold' if index % 3 else 'ginkgo_ochre', thin=True)
    root['mesh_batch_count'] = len(batch.emit(api, root, 'env_fallen_ginkgo_leaves'))
    return root


def build_exterior_vegetation(api, spec):
    """Return the original three tree roots and one 18-leaf root; no grasses."""
    api.collection('Exterior/Vegetation/Ginkgo')
    trees = [('env_ginkgo_west', (-2.35, 6.7), 3.6, 1.25, (14, 14, 14, 13), 5301),
             ('env_ginkgo_east', (14.35, 8.4), 4.0, 1.35, (16, 16, 15, 15), 5302),
             ('env_ginkgo_north', (1.5, 10.1), 2.7, .95, (12, 12, 12, 12), 5303)]
    roots = [_ginkgo(api, *tree) for tree in trees]
    api.collection('Exterior/Vegetation/FallenLeaves')
    roots.append(_fallen(api))
    return roots
