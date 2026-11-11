"""Run with Blender --background --python build_props.py [-- --build-only]."""
import sys, json, hashlib, math
from pathlib import Path
import bpy, bmesh
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=ROOT/"01_游戏开发/Models/首关道具_v01_20261111"
sys.path.insert(0,str(HERE))
from scene_helpers import SceneAPI
from paper_materials import enhance_materials
from props_geometry import build_props, VERSION, PAIR_KEY, PAPER_W, PAPER_D, RED_RECTS

TASKS={
 "F04":{"player":"单件拿放、递交、共享台暂存","program":"原子转移单件所有权；满手拒收；失败保留源物件","acceptance":"同帧争抢仅一人得到纸；共享台始终只占一格"},
 "F05":{"player":"空手按住抄纸","program":"2秒工作量与可中断进度；唯一操作者；湿纸待取","acceptance":"松手续做；未取湿纸不能产第二张"},
 "F06":{"player":"湿纸入指定挂位，等待后取干纸","program":"双槽独立4秒计时；单张状态wet->dry","acceptance":"A完成不影响B；第三张拒收；暂停冻结"},
 "F07":{"player":"干纸放印台并按住印刷","program":"2秒工作量；绑定排序组合键；只在成功后切black","acceptance":"湿纸拒收；黑票可见纸团和印桃、钱纹与票文，红印不可见"},
 "F08":{"player":"黑票放盖印台按住盖章","program":"1秒工作量；成功一次启用red层；禁重复盖印","acceptance":"同一朱印组只启用一次；black/red底纸与黑墨层不重复叠纸"},
 "F09":{"player":"手持朱票在窗口交付","program":"立即消耗票、单次计分并更新订单；固定回执反馈","acceptance":"黑票拒收；连续按键不重复消耗/计分；回执不是新物料"},
}

PLACEMENTS={
 "tool_papermaking_screen":{"station":"station_pulp","local_xyz":[.27,0,.5185],"rotation_xyz_degrees":[0,0,0]},
 "tool_print_brush":{"station":"station_print","local_xyz":[.52,-.21,.682],"rotation_xyz_degrees":[0,0,0]},
 "tool_ink_dish":{"station":"station_print","local_xyz":[.52,.23,.682],"rotation_xyz_degrees":[0,0,0]},
 "tool_rubbing_pad":{"station":"station_print","local_xyz":[-.64,.25,.65],"rotation_xyz_degrees":[0,0,0]},
 "tool_print_block":{"station":"station_print","local_xyz":[-.23,0,.65],"rotation_xyz_degrees":[0,0,0]},
 "tool_stamp":{"station":"station_stamp","local_xyz":[.53,.16,.67],"rotation_xyz_degrees":[0,0,0]},
 "tool_ink_pad":{"station":"station_stamp","local_xyz":[.52,-.22,.65],"rotation_xyz_degrees":[0,0,0]},
 "marker_delivery_receipt":{"station":"station_delivery","local_xyz":[.54,.04,.65],"rotation_xyz_degrees":[0,0,0]},
 "paper_wet":{"station":"station_dry","slot":"A","local_xyz":[-.5,-.085,1.0],"rotation_xyz_degrees":[90,0,0],"preview_only":True},
 "paper_dry":{"station":"station_dry","slot":"B","local_xyz":[.5,-.085,1.0],"rotation_xyz_degrees":[90,0,0],"preview_only":True},
 "paper_black":{"station":"station_print","local_xyz":[-.23,0,.725],"rotation_xyz_degrees":[0,0,0],"preview_only":True},
 "paper_red":{"station":"station_stamp","local_xyz":[-.21,0,.669],"rotation_xyz_degrees":[0,0,0],"preview_only":True},
 "woodcut_zhituan":{"station":None,"usage":"排版层源件；雕版已有完整首款图，不在台面再摆一件"},
 "woodcut_yintao":{"station":None,"usage":"排版层源件；雕版已有完整首款图，不在台面再摆一件"},
 "layer_red_seal":{"parent":"paper_black","local_xyz":[0,0,.0073],"usage":"替代paper_red状态整件的可选叠层方法；两种切换方法不能同时使用"},
}
REPLACE={
 "station_pulp":{"remove_subtrees":["station_pulp__screen_pivot"],"keep":["slot_0","water","vat"]},
 "station_print":{"remove_subtrees":["station_print__ink_dish_pivot","station_print__printing_brush_pivot"],"remove_prefixes":["station_print__print_block_","station_print__print_ink_surface","station_print__block_","station_print__engraved_"],"keep":["tool_tray","slot_0","interaction_main","standing_main"]},
 "station_stamp":{"remove_subtrees":["station_stamp__seal_pivot"],"remove_prefixes":["station_stamp__inkpad_tray","station_stamp__red_inkpad","station_stamp__inkpad_scroll","station_stamp__sample_ticket","station_stamp__note_"],"keep":["seal_contact","slot_0","interaction_main","standing_main"]},
 "station_dry":{"remove_prefixes":["station_dry__preview_A","station_dry__preview_B","station_dry__wet_drop","station_dry__dry_corner_crease"],"keep":["slot_A","slot_B","clip_pivot_A","clip_pivot_B"]},
 "station_delivery":{"remove_exact":["station_delivery__receipt_tag","station_delivery__receipt_text"],"keep":["receipt_anchor","receiving_slot","tray_base","scroll_sign_pivot"]},
}


