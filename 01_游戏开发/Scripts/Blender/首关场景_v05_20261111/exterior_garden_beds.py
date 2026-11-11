"""Nine sparse wall-hugging clusters, 110 rounded folded-paper leaves.

Each cluster uses offset rows of individual sheets, never radial flowers.
No turf disks, grass needles, tree-root rings, or additional materials.
"""
from math import atan2, cos, sin, pi
from random import Random

# cx, cy, half-width/depth, leaf base Z, outward angle, count, placement.
BEDS = (
    (-.30, -.32, .275, .280, .006, -3*pi/4, 13, "wall_corner"),
    (12.30, -.32, .275, .280, .006, -pi/4, 13, "wall_corner"),
    (-.30, 8.32, .275, .280, .006, 3*pi/4, 13, "wall_corner"),
    (12.30, 8.32, .275, .280, .006, pi/4, 13, "wall_corner"),
    (-.25, 6.40, .230, .400, .006, pi, 11, "wall_base"),
    (12.25, 6.40, .230, .400, .006, 0, 11, "wall_base"),
    (-2.93, 6.30, .330, .250, -.130, atan2(-.40, -.58), 12, "tree_base"),
    (14.96, 7.98, .330, .250, -.130, atan2(-.42, .61), 12, "tree_base"),
    (1.98, 10.60, .330, .250, -.130, atan2(.50, .48), 12, "tree_base"),
)
PAPER_THICKNESS = .006


def _face(batches, material, points):
    vertices, faces = batches[material]
    first = len(vertices)
    vertices.extend(points)
    faces.append(tuple(range(first, first+len(points))))


def _rounded_leaf(batches, origin, angle, length, width, tilt, material):
    """Broad oval sheet, actual .006 m edge, shallow folded central spine."""
    ox, oy = origin
    forward, side = (cos(angle), sin(angle)), (-sin(angle), cos(angle))
    sections = 12

    def point(u, v, lift=0):
        along = u*cos(tilt)
        return (ox+forward[0]*along+side[0]*v,
                oy+forward[1]*along+side[1]*v, u*sin(tilt)+lift)

    rows = []
    for i in range(sections+1):
        theta = -pi/2+pi*i/sections
        t = .5+.5*sin(theta)
        half = max(.0006, width*.5*cos(theta)*(.88+.12*t))
        rows.append((point(length*t,-half),
                     point(length*t,0,.008*sin(pi*t)), point(length*t,half)))
    for i in range(sections):
        a, b = rows[i], rows[i+1]
        for first, second in ((0,1),(1,2)):
            top = [a[first],b[first],b[second],a[second]]
            _face(batches,material,top)
            _face(batches,material,[(x,y,z-PAPER_THICKNESS) for x,y,z in reversed(top)])
        for edge in (0,2):
            x0,y0,z0 = a[edge]
            x1,y1,z1 = b[edge]
            edge_face = [(x0,y0,z0),(x1,y1,z1),
                         (x1,y1,z1-PAPER_THICKNESS),(x0,y0,z0-PAPER_THICKNESS)]
            _face(batches,"moss",list(reversed(edge_face)) if edge == 0 else edge_face)
    for end,row in enumerate((rows[0],rows[-1])):
        left, _, right = row
        end_face = [left,right,
                    (right[0],right[1],right[2]-PAPER_THICKNESS),
                    (left[0],left[1],left[2]-PAPER_THICKNESS)]
        _face(batches,"moss",list(reversed(end_face)) if end else end_face)
    # Fine crease is batched; each leaf remains a thin sheet, not a cupped petal.
    crease_mat = "grass" if material == "moss" else "sage"
    for i in range(3,9):
        a,b = rows[i][1],rows[i+1][1]
        offset = .0009
        _face(batches,crease_mat,list(reversed(
              [(a[0]-side[0]*offset,a[1]-side[1]*offset,a[2]+.0008),
               (a[0]+side[0]*offset,a[1]+side[1]*offset,a[2]+.0008),
               (b[0]+side[0]*offset,b[1]+side[1]*offset,b[2]+.0008),
               (b[0]-side[0]*offset,b[1]-side[1]*offset,b[2]+.0008)])))


