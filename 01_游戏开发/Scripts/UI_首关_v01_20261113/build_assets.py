"""Original vector UI kit and source-native portrait renders. No source edits.
Run with bundled Python for SVG/source copies; Blender --python ... -- --portraits.
PNG rasterization is performed by build_assets_png.mjs using a disposable browser.
"""
from pathlib import Path
import json, shutil, hashlib, sys, math

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'01_游戏开发/Art/UI_首关_v01_20261113/assets'
OUT.mkdir(parents=True,exist_ok=True)
PAPER='#fff2cf';INK='#294c67';RED='#bf4932';GOLD='#e8ad3b';LINE='#815639'
ASSETS=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def svg(name,body,size=(128,128),border=None):
    w,h=size
    defs='''<defs><linearGradient id="paper" x2=".9" y2="1"><stop stop-color="#fff8df"/><stop offset="1" stop-color="#efdaad"/></linearGradient><linearGradient id="red" x2="0" y2="1"><stop stop-color="#cf5940"/><stop offset="1" stop-color="#a83728"/></linearGradient></defs>'''
    text=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{defs}{body}</svg>'
    (OUT/(name+'.svg')).write_text(text,encoding='utf-8')
    ASSETS.append({'id':name,'source':name+'.svg','file':name+'.png','width':w,'height':h,'alpha':True,'nine_slice_lbrt':border,'padding_px':8,'dynamic_text_baked':False})
