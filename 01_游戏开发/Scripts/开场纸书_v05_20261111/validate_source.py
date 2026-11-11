"""Read-only validation of the saved v05 Blender source; never renders or saves.

Run: blender -b <Art/v05/开场纸书_v05_20261111.blend> --python validate_source.py
Writes only Art/v05/工程核验_v05.json, even if a check fails.
This is structural/source validation, not Unity or human playback testing.
"""
from pathlib import Path
import hashlib
import json
import math
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "Art" / "开场纸书_v05_20261111"
SOURCE = (OUT / "开场纸书_v05_20261111.blend").resolve()
REPORT = OUT / "工程核验_v05.json"
scene = bpy.context.scene
checks = []


def check(name, passed, detail=None):
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def subtree(root):
    return [root] + list(root.children_recursive)


def geometry(root):
    return [ob for ob in subtree(root) if ob.type in {"MESH", "CURVE", "FONT"}]


def visible_geometry(root):
    return [ob for ob in geometry(root) if not ob.hide_render]


def vec(values):
    return [round(float(value), 6) for value in values]


def get_object(name):
    ob = bpy.data.objects.get(name)
    check("required_object:" + name, ob is not None)
    return ob


source_hash_before = digest(SOURCE)
check("opened_exact_v05_source", Path(bpy.data.filepath).resolve() == SOURCE, bpy.data.filepath)
check("1080p_100_percent", (scene.render.resolution_x, scene.render.resolution_y,
                          scene.render.resolution_percentage) == (1920, 1080, 100))
check("24_fps", scene.render.fps == 24 and abs(scene.render.fps_base - 1) < 1e-9)
check("1152_frames_48_seconds", (scene.frame_start, scene.frame_end) == (1, 1152))
check("active_camera", scene.camera is not None, scene.camera.name if scene.camera else None)

images = [{"name": im.name, "file": im.filepath, "packed": bool(im.packed_file)}
          for im in bpy.data.images if im.source == "FILE"]
fonts_used = {ob.data.font.name: ob.data.font for ob in scene.objects if ob.type == "FONT"}
fonts = [{"name": font.name, "file": font.filepath, "packed": bool(font.packed_file)}
         for font in fonts_used.values()]
sounds = [{"name": sound.name, "file": sound.filepath, "packed": bool(sound.packed_file)}
          for sound in bpy.data.sounds]
check("four_images_packed", len(images) == 4 and all(item["packed"] for item in images), images)
check("used_font_packed", bool(fonts) and all(item["packed"] for item in fonts), fonts)
check("sound_packed", bool(sounds) and all(item["packed"] for item in sounds), sounds)
strips = list(scene.sequence_editor.strips) if scene.sequence_editor else []
sound_strips = [{"name": strip.name, "start": strip.frame_final_start,
                "end_exclusive": strip.frame_final_end,
                "sound": strip.sound.name if strip.sound else None}
               for strip in strips if strip.type == "SOUND"]
check("sound_strip_covers_film", any(item["start"] == 1 and item["end_exclusive"] >= 1153
                                    for item in sound_strips), sound_strips)

chapters = sorted([ob for ob in scene.objects if ob.name.startswith("CHAPTER_")], key=lambda ob: ob.name)
leaves = sorted([ob for ob in scene.objects if ob.name.startswith("TURNING_LEAF_")], key=lambda ob: ob.name)
tabs = sorted([ob for ob in scene.objects if ob.name.startswith("PULL_TAB_")], key=lambda ob: ob.name)
popups = sorted([ob for ob in scene.objects if ob.name.startswith("POPUP_")], key=lambda ob: ob.name)
check("six_chapters", len(chapters) == 6, [ob.name for ob in chapters])
check("five_turning_leaves", len(leaves) == 5, [ob.name for ob in leaves])
check("six_pull_tabs", len(tabs) == 6, [ob.name for ob in tabs])


def chapter_members(index):
    """v05 artwork and ground are deliberately detached from the book/text root."""
    roots = ([chapters[index]] if index < len(chapters) else [])
    roots.extend(ob for name in [f"纸上画幅_{index:02d}", f"PAGE_GROUND_{index:02d}"]
                 if (ob := bpy.data.objects.get(name)))
    roots.extend(ob for ob in popups if ob.name.startswith(f"POPUP_{index:02d}_"))
    return list({ob for root in roots for ob in subtree(root)})