def _staggered_cluster(batches, angle, count, rng):
    """Three unequal offset rows; the leaves never share one radial hub."""
    forward, across = (cos(angle),sin(angle)),(-sin(angle),cos(angle))
    per_row = (4,5,4) if count == 13 else ((4,4,3) if count == 11 else (4,4,4))
    made = 0
    for row,n in enumerate(per_row):
        depth,offset,spread = ((-.055,-.025,.34),(.005,.022,.38),(.073,-.012,.33))[row]
        for i in range(n):
            # Reserve dark green for two rear accents, not an entire dark wall.
            material = ("moss" if i%3 == 0 else "grass") if row == 0 else ("grass" if row == 1 else "sage")
            u = offset+spread*(i/(n-1)-.5)+rng.uniform(-.017,.017)
            v = depth+rng.uniform(-.020,.020)
            origin = (across[0]*u+forward[0]*v,across[1]*u+forward[1]*v)
            length = rng.uniform(*((.240,.285),(.210,.265),(.180,.230))[row])
            width = rng.uniform(*((.235,.285),(.225,.280),(.200,.260))[row])
            tilt = rng.uniform(*((.85,1.10),(.55,.85),(.30,.60))[row])
            # Lean inward so the visible sheet normal faces OUT and UP.
            # Broad near-circular sheets gently splay instead of lining up as signs.
            yaw = angle+pi+(i/(n-1)-.5)*.62+rng.uniform(-.38,.38)
            _rounded_leaf(batches,origin,yaw,length,width,tilt,material)
            made += 1
    return made


def _fit_footprint(batches, half_width, half_depth):
    """Scale the arrangement; never clamp and deform individual round tips."""
    points = [p for vertices,_ in batches.values() for p in vertices]
    sx = min(1,half_width/max(abs(p[0]) for p in points))
    sy = min(1,half_depth/max(abs(p[1]) for p in points))
    for material,(vertices,faces) in batches.items():
        batches[material][0] = [(x*sx,y*sy,z) for x,y,z in vertices]


def build_garden_beds(api, spec):
    """Return nine non-interactive foliage roots with 110 paper leaves total."""
    api.collection("Exterior/Vegetation/RoundedPaperBeds")
    roots = []
    for index,(cx,cy,rx,ry,base,angle,count,placement) in enumerate(BEDS):
        name = "exterior_rounded_paper_bed_%02d" % (index+1)
        root = api.empty(name,(cx,cy,base))
        root["asset_id"] = "env_planting_bed"
        root["role"] = "exterior_vegetation"
        root["non_interactive"] = True
        root["task"] = "F15"
        root["version"] = "v05_20261111"
        root["foliage_style"] = "rounded_folded_paper"
        root["placement"] = placement
        root["cluster_count"] = 1
        root["bed_count"] = 1
        root["grass_strip_count"] = 0
        root["blade_count"] = 0
        root["paper_thickness"] = PAPER_THICKNESS
        root["leaf_base_z"] = base
        root["footprint_half_extents"] = [rx,ry]
        root["palette"] = "two moss rear accents / grass back-middle / sage front"
        root["leaf_face_orientation"] = "outward_and_upward_broad_visible_faces"
        root["arrangement"] = "staggered_individual_sheets_no_rosettes_no_root_ring"
        batches = {mat:[[],[]] for mat in ("moss","grass","sage")}
        root["leaf_count"] = _staggered_cluster(batches,angle,count,Random(91031+index*97))
        _fit_footprint(batches,rx,ry)
        points = [p for vertices,_ in batches.values() for p in vertices]
        minimum = [min(p[axis] for p in points) for axis in range(3)]
        maximum = [max(p[axis] for p in points) for axis in range(3)]
        root["world_bounds_min"] = [minimum[0]+cx,minimum[1]+cy,minimum[2]+base]
        root["world_bounds_max"] = [maximum[0]+cx,maximum[1]+cy,maximum[2]+base]
        for material,(vertices,faces) in batches.items():
            api.mesh(name+"_"+material,vertices,faces,material,parent=root)
        roots.append(root)
    return roots
