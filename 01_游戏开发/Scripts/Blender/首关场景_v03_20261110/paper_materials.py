"""Packed, UV-based papercraft materials for Blender and the GLB export.

Call enhance_materials(api) immediately after SceneAPI().  No geometry, files,
render settings or scene selection are changed.  Only api.materials listed in
PROFILES are enhanced; ink, water and metal keep their existing materials.

UV contract: the assembly script must UV-project every final visible mesh,
including converted curves and custom meshes, at one shared physical scale.
Use its active render UV map, REPEAT wrapping, no per-island fit-to-bounds.
Calibrate a 1 m test face to one UV tile; deterministic island offsets are fine.
Keep an existing illustration's UVs if that face uses an image-specific material.

Base colour is a direct Image Texture -> Principled connection.  A packed
Non-Color normal image feeds a tangent-space Normal Map -> Principled Normal.
There are no Generated coordinates, Mix chains, Noise nodes or Bump nodes that
would disappear on glTF export.  The periodic mathematical paper pattern is
evaluated once with Blender's bundled NumPy and stored inside packed images.
"""

import bpy
import numpy as np


SIZE = 1024
SEED = 20261110
PREFIX = "TEX_JiaoziPaper_v02_"
OWNER = "jiaozi_paper_v02"

# cloud, fibre contrast, weathering, normal strength, roughness.
# Paper fibres read on broad surfaces; painted furniture remains quieter.
PROFILES = {
    "paper":      (.090, .040, .045, 1.00, .92),
    "paper_edge": (.100, .042, .065, 1.10, .95),
    "wood":       (.055, .019, .036,  .50, .88),
    "wood_light": (.060, .021, .032,  .55, .90),
    "wood_dark":  (.040, .014, .024,  .38, .88),
    "roof":       (.065, .025, .032,  .75, .92),
    "stone":      (.060, .024, .042,  .70, .94),
    "wet":        (.045, .020, .026,  .35, .68),
    "red":        (.045, .018, .028,  .45, .88),
    "teal":       (.040, .016, .025,  .40, .88),
    "floor_workshop": (.055, .025, .040, .70, .94),
    "floor_courtyard":(.075, .032, .050, .80, .95),
    "garden_soil": (.080,.030,.055,.80,.95),
    "garden_edge": (.080,.030,.060,.90,.95),
    "paving": (.060,.030,.055,.80,.94),
    "paving_light": (.060,.030,.045,.70,.94),
    "moss": (.055,.020,.035,.50,.95),
    "grass": (.045,.018,.030,.45,.92),
    "sage": (.045,.018,.030,.45,.92),
    "ginkgo_gold": (.040,.020,.020,.45,.88),
    "ginkgo_light": (.040,.020,.020,.40,.88),
    "ginkgo_ochre": (.045,.020,.025,.45,.90),
    "bark": (.070,.030,.050,.70,.92),
}


def _periodic_noise(rng, nx, ny):
    """Smooth tileable value noise. No uncorrelated pixel grain."""
    grid = rng.uniform(-1.0, 1.0, (ny, nx)).astype(np.float32)
    x = np.arange(SIZE, dtype=np.float32) * (nx / SIZE)
    y = np.arange(SIZE, dtype=np.float32) * (ny / SIZE)
    ix, iy = x.astype(np.int32), y.astype(np.int32)
    fx, fy = x - ix, y - iy
    fx = fx * fx * (3.0 - 2.0 * fx)
    fy = fy * fy * (3.0 - 2.0 * fy)
    a = grid[iy[:, None] % ny, ix[None, :] % nx]
    b = grid[iy[:, None] % ny, (ix[None, :] + 1) % nx]
    c = grid[(iy[:, None] + 1) % ny, ix[None, :] % nx]
    d = grid[(iy[:, None] + 1) % ny, (ix[None, :] + 1) % nx]
    low = a * (1.0 - fx[None, :]) + b * fx[None, :]
    high = c * (1.0 - fx[None, :]) + d * fx[None, :]
    return (low * (1.0 - fy[:, None]) + high * fy[:, None]).astype(np.float32)


def _pattern():
    rng = np.random.default_rng(SEED)
    coarse = _periodic_noise(rng, 4, 4)
    middle = _periodic_noise(rng, 11, 9)
    pulp = _periodic_noise(rng, 44, 47)
    # Intersecting, interrupted fibre bundles rather than continuous wood grain.
    fibres = (.58 * _periodic_noise(rng, 224, 31)
              + .42 * _periodic_noise(rng, 37, 197))
    fibres *= .65 + .35 * (middle + 1.0) * .5
    u = np.arange(SIZE, dtype=np.float32)[None, :] / SIZE
    v = np.arange(SIZE, dtype=np.float32)[:, None] / SIZE
    folds = np.zeros((SIZE, SIZE), dtype=np.float32)
    # Sparse, broad shallow creases; all frequencies are integers, so they tile.
    for ax, ay, phase in ((1, 2, .19), (2, -1, .61), (1, -3, .83)):
        position = (ax * u + ay * v + phase
                    + .045 * np.sin(2.0 * np.pi * (u + v)))
        distance = np.abs((position + .5) % 1.0 - .5)
        folds += (np.exp(-np.square(distance / .010))
                  - .40 * np.exp(-np.square(distance / .032))).astype(np.float32)
    # Small broad tonal islands suggest ageing, without dirt dots or UV borders.
    age = np.clip((.70 * coarse + .30 * middle - .13) / .65, 0.0, 1.0)
    cloud = .66 * coarse + .34 * middle
    height_m = (.00070 * fibres + .00024 * pulp
                + .00048 * folds + .00015 * middle).astype(np.float32)
    return cloud, fibres, pulp, folds, age, height_m