def children(root):
    result=[root]
    for child in root.children:result.extend(children(child))
    return result


def bounds(root):
    dg=bpy.context.evaluated_depsgraph_get();points=[]
    inv=root.matrix_world.inverted()
    for ob in children(root):
        if ob.type!="MESH":continue
        ev=ob.evaluated_get(dg);me=ev.to_mesh()
        points.extend(inv@ob.matrix_world@v.co for v in me.vertices)
        ev.to_mesh_clear()
    low=[min(p[i] for p in points) for i in range(3)]
    high=[max(p[i] for p in points) for i in range(3)]
    return {"min":low,"max":high,"size":[high[i]-low[i] for i in range(3)]}


def prepare_meshes():
    for ob in list(bpy.context.scene.objects):
        if ob.type=="CURVE":ob.data.use_fill_caps=True
    bpy.ops.object.select_all(action='DESELECT')
    curves=[ob for ob in bpy.context.scene.objects if ob.type=="CURVE"]
    for ob in curves:ob.select_set(True)
    if curves:
        bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    for ob in [ob for ob in bpy.context.scene.objects if ob.type=="MESH"]:
        bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
        if not ob.get("open_art_surface"):
            bm=bmesh.new();bm.from_mesh(ob.data)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.to_mesh(ob.data);bm.free();ob.data.update()
        if not ob.get("preserve_source_uv"):
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.cube_project(cube_size=1,correct_aspect=False,scale_to_bounds=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        ob.select_set(False)


def record(root):
    objects=children(root);mesh=[o for o in objects if o.type=="MESH"]
    anchors={o.name.split("__",1)[1]:{"position_local":list(o.location),"role":o.get("role","")}
             for o in objects if o.type=="EMPTY" and o!=root}
    box=bounds(root)
    return {"asset_id":root.name,"display_name":root["display_name"],"task_ids":root["task"].split(","),
            "version":VERSION,"role":root["role"],"carryable":bool(root["carryable"]),
            "inventory_units":root["inventory_units"],"art_asset_quantity":1,
            "material_state":root.get("material_state",""),"pair_key":root.get("pair_key",""),
            "bounds_m":box,"mesh_count":len(mesh),
            "triangles":sum(len(p.vertices)-2 for ob in mesh for p in ob.data.polygons),
            "anchors":anchors,"placement":PLACEMENTS[root.name],
            "glb":"GLB/"+root.name+".glb","shared_blend":"首关纸艺道具包_v01_20261111.blend",
            "paper_state_interface":"纸张状态接口_v01_20261111.json",
            "artwork_status":root.get("artwork_status",root.get("engraving_status","modeled_papercraft")),
            "validation_status":"awaiting independent GLB reimport; Blender geometry built"}


def aim(ob,point):ob.rotation_euler=(Vector(point)-ob.location).to_track_quat('-Z','Y').to_euler()


def presentation(api,roots):
    api.collection("90_Presentation_not_exported")
    for index,root in enumerate(roots):
        row,col=divmod(index,5);root.location=((col-2)*1.12,(1-row)*1.05,0)
        root["gallery_translation_only"]=True
        api.text("label_"+root.name,root["display_name"],(root.location.x,root.location.y-.44,.001),.085,"ink")
    backdrop=bpy.data.materials.new('MAT_props_studio_warmgray');backdrop.use_nodes=True
    bsdf=next((n for n in backdrop.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) or backdrop.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    output=next((n for n in backdrop.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None) or backdrop.node_tree.nodes.new('ShaderNodeOutputMaterial')
    backdrop.node_tree.links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value=(.45,.40,.32,1);bsdf.inputs['Roughness'].default_value=.9
    floor=api.box("presentation_ground",(0,0,-.026),(200,200,.05),backdrop,bevel=0)
    world=bpy.data.worlds.new("Warm studio daylight");world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.75,.81,.9,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.32
    bpy.context.scene.world=world
    for name,loc,power,size in (("large_key",(-3,-4,7),240,6),("soft_fill",(4,1,5),126,5)):
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        ob=bpy.data.objects.new(name,data);api.current.objects.link(ob);ob.location=loc;aim(ob,(0,0,0))
    cameras=[]
    for name,loc,target,scale in (("Camera_Overview",(2.2,-5.8,8),(0,0,0),6.6),
                                 ("Camera_Black_Red",(.56,1.05,6),(.56,1.05,0),2.0)):
        data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale
        ob=bpy.data.objects.new(name,data);api.current.objects.link(ob);ob.location=loc;aim(ob,target)
        cameras.append(ob)
    return cameras


def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'GLB').mkdir(exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene['asset_pack']='首关独立纸艺道具';scene['version']=VERSION
    scene['status']='Model assets validated separately; Unity gameplay not tested'
    api=SceneAPI();enhance_materials(api)
    roots=build_props(api,OUT/'Textures/首款组合交子_原图副本_v01_20261111.png')
    assert len(roots)==15
    prepare_meshes();bpy.context.view_layer.update()
    inventory=[]
    for root in roots:
        item=record(root)
        assert item['bounds_m']['min'][2]>=-0.00001,(root.name,item['bounds_m'])
        assert abs(item['bounds_m']['min'][2])<.0001 or root.name=='layer_red_seal'
        bpy.ops.object.select_all(action='DESELECT')
        for ob in children(root):ob.select_set(True)
        bpy.context.view_layer.objects.active=root
        path=OUT/item['glb']
        bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
            export_apply=True,export_extras=True,export_yup=True,export_animations=False)
        item['glb_bytes']=path.stat().st_size;item['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        inventory.append(item)
        print('EXPORTED',root.name,item['bounds_m']['size'],flush=True)
    bpy.ops.object.select_all(action='DESELECT')
    cameras=presentation(api,roots)
    scene.camera=cameras[0];scene.render.engine='CYCLES';scene.cycles.samples=48
    scene.cycles.use_denoising=True;scene.cycles.device='GPU'
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='CUDA';prefs.get_devices()
        for device in prefs.devices:device.use=device.type=='CUDA'
    except Exception:scene.cycles.device='CPU'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.resolution_percentage=100
    blend=OUT/'首关纸艺道具包_v01_20261111.blend'
    note=bpy.data.texts.new('READ_ME_纸艺道具接口')
    note.write('15 independent assets. Root origins are bottom-centre in each standalone GLB.\n'
               'Shared BLEND arranges roots in a review gallery; reset only the root location when appending.\n'
               'Paper .42 x .60 m, +Z face, physical grip at (0,+.21,.006).\n'
               'HoldPoint already offset to sheet centre uses attach_pivot=(0,0,0), not grip_pivot again.\n'
               'Tools are fixed to stations and are not inventory items.\n'
               'Black UV patches omit BOTH red seal regions. Red states restore them in one layer group.\n'
               'Formal first-pair composite reference is preserved; this is not a 15-combination compositor.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    source=ROOT/'03_历史成果/原工作区/output/jiaozi-production-assets-20261103/08_组合交子_纸团印桃.png'
    manifest={"version":VERSION,"blender":bpy.app.version_string,"units":"metres","asset_count":15,
              "paper_size_m":[PAPER_W,PAPER_D],"character_reference_height_m":1.2,"table_reference_height_m":.65,
              "pair_ids":["yintao","zhituan"],"pair_key":PAIR_KEY,
              "task_contracts":TASKS,"assets":inventory,"replace_v05_objects":REPLACE,
              "artwork_source":{"path":str(source),"sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
                  "copy":"Textures/首款组合交子_原图副本_v01_20261111.png","original_pixels_unchanged":True,
                  "red_rectangles_source_pixels":RED_RECTS,"layer_method":"UV-region geometry masks; no baked RGB replacement",
                  "scope":"first pair only; no claim of reusable 15-pair source layers"},
              "code_repository_commit":None,"unity_runtime_tested":False,
              "validation_report":"道具实测验证_v01_20261111.json"}
    (OUT/'资产清单_v01_20261111.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    interface={"version":VERSION,"pair_key_rule":"lexical sort stable IDs then join with |; map to code repository if it differs",
               "pair_key":PAIR_KEY,"states":["wet","dry","black","red"],
               "states_to_asset":{state:"paper_"+state for state in ("wet","dry","black","red")},
               "ownership":"one player hand OR one station slot OR consumed; exactly one item",
               "replace_visual":"replace the state root, preserve gameplay paper ID, owner and pair key",
               "optional_red_layer":"keep paper_black and add layer_red_seal at (0,0,.0073) once instead of replacing with paper_red; never both",
               "attach_to_HoldPoint":"asset.attach_pivot=(0,0,0); character HoldPoint is already at paper centre",
               "attach_to_PalmCenter":"先校准掌面 contact 坐标系（骨中心不是表面），再 asset_world = calibrated_palm_contact_world @ inverse(grip_local)。不能直接使用骨中心 PalmCenter_world 宣称与 HoldPoint 零偏移挂接等价。主方案优先使用已经校准的 HoldPoint。",
               "palm_surface_calibration":"本轮局部坐标约定下：calibrated_palm_contact_world = PalmCenter_world @ Translation(0,0,0.031)。再乘 inverse(grip_local)，得到相对 PalmCenter 的 Translation(0,-0.21,0.025)，与当前 HoldPoint 严格等价；不能重复叠加 HoldPoint 偏移。",
               "physical_grip_local_m":[0,.21,.006],"palm_contacts_local_m":[[-.19,.21,.006],[.19,.21,.006]],
               "current_two_character_calibration":{"character_height_m":1.2,"palm_span_m":.38,
                   "PalmCenter_approx_m":[0,-.245,.378],"HoldPoint_approx_m":[0,-.455,.403],
                   "contact_offset_from_PalmCenter_m":[0,0,.031],
                   "HoldPoint_offset_from_PalmCenter_m":[0,-.21,.025],
                   "source":"角色代理本轮实测；角色包与主整合场景负责最终持纸画面核验"},
               "table_place":"match placement_pivot with station paper anchor",
               "rack_place":"rotate X +90 degrees, then align paper centre root to slot A/B centre; +Z paper normal becomes -Y",
               "fixed_tools":"inventory_units=0, carryable=false; only animation_pivot/contact_point are driven by station animation",
               "work_events":"rule success drives visuals; models never award score, consume paper or add workflow steps",
               "coordinates":"Blender XY plane Z up -> glTF X,Z,-Y (Y up); target Unity importer still needs live verification"}
    (OUT/'纸张状态接口_v01_20261111.json').write_text(json.dumps(interface,ensure_ascii=False,indent=2),encoding='utf-8')
    if '--build-only' not in sys.argv:
        for camera,name,res in ((cameras[0],'预览_首关道具总览_v01_20261111.png',(1800,1250)),
                                (cameras[1],'预览_黑票与朱票分层_v01_20261111.png',(1600,1000))):
            scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=res
            scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
            print('RENDERED',name,flush=True)
        scene.camera=cameras[0];bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    print('PROPS_BUILD_COMPLETE',flush=True)


if __name__=='__main__':main()
