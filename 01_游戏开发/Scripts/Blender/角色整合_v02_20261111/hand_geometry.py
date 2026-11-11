"""Closed, connected paper-craft hands; pure Python, no Blender dependency.

``make_hand_geometry(side, dimensions)`` returns vertices, polygon faces and
one material tag per face. Dimensions are metres: w=.080, l=.095, t=.050.
The wrist joint is (0, 0, 0), fingers extend +Y, hand back is +Z, palm is
-Z. A capped .012 m wrist insert extends -Y into the sleeve. The left thumb
extends +X and the right -X, per the rig's corrected semantic-axis convention:
Work fingers world -Y and back world +Z send local +X toward world -X.

The four fingers share one gently scalloped end instead of separate spheres.
The thumb replaces a side patch of the palm with a continuous branch: there
are no intersecting component shells, holes, finger balls or black creases.
Do not apply subdivision merely to close the mesh; it is already closed.
"""
import math


def make_hand_geometry(side, dimensions=None):
    """Return ``(vertices, faces, material_tags)`` for one watertight hand.

    Accepted dimensions: ``w`` palm width, ``l`` joint-to-fingertip length,
    ``t`` maximum palm thickness, ``wrist_insert`` (default .012), and
    ``wrist_extension`` (default 0). The latter moves the complete palm and
    thumb forward without stretching them, lengthening only the narrow wrist.
    Default whole-hand width including the thumb is about .1082 m. The palm
    underside has broad shallow facets suitable for real-mesh contact probes;
    this function does not attach bones or assert any world-space pose.
    """
    side = str(side).upper()
    if side not in ('L', 'R'):
        raise ValueError("side must be 'L' or 'R'")
    dimensions = dimensions or {}
    w = float(dimensions.get('w', .080))
    length = float(dimensions.get('l', .095))
    thickness = float(dimensions.get('t', .050))
    insert = float(dimensions.get('wrist_insert', .012))
    extension = float(dimensions.get('wrist_extension', 0.0))
    if min(w, length, thickness) <= 0 or min(insert, extension) < 0:
        raise ValueError('Hand dimensions must be positive; wrist lengths >= 0')

    vertices, faces, tags = [], [], []
    count = 32

    def vertex(xyz):
        vertices.append(tuple(float(v) for v in xyz))
        return len(vertices) - 1

    def face(indices, tag=None):
        # The distal centreline intentionally merges its upper/lower vertices.
        clean = []
        for index in indices:
            if not clean or index != clean[-1]:
                clean.append(index)
        if len(clean) > 1 and clean[0] == clean[-1]:
            clean.pop()
        if len(set(clean)) < 3:
            return
        faces.append(tuple(clean))
        if tag is None:
            average_z = sum(vertices[i][2] for i in clean) / len(clean)
            tag = 'skin_top' if average_z > thickness * .12 else 'skin_side'
        tags.append(tag)

    # The narrow, closed cuff insert blends into a fuller palm. Elliptical
    # cross sections give broad facets without a plastic ball silhouette.
    sections = [
        (-insert, .250*w, .330*thickness),
        (0.000*length, .275*w, .365*thickness),
        (0.158*length, .400*w, .465*thickness),
        (0.337*length, .485*w, .500*thickness),
        (0.558*length, .500*w, .500*thickness),
        (0.768*length, .485*w, .450*thickness),
    ]
    rings = []
    for row, (y, radius_x, radius_z) in enumerate(sections):
        ring = []
        for k in range(count):
            x = radius_x*math.cos(2*math.pi*k/count)
            z = radius_z*math.sin(2*math.pi*k/count)
            if row in (3, 4) and 22 <= k <= 26:
                # A small 35 x 21 mm true support patch, not a lowest edge.
                # Five transverse points retain the surrounding soft facets.
                x = (k-24)*.109375*w
                z = -.500*thickness
            ring.append(vertex((x, y, z)))
        rings.append(ring)

    # Four soft finger lobes, with the little-finger side slightly shorter.
    # Their notches are only a few millimetres deep, not open finger gaps.
    distal_x = [.475*w*math.cos(2*math.pi*k/count) for k in range(count)]
    def tip_profile(x):
        s = x/(.5*w)
        return .945-.024*math.cos(4*math.pi*s)-.040*max(s, 0)**1.5-.008*s
    profiles = [tip_profile(x) for x in distal_x]
    normalizer = max(profiles)
    nose_y = [length*p/normalizer for p in profiles]
    rings.append([vertex((distal_x[k], nose_y[k]-.043*length,
                          .245*thickness*math.sin(2*math.pi*k/count)))
                  for k in range(count)])
    # Collapse only Z, not X, at the gently scalloped tip centreline. This
    # creates a real closed rounded end, rather than a concave triangle fan.
    merged = {}
    tip_ring = []
    for k in range(count):
        key = (round(distal_x[k], 12), round(nose_y[k], 12))
        if key not in merged:
            merged[key] = vertex((distal_x[k], nose_y[k], 0.0))
        tip_ring.append(merged[key])
    rings.append(tip_ring)

    # Remove the left palm-side patch which the connected thumb replaces.
    # Its two longitudinal rows and eight angular spans form a 20-edge rim.
    removed = []
    for row in range(len(rings)-1):
        for k in range(count):
            nxt = (k+1) % count
            quad = (rings[row][k], rings[row+1][k],
                    rings[row+1][nxt], rings[row][nxt])
            if 2 <= row < 4 and 12 <= k < 20:
                removed.append(quad)
            else:
                face(quad)

    # The capped sleeve insert is not an exposed hole. Winding is -Y.
    wrist_center = vertex((0, -insert, 0))
    for k in range(count):
        face((wrist_center, rings[0][k], rings[0][(k+1) % count]),
             'skin_side')

    # Recover the directed rim of the removed patch. The new branch uses the
    # same rim direction, so every shared edge has opposite directed owners.
    directed = []
    edge_usage = {}
    for polygon in removed:
        for a, b in zip(polygon, polygon[1:]+polygon[:1]):
            key = tuple(sorted((a, b)))
            edge_usage[key] = edge_usage.get(key, 0)+1
            directed.append((a, b))
    boundary = [(a, b) for a, b in directed
                if edge_usage[tuple(sorted((a, b)))] == 1]
    successor = dict(boundary)
    rim = [boundary[0][0]]
    while successor[rim[-1]] != rim[0]:
        rim.append(successor[rim[-1]])
    if len(rim) != len(boundary):
        raise RuntimeError('Thumb patch boundary is not one simple loop')

    center = [sum(vertices[i][axis] for i in rim)/len(rim)
              for axis in range(3)]
    # Thumb travels inward and slightly forward; its cross section is normal
    # to that direction. Angles come from the real rim, not an arbitrary
    # reordered circle, avoiding twisted junction faces.
    ux, uy = .530, .848
    unit = math.hypot(ux, uy)
    ux, uy = ux/unit, uy/unit
    angles = []
    for index in rim:
        x, y, z = vertices[index]
        along = (x-center[0])*ux+(y-center[1])*uy
        angles.append(math.atan2(z-center[2], along))
    previous = rim
    for cx, cy, radius_u, radius_z in (
        (-.575*w, .410*length, .170*w, .340*thickness),
        (-.735*w, .505*length, .130*w, .270*thickness),
        (-.815*w, .555*length, .070*w, .160*thickness),
    ):
        following = [vertex((cx+ux*radius_u*math.cos(angle),
                             cy+uy*radius_u*math.cos(angle),
                             radius_z*math.sin(angle))) for angle in angles]
        for k in range(len(rim)):
            nxt = (k+1) % len(rim)
            face((previous[k], previous[nxt], following[nxt], following[k]))
        previous = following
    thumb_tip = vertex((-.850*w, .575*length, 0))
    for k in range(len(rim)):
        face((previous[k], previous[(k+1) % len(rim)], thumb_tip))

    # Split the two polygons sharing the palm's centre longitudinal edge.
    # The resulting real vertex survives explicit triangulation and can be
    # used as a Work / Carry palm contact probe instead of an arbitrary tip.
    edge_a, edge_b = rings[3][24], rings[4][24]
    probe = vertex((0, .4475*length, -.500*thickness))
    original_faces, original_tags = list(faces), list(tags)
    faces, tags = [], []
    for polygon, tag in zip(original_faces, original_tags):
        split_edge = None
        for k, (a, b) in enumerate(zip(polygon, polygon[1:]+polygon[:1])):
            if {a, b} == {edge_a, edge_b}:
                split_edge = k
                break
        if split_edge is None:
            face(polygon, tag)
        else:
            ordered = polygon[split_edge:]+polygon[:split_edge]
            a, b, c, d = ordered
            face((a, probe, d), tag)
            face((probe, b, c), tag)
            face((probe, c, d), tag)

    # Lengthen the wrist bridge only. The insert cap stays inside the sleeve;
    # all original nonnegative-Y palm/thumb points translate as one shape.
    if extension:
        vertices = [(x, y+extension if y >= 0 else y, z) for x, y, z in vertices]

    # Remove vertices belonging only to the deleted interior patch. Keeping
    # an unused inner point would break component-based hand validation.
    used = sorted({i for polygon in faces for i in polygon})
    remap = {old: new for new, old in enumerate(used)}
    vertices = [vertices[i] for i in used]
    faces = [tuple(remap[i] for i in polygon) for polygon in faces]
    if side == 'L':
        vertices = [(-x, y, z) for x, y, z in vertices]
        faces = [tuple(reversed(polygon)) for polygon in faces]
    return vertices, faces, tags


