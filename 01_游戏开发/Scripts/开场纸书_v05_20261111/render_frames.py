"""Render/resume v05 at 1080p/24 fps with an exact source fingerprint.

blender -b <v05.blend> --python render_frames.py
blender -b <v05.blend> --python render_frames.py -- 1 192

On source/settings changes, old frames are re-rendered in place. No other
directory is removed or modified. Work images are not deliverables.
"""
from pathlib import Path
import hashlib
import json
import ast
import shutil
import struct
import sys
import time
import bpy

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "Art" / "开场纸书_v05_20261111"
SOURCE = (OUT / "开场纸书_v05_20261111.blend").resolve()
if not bpy.data.filepath or Path(bpy.data.filepath).resolve() != SOURCE:
    raise RuntimeError(f"Open the exact v05 source first: {SOURCE}")
if not bpy.context.scene.camera:
    raise RuntimeError("v05 source has no active camera")

destination = HERE / "work" / "frames_final"
destination.mkdir(parents=True, exist_ok=True)
manifest_path = destination / "render_manifest.json"
source_tags = destination / "source_tags"
source_tags.mkdir(exist_ok=True)
scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.render.fps_base = 1
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 95
scene.render.image_settings.color_mode = "RGB"
scene.render.use_file_extension = True
scene.render.use_border = False
scene.frame_start, scene.frame_end = 1, 1152

start, end = 1, 1152
audit_only = False
if "--" in sys.argv:
    arguments = sys.argv[sys.argv.index("--") + 1:]
    if "--audit-cache" in arguments:
        audit_only = True
        arguments.remove("--audit-cache")
    if len(arguments) > 2:
        raise ValueError("Expected optional start and end frame only")
    if arguments:
        start = int(arguments[0])
    if len(arguments) > 1:
        end = int(arguments[1])
if not 1 <= start <= end <= 1152:
    raise ValueError("Frame range must be inside 1..1152")

with SOURCE.open("rb") as source_stream:
    source_hash = hashlib.file_digest(source_stream, "sha256").hexdigest()
fingerprint = {
    "version": "v05_20261111",
    "source_file": SOURCE.name,
    "source_sha256": source_hash,
    "blender": bpy.app.version_string,
    "engine": scene.render.engine,
    "camera": scene.camera.name,
    "width": 1920,
    "height": 1080,
    "fps": 24,
    "jpeg_quality": 95,
    "frame_start": 1,
    "frame_end": 1152,
}
fingerprint_hash = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()


def action_paths(action, slot=None):
    """Blender 5 layered actions, with a legacy fallback for older files."""
    paths = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                if slot is None or bag.slot_handle != slot.handle:
                    continue
                paths.extend(fc.data_path for fc in bag.fcurves)
    if hasattr(action, "fcurves"):
        paths.extend(fc.data_path for fc in action.fcurves)
    return paths


def arithmetic_only(expression, names):
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult,
               ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd, ast.Constant,
               ast.Name, ast.Load)
    try:
        nodes = list(ast.walk(ast.parse(expression, mode="eval")))
        return all(isinstance(node, allowed) and
                   (not isinstance(node, ast.Name) or node.id in names)
                   for node in nodes)
    except (SyntaxError, TypeError):
        return False