book = get_object("BOOK · 正常双页书册")
table = get_object("暖木桌面")
scene.frame_set(90)
check("book_lies_horizontal_local_x_minus_pi_over_two",
      bool(book and abs(book.rotation_euler.x + math.pi / 2) < 1e-5 and
           abs(book.rotation_euler.y) < 1e-6 and abs(book.rotation_euler.z) < 1e-6))
page_planes = []
if book and table:
    table_top = max((table.matrix_world @ Vector(corner)).z for corner in table.bound_box)
    for name in ["当前左页", "当前右页"]:
        page = get_object(name)
        if not page:
            continue
        evaluated = page.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        normal_matrix = evaluated.matrix_world.to_3x3().inverted().transposed()
        upward = [(normal_matrix @ polygon.normal).normalized().z for polygon in mesh.polygons
                  if polygon.area > .01]
        heights = [(evaluated.matrix_world @ vertex.co).z for vertex in mesh.vertices]
        data = {"object": name, "min_world_z": min(heights), "max_world_z": max(heights),
                "table_top_z": table_top, "upward_faces": sum(z > .97 for z in upward),
                "horizontal_large_faces": sum(abs(z) > .97 for z in upward)}
        page_planes.append(data)
        check("page_surface_horizontal_and_above_table:" + name,
              data["upward_faces"] > 0 and min(heights) > table_top and
              max(heights) - min(heights) < .3, data)
        evaluated.to_mesh_clear()

popup_motion = []
for index in range(6):
    group = [ob for ob in popups if ob.name.startswith(f"POPUP_{index:02d}_")]
    check("popup_hinges_exist_chapter_%d" % (index + 1), bool(group), len(group))
    bad = []
    for popup in group:
        start = index * 192 + 1
        scene.frame_set(start)
        folded = vec(popup.rotation_euler)
        scene.frame_set(start + 89)
        upright = vec(popup.rotation_euler)
        scene.frame_set(start + 164)
        final = vec(popup.rotation_euler)
        valid = (abs(abs(folded[0]) - math.pi / 2) < 1e-5 and
                 max(abs(value) for value in upright) < 1e-5 and
                 abs(folded[1]) < 1e-6 and abs(folded[2]) < 1e-6 and
                 (max(abs(value) for value in final) < 1e-5 if index == 5
                  else abs(final[0] - folded[0]) < 1e-5))
        if not valid:
            bad.append(popup.name)
        popup_motion.append({"object": popup.name, "chapter": index + 1,
                             "folded": folded, "upright": upright, "end": final})
    check("popup_fold_x_to_upright_chapter_%d" % (index + 1), not bad, bad)