def generate_vectors():
    # All typography belongs to live UI. Paper bevels remain broad and sparse.
    svg('panel_paper','''<path d="M12 19H244L252 27V244L244 252H18L7 240V27Z" fill="#784933" opacity=".3"/><path d="M8 8H240L248 16V235L240 244H16L8 235Z" fill="url(#paper)" stroke="#a87545" stroke-width="2"/><path d="M18 20H234V230H22V26H228" fill="none" stroke="#d2ad6b" stroke-width="2"/><path d="M8 8L25 13H230L240 8M248 16L239 25V224L248 235" fill="none" stroke="#fff9e8" stroke-width="4"/><path d="M30 40H45M30 40V55M226 40H211M226 40V55M30 214H45M30 214V199M226 214H211M226 214V199" fill="none" stroke="#ad7244" stroke-width="3"/>''',(256,256),[64,64,64,64])
    for state,fill,border,top,shadow in [('normal','#bf4932','#883825',10,True),('hover','#d85b3b','#8d3624',8,True),('pressed','#9f3828','#742b20',17,False),('disabled','#b7a58c','#96866e',10,True),('focus','#bf4932','#294c67',10,True)]:
        stroke=5 if state=='focus' else 2
        body=(f'<path d="M12 24H310V83L302 90H20L10 81Z" fill="#653725" opacity=".42"/>' if shadow else '')
        body+=f'<path d="M12 {top}H302L312 {top+10}V76L302 84H20L10 75V20Z" fill="{fill}" stroke="{border}" stroke-width="{stroke}"/><path d="M24 {top+8}H294M20 25V65" stroke="#ffe8ab" stroke-width="2" opacity=".55"/><path d="M26 71H294" stroke="#742b20" stroke-width="2" opacity=".4"/><path d="M30 38h8v-8m244 8h-8v-8M30 56h8v8m244-8h-8v8" fill="none" stroke="#f7dcb0" stroke-width="2" opacity=".7"/>'
        svg('button_primary_'+state,body,(320,96),[48,28,48,28])
    svg('button_secondary','<path d="M12 16H302L312 26V78L302 88H20L10 78V26Z" fill="#6a4d35" opacity=".25"/><path d="M12 8H302L312 18V70L302 80H20L10 70V18Z" fill="url(#paper)" stroke="#294c67" stroke-width="3"/><path d="M25 18H295M25 70H295" stroke="#c6a16e" stroke-width="2"/>',(320,96),[32,24,32,24])
    svg('progress_track','<rect x="5" y="8" width="310" height="18" rx="9" fill="#60462f" opacity=".23"/><rect x="4" y="4" width="312" height="18" rx="9" fill="#e2c99a" stroke="#926c44" stroke-width="2"/>',(320,32),[16,12,16,12])
    svg('progress_fill','<rect x="4" y="4" width="312" height="18" rx="9" fill="#398680"/><path d="M14 8H303" stroke="#9fd0a1" stroke-width="3" stroke-linecap="round"/>',(320,32),[16,12,16,12])
    for state,color in [('wet','#89cbc4'),('dry',PAPER),('black',PAPER),('red',PAPER)]:
        body=f'<path d="M26 17H94L108 31V107L98 115H29L20 107V25Z" fill="#6b5039" opacity=".2"/><path d="M22 12H90L105 27V101L96 110H25L17 101V21Z" fill="{color}" stroke="#856442" stroke-width="3"/><path d="M90 12V29H105" fill="#fff9e6" stroke="#856442" stroke-width="2"/>'
        if state=='wet':body+='<path d="M51 37C46 49 38 57 38 65a14 14 0 0028 0C66 57 57 48 51 37Z" fill="#2c8587"/><path d="M76 66c-3 7-8 12-8 17a9 9 0 0018 0c0-5-5-10-10-17Z" fill="#2c8587"/><path d="M42 93H87" stroke="#e1ffff" stroke-width="3"/>'
        if state in ('black','red'):body+='<path d="M28 35H92V96H28Z M33 40H87V91H33Z" fill="none" stroke="#344248" stroke-width="2"/><path d="M44 49h30m-30 6h30m-30 6h30M41 80h15v-10H41zm27 0h12V70H68z" fill="none" stroke="#344248" stroke-width="3"/>'
        if state=='dry':body+='<path d="M33 42H86M33 50H74M33 85H86" stroke="#d5b77e" stroke-width="3"/><path d="M78 63l3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z" fill="#e8ad3b"/>'
        if state=='red':body+='<g transform="rotate(-9 84 87)"><rect x="68" y="71" width="33" height="33" rx="2" fill="#bf4932"/><path d="M74 77H95V98H74V77m7 0v14h7V83h7" fill="none" stroke="#fff2cf" stroke-width="2"/></g>'
        svg('icon_'+state,body)
    common=lambda b:f'<path d="M17 20H104L113 29V101L104 113H24L15 104Z" fill="#80543b" opacity=".16"/>{b}'
    svg('icon_clock',common('<circle cx="64" cy="64" r="43" fill="url(#paper)" stroke="#294c67" stroke-width="7"/><path d="M64 33V65L82 77M64 17V10M49 10H79" stroke="#294c67" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M33 64h6m25 30v-6m31-24h-6" stroke="#bf4932" stroke-width="4"/>'))
    svg('icon_pause','<rect x="27" y="22" width="27" height="85" rx="5" fill="#294c67"/><rect x="75" y="22" width="27" height="85" rx="5" fill="#294c67"/><path d="M33 28V97M81 28V97" stroke="#6c94ad" stroke-width="4"/>')
    svg('icon_order','<path d="M31 17H99V109H27V25Z" fill="url(#paper)" stroke="#815639" stroke-width="3"/><path d="M41 10H85V27H41Z" fill="#bf4932"/><path d="M41 44H84M41 59H84M41 74H69" stroke="#294c67" stroke-width="5"/><circle cx="88" cy="92" r="17" fill="#e8ad3b"/><path d="M79 91l6 6 12-13" stroke="#70462b" stroke-width="5" fill="none"/>')
    star='M64 13L79 44L113 48L88 72L94 107L64 90L34 107L40 72L15 48L49 44Z'
    svg('icon_star',f'<path d="{star}" transform="translate(0 5)" fill="#935b2e" opacity=".25"/><path d="{star}" fill="#e8ad3b" stroke="#a56b2d" stroke-width="3"/><path d="M64 13V64L15 48L49 44Z" fill="#ffda64"/><path d="M64 64L94 107L64 90L34 107Z" fill="#ce8b2e"/>')
    svg('icon_lock','<path d="M40 57V39a24 24 0 0148 0V57" fill="none" stroke="#294c67" stroke-width="11"/><rect x="25" y="51" width="78" height="59" rx="8" fill="#e8ad3b" stroke="#946331" stroke-width="3"/><circle cx="64" cy="76" r="9" fill="#294c67"/><path d="M59 77h10v16H59Z" fill="#294c67"/>')
    svg('icon_check','<path d="M15 67L46 100L112 30" stroke="#185b57" stroke-width="19" fill="none" stroke-linejoin="round"/><path d="M15 62L46 95L112 25" stroke="#3f9582" stroke-width="15" fill="none" stroke-linejoin="round"/>')
    for key,color in [('p1',INK),('p2',RED)]:
        # Number/letter lives in DOM/TextElement, these are background tabs only.
        svg('badge_'+key,f'<path d="M20 12H108V104L64 118L20 104Z" fill="{color}" stroke="#fff2cf" stroke-width="4"/><path d="M29 21H99V98L64 108L29 98Z" fill="none" stroke="#fff2cf" stroke-width="2" opacity=".6"/>')
    svg('icon_back','<path d="M68 25L26 64L68 103M29 64H110" fill="none" stroke="#294c67" stroke-width="10" stroke-linejoin="round"/>')
    svg('icon_settings','<path d="M56 14h16l4 16 14 8 16-4 8 14-11 12v16l11 12-8 14-16-4-14 8-4 16H56l-4-16-14-8-16 4-8-14 11-12V60L14 48l8-14 16 4 14-8Z" fill="#294c67"/><circle cx="64" cy="68" r="21" fill="#fff2cf"/><circle cx="64" cy="68" r="10" fill="#bf4932"/>')

