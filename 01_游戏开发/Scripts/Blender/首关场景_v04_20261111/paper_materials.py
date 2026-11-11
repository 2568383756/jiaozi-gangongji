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
SEED = 20261111
PREFIX = "TEX_JiaoziPaper_v04_"
OWNER = "jiaozi_paper_v04"
FIBRE_COUNT = 1080

# cloud, fibre contrast, weathering, normal strength, roughness.
# Sparse xuan-paper strands, not a woven fabric.  Keep distant colour blocks
# clean; furniture and painted leaves are smoother than uncoated paper edges.
PROFILES = {
    "paper":      (.048, .110, .006, .92, .91),
    "paper_edge": (.052, .125, .008, 1.00, .94),
    "wood":       (.028, .038, .005, .38, .84),
    "wood_light": (.032, .049, .004, .46, .87),
    "wood_dark":  (.022, .026, .004, .29, .83),
    "roof":       (.032, .039, .005, .47, .87),
    "stone":      (.034, .047, .007, .45, .91),
    "wet":        (.025, .032, .003, .28, .73),
    "red":        (.022, .029, .003, .28, .84),
    "teal":       (.021, .028, .003, .27, .84),
    "floor_workshop": (.039, .068, .006, .66, .92),
    "floor_courtyard":(.046, .085, .007, .78, .94),
    "garden_soil": (.039, .048, .009, .49, .93),
    "garden_edge": (.042, .057, .009, .57, .94),
    "paving": (.035, .050, .007, .50, .92),
    "paving_light": (.034, .050, .006, .48, .92),
    "moss": (.023, .014, .005, .27, .88),
    "grass": (.019, .013, .003, .24, .82),
    "sage": (.019, .013, .003, .24, .82),
    "ginkgo_gold": (.018, .014, .003, .24, .80),
    "ginkgo_light": (.017, .014, .003, .22, .80),
    "ginkgo_ochre": (.020, .014, .004, .25, .82),
    "bark": (.030, .019, .007, .36, .86),
}


def _soft_pulp(rng, frequency):
    """Isotropic, smoothly filtered paper pulp; no grid interpolation axes."""
    fy = np.fft.fftfreq(SIZE)[:, None] * SIZE
    fx = np.fft.rfftfreq(SIZE)[None, :] * SIZE
    spectrum = np.fft.rfft2(rng.standard_normal((SIZE, SIZE)).astype(np.float32))
    spectrum *= np.exp(-.5 * (fx * fx + fy * fy) / (frequency * frequency))
    field = np.fft.irfft2(spectrum, s=(SIZE, SIZE)).astype(np.float32)
    field -= field.mean()
    field /= max(float(field.std()) * 2.6, 1e-8)
    return np.clip(field, -1.0, 1.0)


def _stamp_strand(field, cx, cy, length, width, angle, bend, amplitude):
    """Deposit one tapered curved strand, wrapping its small patch at tile edges.

    Length/width are pixels. Random orientation and local support remove the
    old continuous horizontal/vertical crosshatch and repeating diagonal lines.
    """
    reach = int(np.ceil(length * .58 + width * 4.0 + abs(bend) + 2))
    xs = np.arange(int(np.floor(cx)) - reach, int(np.floor(cx)) + reach + 1)
    ys = np.arange(int(np.floor(cy)) - reach, int(np.floor(cy)) + reach + 1)
    dx = (xs.astype(np.float32)[None, :] + .5) - cx
    dy = (ys.astype(np.float32)[:, None] + .5) - cy
    cs, sn = np.cos(angle), np.sin(angle)
    along = cs * dx + sn * dy
    across = -sn * dx + cs * dy
    t = along / max(length * .5, 1.0)
    curve = bend * np.maximum(0.0, 1.0 - t * t)
    taper = np.square(np.maximum(0.0, 1.0 - t * t))
    profile = np.exp(-np.square((across - curve) / width)) * taper
    field[np.ix_(ys % SIZE, xs % SIZE)] += (amplitude * profile).astype(np.float32)