def inspect_hand_geometry(side='L', dimensions=None):
    """Pure-Python closedness, winding, volume and bounds audit for callers."""
    vertices, faces, tags = make_hand_geometry(side, dimensions)
    edge_owners = {}
    adjacency = {i: set() for i in range(len(vertices))}
    volume = 0.0
    min_area = float('inf')
    for polygon in faces:
        for a, b in zip(polygon, polygon[1:]+polygon[:1]):
            edge_owners.setdefault(tuple(sorted((a, b))), []).append((a, b))
            adjacency[a].add(b)
            adjacency[b].add(a)
        a = vertices[polygon[0]]
        for k in range(1, len(polygon)-1):
            b, c = vertices[polygon[k]], vertices[polygon[k+1]]
            cross = (b[1]*c[2]-b[2]*c[1],
                     b[2]*c[0]-b[0]*c[2], b[0]*c[1]-b[1]*c[0])
            volume += sum(a[i]*cross[i] for i in range(3))/6
            ab, ac = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
            area_cross = (ab[1]*ac[2]-ab[2]*ac[1],
                          ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
            min_area = min(min_area, .5*math.sqrt(sum(v*v for v in area_cross)))
    reached, pending = set(), [0]
    while pending:
        index = pending.pop()
        if index in reached:
            continue
        reached.add(index)
        pending.extend(adjacency[index]-reached)
    bounds = {'min': [min(v[i] for v in vertices) for i in range(3)],
              'max': [max(v[i] for v in vertices) for i in range(3)]}
    bounds['size'] = [bounds['max'][i]-bounds['min'][i] for i in range(3)]
    dim = dimensions or {}
    expected_probe = (0, .4475*float(dim.get('l', .095))+float(dim.get('wrist_extension', 0)),
                      -.5*float(dim.get('t', .050)))
    probe_id = min(range(len(vertices)), key=lambda i: sum((vertices[i][k]-expected_probe[k])**2 for k in range(3)))
    return {'side': side, 'vertices': len(vertices), 'faces': len(faces),
            'triangles': sum(len(f)-2 for f in faces), 'bounds': bounds,
            'palm_probe_vertex': probe_id, 'palm_probe_local': vertices[probe_id],
            'one_component': len(reached) == len(vertices),
            'every_edge_has_two_faces': all(len(v) == 2 for v in edge_owners.values()),
            'consistent_edge_winding': all(len(v) == 2 and v[0] == tuple(reversed(v[1]))
                                            for v in edge_owners.values()),
            'euler_characteristic': len(vertices)-len(edge_owners)+len(faces),
            'signed_volume_m3': volume, 'minimum_triangle_area_m2': min_area,
            'material_tags': sorted(set(tags))}


if __name__ == '__main__':
    import json
    print(json.dumps([inspect_hand_geometry(side) for side in ('L', 'R')], indent=2))