def copy_sources():
    files={
      'scene.png':'01_游戏开发/Models/首关整合_v02_20261111/预览_触台比例全景_v02_20261111.png',
      'logo.png':'01_游戏开发/Art/品牌标识/方形Logo_v01_20261110/Logo_交子赶工记_正方形_v01_20261110.png',
      'ticket.png':'01_游戏开发/Art/开场纸书_v05_20261111/assets/组合交子_纸团印桃_引用_v01.png',
      'preview_music.wav':'01_游戏开发/Art/开场纸书_v05_20261111/assets/开场配乐与纸声_v05.wav'}
    records=[]
    for target,source in files.items():
        p=ROOT/source;shutil.copyfile(p,OUT/target)
        records.append({'file':target,'source_repo_path':source,'sha256':sha(p),'copied_bytes_identical':sha(p)==sha(OUT/target),'purpose':'Existing preview soundtrack for UI volume audition; not new final gameplay music.' if target.endswith('.wav') else 'Existing approved local visual reference, unmodified byte copy.'})
    metadata=ROOT/'01_游戏开发/Art/开场纸书_v05_20261111/assets/开场音轨来源_v05.json'
    if metadata.exists():shutil.copyfile(metadata,OUT/'preview_music_source.json')
    return records

def render_portraits():
    import bpy
    from mathutils import Vector
    records=[]
    for cid,label in [('zhituan','纸团'),('yintao','印桃')]:
        source=ROOT/f'01_游戏开发/Models/首批角色_v02_20261111/角色_{label}_整合_v02_20261111.blend'
        before=sha(source)
        bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
        scene=bpy.context.scene
        rig=bpy.data.objects['rig_'+cid];act=bpy.data.actions[cid+'_Idle'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
        scene.frame_set(1)
        scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE'
        pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
        for device in pref.devices:device.use=device.type=='CUDA'
        scene.cycles.device='GPU';scene.render.film_transparent=True
        scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
        scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
        world=bpy.data.worlds.new('UI portrait studio');world.use_nodes=True;scene.world=world
        world.node_tree.nodes['Background'].inputs['Color'].default_value=(.55,.53,.49,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
        for name,loc,energy,size in [('Key',(-3,-4,5),330,4),('Fill',(4,-1,3),140,3),('Rim',(0,3,4),180,3)]:
            data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
            ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,.6))-ob.location).to_track_quat('-Z','Y').to_euler()
        data=bpy.data.cameras.new('UI portrait camera');ob=bpy.data.objects.new('UI portrait camera',data);scene.collection.objects.link(ob)
        ob.location=(1.2,-7,1.75);ob.rotation_euler=(Vector((0,0,.61))-ob.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=1.48;scene.camera=ob
        target=OUT/f'portrait_{cid}.png';scene.render.filepath=str(target);bpy.ops.render.render(write_still=True)
        records.append({'file':target.name,'source_repo_path':source.relative_to(ROOT).as_posix(),'source_sha256':before,'source_unmodified':before==sha(source),'width':768,'height':768,'alpha':True,'render':'Cycles CUDA 48 samples, original v02 mesh/Idle frame 1, transparent studio, no model save'})
    (OUT/'portrait_sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')

if '--portraits' in sys.argv:render_portraits()
else:
    generate_vectors();copies=copy_sources()
    manifest={'version':'v01_20261113','authoring':'Original editable SVG vector shapes; PNG rasterization preserves alpha. Existing local art reused only as byte copies. Portraits rendered from actual v02 BLEND, no source model mutation.','reference_resolution':[1920,1080],'color_palette':{'paper':PAPER,'ink':INK,'vermilion':RED,'gold':GOLD},'units':'pixels; nine_slice_lbrt order is left,bottom,right,top','scaling':'Panels/buttons: stretch center, preserve corners. Icons: preserve aspect. Text and changing numbers are separate UI elements.','assets':ASSETS,'copied_sources':copies,'portraits':['portrait_zhituan.png','portrait_yintao.png'],'sprite_count':len(ASSETS),'unity_import':'PNG Texture Type Sprite (2D and UI), sRGB on, Alpha Is Transparency on; use nine_slice_lbrt as Sprite Editor borders. UI Toolkit may use matching -unity-slice values. No Unity import validation claimed.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SVG_COUNT',len(ASSETS),'COPIES',len(copies))