def _normal_rgb(height_m):
    """OpenGL/glTF +Y tangent normal, assuming one UV tile spans one metre."""
    du = (np.roll(height_m, -1, axis=1) - np.roll(height_m, 1, axis=1)) * (SIZE * .5)
    dv = (np.roll(height_m, -1, axis=0) - np.roll(height_m, 1, axis=0)) * (SIZE * .5)
    normal = np.stack((-du, -dv, np.ones_like(height_m)), axis=-1)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-8)
    return (normal * .5 + .5).astype(np.float32)


def _linear_to_srgb(rgb):
    rgb = np.maximum(np.asarray(rgb, dtype=np.float32), 0.0)
    return np.where(rgb <= .0031308, rgb * 12.92,
                    1.055 * np.power(rgb, 1.0 / 2.4) - .055)


def _packed_image(name, rgb, non_color=False):
    image = bpy.data.images.get(name)
    if image is not None and image.get("generator") != OWNER:
        raise RuntimeError("Refusing to replace an unrelated image: " + name)
    if image is None:
        image = bpy.data.images.new(name, width=SIZE, height=SIZE,
                                    alpha=True, float_buffer=False,
                                    is_data=non_color)
    elif tuple(image.size) != (SIZE, SIZE):
        image.scale(SIZE, SIZE)
    image["generator"] = OWNER
    image["tile_size_m"] = 1.0
    image.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    pixels = np.ones((SIZE, SIZE, 4), dtype=np.float32)
    pixels[:, :, :3] = np.clip(rgb, 0.0, 1.0)
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    image.file_format = "PNG"
    image.pack()
    return image


def enhance_materials(api):
    """Enhance ten palette materials and return a serializable handoff report."""
    cloud, fibres, pulp, folds, age, height = _pattern()
    normal_image = _packed_image(PREFIX + "Normal", _normal_rgb(height), True)
    report = {"size": SIZE, "seed": SEED, "uv_tile_m": 1.0,
              "uv_source": "active render UV; repeat; shared physical scale",
              "packed_images": [normal_image.name], "materials": [],
              "unchanged": ["ink", "water", "metal"],
              "normal_convention": "tangent OpenGL/glTF +Y"}
    for key, profile in PROFILES.items():
        material = api.materials.get(key)
        if material is None:
            continue
        material.use_nodes = True
        tree = material.node_tree
        previous = next((n for n in tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        # Preserve the original palette on repeated calls, rather than using an
        # image-linked input's unrelated default value as the new palette.
        stored = material.get("paper_original_linear")
        base = list(stored) if stored is not None else list(
            previous.inputs["Base Color"].default_value if previous else material.diffuse_color)
        material["paper_original_linear"] = base
        cloud_amount, fibre_amount, wear, normal_strength, roughness = profile
        shade = (1.0 + cloud_amount * cloud + fibre_amount * fibres
                 + fibre_amount * .30 * pulp - .011 * folds - wear * age)
        rgb = _linear_to_srgb(base[:3])[None, None, :] * shade[:, :, None]
        # Weathering shifts just the broad worn regions toward warm paper.
        rgb *= 1.0 + age[:, :, None] * np.array([.006, -.002, -.018], dtype=np.float32)
        colour_image = _packed_image(PREFIX + key + "_BaseColor", rgb)
        tree.nodes.clear()
        output = tree.nodes.new("ShaderNodeOutputMaterial")
        output.location = (620, 60)
        bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (300, 60)
        bsdf.inputs["Base Color"].default_value = base
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = 0.0
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = .18
        color_node = tree.nodes.new("ShaderNodeTexImage")
        color_node.name = "Packed paper base colour"
        color_node.image = colour_image
        color_node.extension = "REPEAT"
        color_node.interpolation = "Linear"
        color_node.location = (-390, 220)
        normal_node = tree.nodes.new("ShaderNodeTexImage")
        normal_node.name = "Packed paper tangent normal"
        normal_node.image = normal_image
        normal_node.extension = "REPEAT"
        normal_node.interpolation = "Linear"
        normal_node.location = (-390, -110)
        normal_map = tree.nodes.new("ShaderNodeNormalMap")
        normal_map.space = "TANGENT"
        normal_map.inputs["Strength"].default_value = normal_strength
        normal_map.location = (25, -90)
        tree.links.new(color_node.outputs["Color"], bsdf.inputs["Base Color"])
        tree.links.new(normal_node.outputs["Color"], normal_map.inputs["Color"])
        tree.links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
        tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
        material["paper_texture_version"] = "v03_20261110"
        material["paper_uv_tile_m"] = 1.0
        report["packed_images"].append(colour_image.name)
        report["materials"].append({"key": key, "name": material.name,
                                    "roughness": roughness,
                                    "normal_strength": normal_strength})
    api.paper_material_report = report
    return report