def audit_static_render_state():
    """Fail closed: this optimization is only for this transform-only paper film."""
    reasons = []
    allowed_paths = {"location", "rotation_euler", "rotation_quaternion", "scale", "hide_render"}
    node_types = {"ShaderNodeBsdfPrincipled", "ShaderNodeBump", "ShaderNodeMath",
                  "ShaderNodeOutputMaterial", "ShaderNodeTexImage", "ShaderNodeTexNoise",
                  "ShaderNodeBackground", "ShaderNodeOutputWorld",
                  "ShaderNodeTexCoord", "ShaderNodeVectorMath", "ShaderNodeValToRGB"}
    if scene.render.engine != "BLENDER_EEVEE":
        reasons.append("Only the audited EEVEE renderer is supported")
    if getattr(scene.render, "use_motion_blur", True):
        reasons.append("Motion blur is enabled or its state cannot be proved")
    if getattr(scene.eevee, "use_motion_blur", False):
        reasons.append("EEVEE motion blur is enabled")
    if scene.animation_data:
        reasons.append("Scene has animation data")
    for prop in ("node_tree", "compositing_node_group", "compositor_node_group"):
        if getattr(scene, prop, None):
            reasons.append("Scene has a compositor tree: " + prop)
    for handler_name in ("frame_change_pre", "frame_change_post", "depsgraph_update_pre",
                         "depsgraph_update_post", "render_pre", "render_post"):
        if getattr(bpy.app.handlers, handler_name):
            reasons.append("Custom handlers present: " + handler_name)
    if scene.sequence_editor:
        if any(strip.type != "SOUND" for strip in scene.sequence_editor.strips):
            reasons.append("Sequencer has visual strips")
    for ob in scene.objects:
        if ob.type not in {"MESH", "CURVE", "FONT", "EMPTY", "LIGHT", "CAMERA"}:
            reasons.append("Unsupported object type: " + ob.name)
        if ob.instance_type != "NONE" or ob.particle_systems or ob.constraints:
            reasons.append("Instance/particle/constraint object: " + ob.name)
        if any(mod.type not in {"BEVEL", "SOLIDIFY"} for mod in ob.modifiers):
            reasons.append("Unsupported modifier: " + ob.name)
        if ob.data and getattr(ob.data, "shape_keys", None):
            reasons.append("Shape keys: " + ob.name)
        anim = ob.animation_data
        if not anim:
            continue
        if anim.nla_tracks:
            reasons.append("NLA strips: " + ob.name)
        if anim.action:
            paths = action_paths(anim.action, getattr(anim, "action_slot", None))
            if not paths or any(prop not in allowed_paths for prop in paths):
                reasons.append("Unproved or non-transform action: " + ob.name)
        for curve in anim.drivers:
            driver = curve.driver
            names = {variable.name for variable in driver.variables}
            if curve.data_path not in allowed_paths or driver.type != "SCRIPTED":
                reasons.append("Unsupported driver output: " + ob.name)
            if not arithmetic_only(driver.expression, names):
                reasons.append("Driver expression is not pure transform arithmetic: " + ob.name)
            for variable in driver.variables:
                if variable.type != "TRANSFORMS":
                    reasons.append("Non-transform driver input: " + ob.name)
                for target in variable.targets:
                    if target.id not in scene.objects.values() or target.bone_target:
                        reasons.append("External/bone driver input: " + ob.name)
    data_groups = (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights,
                   bpy.data.materials, bpy.data.worlds, bpy.data.collections)
    for group in data_groups:
        for data in group:
            animation = getattr(data, "animation_data", None)
            if not animation:
                continue
            # The v05 camera widens during page turns. Permit only this single
            # evaluated projection scalar; every other data animation fails closed.
            if isinstance(data, bpy.types.Camera):
                paths = action_paths(animation.action, getattr(animation, "action_slot", None)) if animation.action else []
                if (not paths or set(paths) != {"ortho_scale"} or animation.drivers
                        or animation.nla_tracks):
                    reasons.append("Unsupported camera data animation: " + data.name)
            else:
                reasons.append("Animated data: " + data.name)
    for image in bpy.data.images:
        if image.source != "FILE" or not image.packed_file:
            reasons.append("Non-packed/non-static image: " + image.name)
    for group in (bpy.data.materials, bpy.data.worlds):
        for data in group:
            tree = data.node_tree
            if not tree:
                continue
            if tree.animation_data:
                reasons.append("Animated node tree: " + data.name)
            for node in tree.nodes:
                if node.bl_idname not in node_types:
                    reasons.append("Unproved material/world node: " + node.bl_idname)
                if node.bl_idname == "ShaderNodeTexCoord":
                    if node.object or any(link.from_socket.name not in {"Generated", "UV"}
                                          for link in tree.links if link.from_node == node):
                        reasons.append("Unproved coordinate dependency: " + data.name)
    return sorted(set(reasons))


def static_properties(value):
    """Capture static scalar/array RNA attributes without traversing ID pointers."""
    result = {}
    if value is None:
        return result
    for prop in value.bl_rna.properties:
        name = prop.identifier
        if name == "rna_type" or prop.type in {"POINTER", "COLLECTION"}:
            continue
        try:
            item = getattr(value, name)
            if getattr(prop, "is_array", False):
                item = list(item)
            if isinstance(item, (str, int, float, bool, list, tuple)) or item is None:
                result[name] = item
        except (AttributeError, TypeError, ValueError):
            continue
    return result


def static_material_signature(material):
    result = {"name": material.name_full, "properties": static_properties(material), "nodes": []}
    tree = material.node_tree
    if tree:
        for node in sorted(tree.nodes, key=lambda item: item.name):
            result["nodes"].append({
                "name": node.name, "type": node.bl_idname, "properties": static_properties(node),
                "inputs": [static_properties(socket) for socket in node.inputs],
                "image": node.image.name_full if getattr(node, "image", None) else None,
                "ramp": {"interpolation": node.color_ramp.interpolation,
                         "elements": [(element.position, list(element.color))
                                      for element in node.color_ramp.elements]}
                        if hasattr(node, "color_ramp") else None,
            })
        result["links"] = sorted((link.from_node.name, link.from_socket.identifier,
                                  link.to_node.name, link.to_socket.identifier) for link in tree.links)
    return result