def _short_fibres(rng):
    fibres = np.zeros((SIZE, SIZE), dtype=np.float32)
    for _ in range(FIBRE_COUNT):
        # A deliberately legible papercraft scale: the first render's subpixel
        # strands vanished under denoising. Slightly broader sparse strands
        # survive the station close-up without becoming a woven blanket.
        length = rng.uniform(14, 42)
        if rng.random() < .12:
            length = rng.uniform(42, 68)
        amplitude = rng.uniform(.36, .82) * (1.0 if rng.random() < .64 else -.65)
        _stamp_strand(fibres, rng.uniform(0, SIZE), rng.uniform(0, SIZE),
                      length, rng.uniform(1.25, 2.35), rng.uniform(0, 2 * np.pi),
                      rng.uniform(-3.6, 3.6), amplitude)
    fibres -= fibres.mean()
    return np.clip(fibres, -1.0, 1.0)


def _shallow_impressions(rng):
    impressions = np.zeros((SIZE, SIZE), dtype=np.float32)
    # Soft pressure dents and a few short, gently bent creases. No full-width
    # sine-wave folds or painted dark crease network.
    for _ in range(14):
        _stamp_strand(impressions, rng.uniform(0, SIZE), rng.uniform(0, SIZE),
                      rng.uniform(40, 130), rng.uniform(7, 17),
                      rng.uniform(0, 2 * np.pi), rng.uniform(-8, 8),
                      rng.uniform(-.50, .25))
    for _ in range(7):
        _stamp_strand(impressions, rng.uniform(0, SIZE), rng.uniform(0, SIZE),
                      rng.uniform(80, 170), rng.uniform(2.8, 5.0),
                      rng.uniform(0, 2 * np.pi), rng.uniform(-10, 10),
                      rng.uniform(-.28, .28))
    return np.clip(impressions, -.65, .50)


def _pattern():
    rng = np.random.default_rng(SEED)
    coarse = _soft_pulp(rng, 2.8)
    middle = _soft_pulp(rng, 8.0)
    # Two isotropic pulp scales provide the soft sheet body around the longer
    # fibres. Their low contrast avoids dirt spots and sand/plaster speckles.
    pulp = .72 * _soft_pulp(rng, 36.0) + .28 * _soft_pulp(rng, 88.0)
    fibres = _short_fibres(rng)
    folds = _shallow_impressions(rng)
    cloud = .72 * coarse + .28 * middle
    age = np.clip((coarse - .45) / .55, 0.0, 1.0)
    # Submillimetre relief: visibly pressed paper at the actual close-up scale,
    # not deep cloth ridges. Profile strengths keep painted timber quieter.
    height_m = (.000420 * fibres + .000210 * pulp
                + .000650 * folds + .000120 * middle).astype(np.float32)
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
    """Enhance available palette materials and return a handoff report."""
    cloud, fibres, pulp, folds, age, height = _pattern()
    normal_image = _packed_image(PREFIX + "Normal", _normal_rgb(height), True)
    report = {"size": SIZE, "seed": SEED, "uv_tile_m": 1.0,
              "uv_source": "active render UV; repeat; shared physical scale",
              "texture_style": "readable_sparse_xuan_fibres_and_soft_pressed_pulp",
              "short_fibres_per_tile": FIBRE_COUNT,
              "height_range_mm": [float(height.min() * 1000), float(height.max() * 1000)],
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
                 + fibre_amount * .40 * pulp
                 + fibre_amount * .22 * folds - wear * age)
        rgb = _linear_to_srgb(base[:3])[None, None, :] * shade[:, :, None]
        # A tiny warm shift on broad aged regions; the palette remains owned by
        # SceneAPI/the assembly script, with no brown dirt speckles added here.
        rgb *= 1.0 + age[:, :, None] * np.array([.002, 0.0, -.005], dtype=np.float32)
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
        material["paper_texture_version"] = "v04_20261111"
        material["paper_uv_tile_m"] = 1.0
        report["packed_images"].append(colour_image.name)
        report["materials"].append({"key": key, "name": material.name,
                                    "roughness": roughness,
                                    "normal_strength": normal_strength})
    api.paper_material_report = report
    return report