leaf_motion = []
leaf_framing = []
for index, leaf in enumerate(leaves):
    first, last = index * 192 + 165, (index + 1) * 192
    samples = []
    for frame in range(first, last + 1):
        scene.frame_set(frame)
        samples.append({"frame": frame, "rotation": vec(leaf.rotation_euler),
                        "hidden": leaf.hide_render})
    angles = [entry["rotation"][2] for entry in samples]
    only_z = all(abs(entry["rotation"][0]) < 1e-6 and abs(entry["rotation"][1]) < 1e-6
                 for entry in samples)
    monotonic = all(angles[n + 1] <= angles[n] + 1e-6 for n in range(len(angles) - 1))
    valid = (only_z and monotonic and abs(angles[0]) < 1e-5 and
             abs(angles[-1] + math.pi) < 1e-5 and all(not entry["hidden"] for entry in samples))
    check("leaf_turn_z_0_to_minus_pi:" + leaf.name, valid)
    spine = (leaf.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    check("leaf_world_spine_parallel_y:" + leaf.name,
          abs(spine.x) < 1e-5 and abs(abs(spine.y)-1) < 1e-5 and abs(spine.z) < 1e-5,
          vec(spine))
    leaf_motion.append({"name": leaf.name, "frame_start": first, "frame_end": last,
                        "first_rotation": samples[0]["rotation"],
                        "last_rotation": samples[-1]["rotation"],
                        "monotonic": monotonic, "only_z": only_z})
    framing = []
    for frame in range(first, last + 1):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        camera = scene.camera.evaluated_get(depsgraph)
        projected = []
        for ob in visible_geometry(leaf):
            evaluated = ob.evaluated_get(depsgraph)
            projected.extend(world_to_camera_view(scene, camera, evaluated.matrix_world @ Vector(corner))
                             for corner in evaluated.bound_box)
        if not projected:
            framing.append({"frame": frame, "empty": True, "in_frame": False})
            continue
        bounds = [min(v.x for v in projected), min(v.y for v in projected),
                  max(v.x for v in projected), max(v.y for v in projected)]
        overflow = max(0, -bounds[0], -bounds[1], bounds[2]-1, bounds[3]-1)
        framing.append({"frame": frame, "bounds_uv": [round(v, 6) for v in bounds],
                        "ortho_scale": camera.data.ortho_scale,
                        "maximum_overflow": round(overflow, 6),
                        "in_frame": overflow <= 1e-5 and min(v.z for v in projected) > 0})
    bad_frames = [entry for entry in framing if not entry["in_frame"]]
    check("turning_leaf_inside_camera:" + leaf.name, not bad_frames, bad_frames)
    leaf_framing.append({"object": leaf.name, "samples": framing, "bad_frames": len(bad_frames)})

driver_links = []
scene.frame_set(858)
for ob in scene.objects:
    if not ob.animation_data:
        continue
    for fcurve in ob.animation_data.drivers:
        driver = fcurve.driver
        for variable in driver.variables:
            for target in variable.targets:
                if target.id in tabs:
                    driver_links.append({"object": ob.name, "property": fcurve.data_path,
                                         "array_index": fcurve.array_index,
                                         "tab": target.id.name, "expression": driver.expression,
                                         "valid": bool(driver.is_valid),
                                         "input_transform": target.transform_type,
                                         "input_space": target.transform_space})
tab_motion = []
for index, tab in enumerate(tabs):
    start = index * 192 + 1
    values = []
    for frame in [start, start + 52, start + 132, start + 151]:
        scene.frame_set(frame)
        values.append({"frame": frame, "location": vec(tab.location)})
    valid_motion = (abs(values[0]["location"][0]) < 1e-6 and
                    values[1]["location"][0] > .7 and
                    abs(values[-1]["location"][0]) < 1e-6)
    links = [link for link in driver_links if link["tab"] == tab.name]
    check("tab_motion:" + tab.name, valid_motion, values)
    check("tab_drives_artwork:" + tab.name, bool(links) and all(link["valid"] for link in links), links)
    tab_motion.append({"tab": tab.name, "samples": values, "driver_count": len(links)})

game_art = [ob for ob in scene.objects
            if ob.get("source_asset") in {"扁平纸团印桃_v02.png", "组合交子_纸团印桃_引用_v01.png"}]
holds = []
for index in range(6):
    frame = 90 + index * 192
    scene.frame_set(frame)
    active = [chapter.name for chapter in chapters if not chapter.hide_render]
    inactive_leaks = [ob.name for number in range(6) if number != index
                      for ob in chapter_members(number)
                      if ob.type in {"MESH", "CURVE", "FONT"} and not ob.hide_render]
    game_visible = [ob.name for ob in game_art if not ob.hide_render]
    check("only_current_chapter_at_hold_%d" % (index + 1),
          len(active) == 1 and len(chapters) == 6 and active[0] == chapters[index].name and not inactive_leaks,
          {"active": active, "inactive_geometry_visible": inactive_leaks})
    check("no_leaf_at_hold_%d" % (index + 1), all(leaf.hide_render for leaf in leaves))
    if index < 4:
        check("no_game_actors_or_pair_bill_in_history_%d" % (index + 1), not game_visible, game_visible)
    holds.append({"frame": frame, "chapter": index + 1, "active": active,
                  "game_art_visible": game_visible,
                  "visible_geometry_count": sum(ob.type in {"MESH", "CURVE", "FONT"} and not ob.hide_render
                                                for ob in chapter_members(index))})

historical_tickets = []
for name, frame in [("民间凭券", 474), ("官发纸币", 474), ("流通纸券", 666)]:
    ob = get_object(name)
    scene.frame_set(frame)
    visible = bool(ob and not ob.hide_render and visible_geometry(ob))
    check("historical_ticket_preserved:" + name, visible)
    historical_tickets.append({"object": name, "frame": frame, "visible": visible})

sheet = get_object("单张纸_完整工序")
printed = get_object("黑墨状态")
sealmark = get_object("朱印状态")
path_samples = []
for frame, stage, expected_x, expected_z in [
    (790, "wet_paper", -3.73, 3.42),
    (833, "drying_slot_0", -2.12, 3.56),
    (865, "printed", .05, 3.16),
    (901, "sealed", 1.8, 3.16),
    (927, "delivered", 3.74, 3.16),
]:
    scene.frame_set(frame)
    valid = bool(sheet and abs(sheet.location.x - expected_x) < .001 and
                 abs(sheet.location.z - expected_z) < .001 and not sheet.hide_render)
    check("single_sheet_path:" + stage, valid)
    path_samples.append({"frame": frame, "stage": stage,
                         "location": vec(sheet.location) if sheet else None,
                         "ink_scale": vec(printed.scale) if printed else None,
                         "seal_scale": vec(sealmark.scale) if sealmark else None})
if printed and sealmark:
    scene.frame_set(833)
    check("dry_sheet_has_no_ink_or_seal", max(printed.scale) < .001 and max(sealmark.scale) < .001)
    scene.frame_set(865)
    check("printed_sheet_has_ink_no_seal", min(printed.scale) > .99 and max(sealmark.scale) < .001)
    scene.frame_set(901)
    check("sealed_sheet_has_ink_and_seal", min(printed.scale) > .99 and min(sealmark.scale) > .99)
sheet_roots = [ob.name for ob in scene.objects if ob.name.startswith("单张纸_完整工序")]
check("one_travelling_sheet_root", len(sheet_roots) == 1, sheet_roots)
slots = [ob.name for ob in scene.objects if ob.name.startswith("晾纸槽_")]
check("two_drying_slots", len(slots) == 2, slots)
stations = ["F05_抄纸槽", "F06_双槽晾纸架", "F07_印刷台", "F08_盖印台", "F09_交付台", "F04_共享台"]
check("five_stations_plus_shared_table", all(bpy.data.objects.get(name) for name in stations), stations)

all_text = [{"object": ob.name, "body": ob.data.body} for ob in scene.objects if ob.type == "FONT"]
character_names = ["纸团", "印桃", "阿楮", "朱小印"]
name_leaks = [item for item in all_text if any(name in item["body"] for name in character_names)]
check("titles_and_captions_no_character_names", not name_leaks, name_leaks)
chapter3_text = [ob.data.body for ob in chapter_members(2) if ob.type == "FONT"]
check("chapter_three_official_jiaozi", "官办交子" in chapter3_text and "益州交子务" in chapter3_text, chapter3_text)
source_hash_after = digest(SOURCE)
check("source_file_unchanged_during_read_only_check", source_hash_before == source_hash_after)

result = {
    "version": "v05_20261111", "blender": bpy.app.version_string,
    "source": str(SOURCE), "source_sha256": source_hash_after,
    "passed": all(item["passed"] for item in checks),
    "checks_passed": sum(item["passed"] for item in checks), "checks_total": len(checks),
    "width": scene.render.resolution_x, "height": scene.render.resolution_y,
    "fps": scene.render.fps, "frames": scene.frame_end - scene.frame_start + 1,
    "duration_seconds": 48, "objects": len(scene.objects),
    "packed_images": images, "packed_fonts": fonts, "packed_sounds": sounds,
    "leaf_motion": leaf_motion, "tab_motion": tab_motion, "driver_links": driver_links,
    "page_world_planes": page_planes, "popup_hinges": len(popups), "popup_motion": popup_motion,
    "turning_leaf_camera_framing": leaf_framing,
    "chapter_hold_samples": holds, "historical_tickets": historical_tickets,
    "single_sheet_path": path_samples, "checks": checks,
    "rendered_in_this_check": False, "source_saved_in_this_check": False,
    "browser_playback_checked": False, "human_visual_review": False,
    "unity_integration_tested": False,
    "limitations": ["Source/structure checks do not prove final visual quality or collision-free page turns.",
                    "No Unity execution, game interaction, browser playback or human viewing was performed."],
}
REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
failed = [item for item in checks if not item["passed"]]
print(json.dumps({"report": str(REPORT), "passed": result["passed"],
                  "checks_passed": result["checks_passed"], "checks_total": len(checks),
                  "failed": failed}, ensure_ascii=False, indent=2), flush=True)
if failed:
    raise RuntimeError("v05 source validation failed; inspect 工程核验_v05.json")