cache_reasons = audit_static_render_state()
cache_enabled = not cache_reasons
state_sources = {}
static_prefix = b""
ordered_objects = sorted(scene.objects, key=lambda item: item.name_full)
if cache_enabled:
    # The source digest covers immutable mesh vertices/UVs, packed pixels, curves,
    # collection visibility and all other saved static data. Explicit signatures
    # additionally describe the actual materials/camera/light data in this run.
    static_description = {
        "source_fingerprint": fingerprint,
        "materials": [static_material_signature(mat) for mat in sorted(bpy.data.materials, key=lambda item: item.name_full)],
        "world": static_material_signature(scene.world),
        "objects": [{"name": ob.name_full, "type": ob.type,
                     "data": ob.data.name_full if ob.data else None,
                     "materials": [slot.material.name_full if slot.material else None for slot in ob.material_slots],
                     "modifiers": [static_properties(mod) for mod in ob.modifiers],
                     "light_camera_properties": static_properties(ob.data) if ob.type in {"LIGHT", "CAMERA"} else None}
                    for ob in ordered_objects],
    }
    static_prefix = hashlib.sha256(json.dumps(static_description, sort_keys=True, default=str).encode()).digest()
print("INTRO_HOLD_CACHE_AUDIT", json.dumps({"enabled": cache_enabled, "reasons": cache_reasons}, ensure_ascii=False), flush=True)


def visible_state(frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    digest = hashlib.sha256(static_prefix)
    digest.update(scene.camera.name_full.encode())
    for ob in ordered_objects:
        # Empties do not render. Their evaluated transforms propagate into their
        # children. Camera is included regardless of its own render-hidden flag.
        if ob.type == "EMPTY" or (ob.hide_render and ob != scene.camera):
            continue
        evaluated = ob.evaluated_get(depsgraph)
        digest.update(ob.name_full.encode() + b"\0" + ob.type.encode() + b"\0")
        digest.update((ob.data.name_full if ob.data else "").encode() + b"\0")
        digest.update(struct.pack("<16d", *(value for row in evaluated.matrix_world for value in row)))
        if ob.type == "CAMERA":
            camera_data = evaluated.data
            digest.update(camera_data.type.encode() + b"\0" + camera_data.sensor_fit.encode())
            digest.update(struct.pack("<8d", camera_data.ortho_scale, camera_data.lens,
                                      camera_data.shift_x, camera_data.shift_y,
                                      camera_data.clip_start, camera_data.clip_end,
                                      camera_data.sensor_width, camera_data.sensor_height))
    return digest.hexdigest()


if audit_only:
    states = set()
    if cache_enabled:
        for frame in range(start, end + 1):
            states.add(visible_state(frame))
    print("INTRO_HOLD_CACHE_DRY_RUN", json.dumps({"enabled": cache_enabled, "reasons": cache_reasons,
          "range": [start, end], "frames": end - start + 1, "unique_states": len(states),
          "potential_reused": end - start + 1 - len(states) if cache_enabled else 0}), flush=True)
    raise SystemExit(0)


def complete_jpeg(path):
    if not path.exists() or path.stat().st_size < 10000:
        return False
    with path.open("rb") as stream:
        if stream.read(2) != b"\xff\xd8":
            return False
        stream.seek(-2, 2)
        return stream.read(2) == b"\xff\xd9"


def save_manifest():
    result = {"fingerprint": fingerprint, "fingerprint_sha256": fingerprint_hash,
              "source_tags": "source_tags/frame_NNNN.sha256",
              "hold_cache": {"enabled": cache_enabled, "audit_reasons": cache_reasons,
                             "comparison": "exact evaluated visible matrices plus audited static source/data/material state"}}
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")


started = time.monotonic()
rendered = reused = skipped = 0
save_manifest()
for frame in range(start, end + 1):
    target = destination / f"frame_{frame:04d}.jpg"
    tag = source_tags / f"frame_{frame:04d}.sha256"
    matches = tag.exists() and tag.read_text(encoding="ascii").strip() == fingerprint_hash
    state = visible_state(frame) if cache_enabled else None
    if matches and complete_jpeg(target):
        skipped += 1
        if state:
            state_sources.setdefault(state, target)
        continue
    cached = state_sources.get(state) if state else None
    if cached and cached != target and complete_jpeg(cached):
        shutil.copyfile(cached, target)
        reused += 1
    else:
        scene.frame_set(frame)
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        rendered += 1
    if not complete_jpeg(target):
        raise RuntimeError(f"Incomplete output after rendering frame {frame}")
    tag.write_text(fingerprint_hash + "\n", encoding="ascii")
    if state:
        state_sources.setdefault(state, target)
    if frame % 24 == 0 or frame == end:
        print("INTRO_PROGRESS", frame, end, "rendered", rendered, "reused", reused,
              "resumed", skipped, "elapsed_s", round(time.monotonic()-started, 1), flush=True)
print("INTRO_RENDER_COMPLETE", start, end, "rendered", rendered, "reused", reused, "resumed", skipped, flush=True)
