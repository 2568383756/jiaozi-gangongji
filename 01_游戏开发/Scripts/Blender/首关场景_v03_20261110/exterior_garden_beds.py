"""Low rounded, folded-paper planting beds for the first level exterior.

Each planting group is batched into three material meshes.  The first three
beds retain an open soil/root circle beneath the existing ginkgo trees.
"""

from math import cos, sin, pi, sqrt
from random import Random


BEDS = (
    (-2.35, 6.7, 1.12, .90),
    (14.35, 8.4, 1.08, 1.05),
    (1.5, 10.1, 1.25, .72),
    (-2.1, 2.9, 1.05, .70),
    (14.5, 3.4, 1.05, .82),
    (10.0, 10.3, 1.30, .55),
    (10.0, -2.3, 1.35, .65),
    (1.1, -2.9, 1.35, .30),
)


def _face(batches, material, points):
    vertices, faces = batches[material]
    first = len(vertices)
    vertices.extend(points)
    faces.append(tuple(range(first, first + len(points))))


def _bound_xy(x, y, rx, ry, root_clearance=0):
    """Keep every vertex inside the specified oval and outside exposed roots."""
    distance = sqrt(x*x + y*y)
    if root_clearance and distance < root_clearance:
        if distance < 1e-8:
            x, y, distance = root_clearance, 0.0, root_clearance
        x *= root_clearance / distance
        y *= root_clearance / distance
    oval = sqrt((x/rx)**2 + (y/ry)**2)
    if oval > .97:
        x *= .97 / oval
        y *= .97 / oval
    return x, y


def _turf(batches, rx, ry, tree, rng):
    """An irregular thin paper silhouette, with a real hole for tree roots."""
    count = 24
    outer = []
    inner = []
    for i in range(count):
        angle = 2*pi*i/count
        radius = rng.uniform(.88, .985)
        outer.append((rx*radius*cos(angle), ry*radius*sin(angle)))
        if tree:
            inner.append((.275*cos(angle), .275*sin(angle)))
    top, bottom = -.125, -.140
    for i in range(count):
        j = (i + 1) % count
        a, b = outer[i], outer[j]
        material = ("moss", "moss", "grass", "moss", "sage", "moss")[i % 6]
        _face(batches, "moss", [(a[0], a[1], bottom),
                                 (b[0], b[1], bottom),
                                 (b[0], b[1], top),
                                 (a[0], a[1], top)])
        if tree:
            c, d = inner[j], inner[i]
            _face(batches, material, [(a[0], a[1], top),
                                      (b[0], b[1], top),
                                      (c[0], c[1], top),
                                      (d[0], d[1], top)])
            _face(batches, "moss", [(d[0], d[1], top),
                                     (c[0], c[1], top),
                                     (c[0], c[1], bottom),
                                     (d[0], d[1], bottom)])
        else:
            _face(batches, material, [(0, 0, top),
                                      (a[0], a[1], top),
                                      (b[0], b[1], top)])


def _rounded_leaf(batches, origin, angle, length, width, tilt,
                  material, rx, ry, tree, raised=False):
    """Broad obovate paper petal with rounded tip and a shallow central fold.

    A 0.008 m paper edge remains visible.  All upper outline vertices lie
    on one tilted plane; only the middle ridge is raised by 0.012 m.
    This keeps the silhouette a folded sheet rather than an inflated leaf.
    """
    ox, oy = origin
    forward = (cos(angle), sin(angle))
    side = (-sin(angle), cos(angle))
    clearance = .35 if tree else 0.0
    base_z = -.119 + (.016 if raised else 0.0)

    def point(u, v, ridge=0):
        along = u*cos(tilt)
        x = ox + forward[0]*along + side[0]*v
        y = oy + forward[1]*along + side[1]*v
        x, y = _bound_xy(x, y, rx, ry, clearance)
        return (x, y, base_z + u*sin(tilt) + ridge)

    outline = []
    segments = 16
    for i in range(segments):
        theta = 2*pi*i/segments
        u = length*(.5 + .5*cos(theta))
        # Broad round crown, gently narrowed heel; never a pointed spear.
        v = width*.5*sin(theta)*(.76 + .24*cos(theta))
        outline.append(point(u, v))
    ridge = point(length*.52, 0, .012)
    underside = [(x, y, z-.008) for x, y, z in outline]
    for i in range(segments):
        j = (i+1) % segments
        _face(batches, material, [ridge, outline[i], outline[j]])
        _face(batches, "moss", [outline[i], underside[i],
                                 underside[j], outline[j]])
    _face(batches, "moss", list(reversed(underside)))


def _cluster_centers(rx, ry, tree, rng):
    if tree:
        return [(rx*.57*cos(2*pi*i/5+.16),
                 ry*.57*sin(2*pi*i/5+.16)) for i in range(5)]
    if ry < .4:
        return [(rx*v, ry*(.10 if i % 2 else -.10))
                for i, v in enumerate((-.67, -.34, 0, .34, .67))]
    return [(0, 0)] + [(rx*.57*cos(2*pi*i/4+.3),
                        ry*.55*sin(2*pi*i/4+.3)) for i in range(4)]


def build_garden_beds(api, spec):
    """Return eight selectable planting roots; 25 rounded paper leaves each."""
    api.collection('Exterior/Vegetation/RoundedPaperBeds')
    roots = []
    for index, (cx, cy, rx, ry) in enumerate(BEDS):
        rng = Random(71031 + index*97)
        tree = index < 3
        name = "exterior_rounded_paper_bed_%02d" % (index+1)
        root = api.empty(name, (cx, cy, 0))
        root["asset_id"] = "env_planting_bed"
        root["role"] = "exterior_vegetation"
        root["non_interactive"] = True
        root["task"] = "F15"
        root["version"] = "v03_20261110"
        root["foliage_style"] = "rounded_folded_paper"
        root["bed_count"] = 1
        root["cluster_count"] = 5
        root["leaf_count"] = 25
        root["grass_strip_count"] = 0
        root["paper_thickness"] = .008
        root["bed_semiaxes"] = [rx, ry]
        root["root_clearance_radius"] = .35 if tree else 0.0
        batches = {mat: [[], []] for mat in ("moss", "grass", "sage")}
        _turf(batches, rx, ry, tree, rng)
        centers = _cluster_centers(rx, ry, tree, rng)
        for cluster_index, center in enumerate(centers):
            turn = rng.uniform(0, 2*pi)
            # Five overlapping rounded petals form the reference's clover-like
            # paper clusters.  Darker side leaves sit behind broad light ones.
            for petal in range(5):
                angle = turn + 2*pi*petal/5 + rng.uniform(-.12, .12)
                length = rng.uniform(.265, .360)
                width = rng.uniform(.235, .325)
                tilt = rng.uniform(.58, .96)
                material = ("moss", "grass", "grass", "sage", "sage")[(petal+cluster_index) % 5]
                if material == "sage":
                    width *= 1.07
                _rounded_leaf(batches, center, angle, length, width, tilt,
                              material, rx, ry, tree, raised=petal >= 3)
        for material, (vertices, faces) in batches.items():
            api.mesh(name + "_" + material, vertices, faces, material,
                     parent=root)
        roots.append(root)
    return roots
