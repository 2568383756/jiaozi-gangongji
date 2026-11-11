"""Independent headless validation of the delivered GLBs, not just source meshes."""
import sys,json,struct,math,hashlib
from pathlib import Path
import bpy,bmesh

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from build_props import OUT,children,bounds
from props_geometry import RED_RECTS,PAIR_KEY


def glb_json(path):
    data=path.read_bytes();magic,version,length=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and length==len(data)
    n,kind=struct.unpack_from('<I4s',data,12);assert kind==b'JSON'
    return json.loads(data[20:20+n])


def clip(poly,axis,value,keep_greater):
    result=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ina=(a[axis]>=value) if keep_greater else (a[axis]<=value)
        inb=(b[axis]>=value) if keep_greater else (b[axis]<=value)
        if ina:result.append(a)
        if ina!=inb:
            t=(value-a[axis])/(b[axis]-a[axis])
            result.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(2)))
    return result


def overlap_area(poly,rect):
    for axis,value,keep in ((0,rect[0],True),(0,rect[2],False),(1,rect[1],True),(1,rect[3],False)):
        if not poly:return 0
        poly=clip(poly,axis,value,keep)
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))*.5


def main():
    manifest_path=OUT/'资产清单_v01_20261111.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    report={"version":manifest['version'],"blender":bpy.app.version_string,
            "method":"Fresh Blender scene, actual glTF import for each individual GLB; measured vertices and helpers",
            "checks":[],"failures":[],"unity_runtime_tested":False,
            "live_character_hand_test":"parent integration task; not certified by this asset validation"}
    body_signatures={}
    for item in manifest['assets']:
        sid=item['asset_id'];path=OUT/item['glb'];doc=glb_json(path)
        entry={"asset_id":sid,"glb_bytes":path.stat().st_size,"embedded_images":len(doc.get('images',[])),"checks":{}}
        def check(name,condition,detail=None):
            entry['checks'][name]={"pass":bool(condition),"detail":detail}
            if not condition:report['failures'].append(sid+': '+name)
        check('self_contained_images',all('bufferView' in image and 'uri' not in image for image in doc.get('images',[])))
        check('sha256_matches',hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'])
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path))
        bpy.context.view_layer.update()
        roots=[o for o in bpy.context.scene.objects if o.get('asset_id')==sid]
        check('one_asset_root',len(roots)==1)
        if len(roots)!=1:report['checks'].append(entry);continue
        root=roots[0];objects=children(root);meshes=[o for o in objects if o.type=='MESH']
        actual=bounds(root);entry['measured_bounds_m']=actual
        delta=max(abs(actual[key][i]-item['bounds_m'][key][i]) for key in ('min','max','size') for i in range(3))
        check('roundtrip_bounds',delta<.0001,delta)
        check('asset_origin',root.matrix_world.translation.length<1e-6)
        check('placement_anchor',any(o.name==sid+'__placement_pivot' for o in objects))
        check('grip_anchor',any(o.name==sid+'__grip_pivot' for o in objects))
        check('attach_anchor',any(o.name==sid+'__attach_pivot' for o in objects))
        anchor_errors=[]
        for name,expected in item['anchors'].items():
            candidates=[o for o in objects if o.name==sid+'__'+name]
            if len(candidates)!=1:anchor_errors.append(name+': missing');continue
            pos=root.matrix_world.inverted()@candidates[0].matrix_world.translation
            if max(abs(pos[i]-expected['position_local'][i]) for i in range(3))>1e-5:anchor_errors.append(name+': position')
        check('all_anchor_positions',not anchor_errors,anchor_errors)
        check('carry_rule',bool(root.get('carryable'))==(sid in ('paper_wet','paper_dry','paper_black','paper_red')))
        check('finite_vertices',all(math.isfinite(v) for o in meshes for vertex in o.data.vertices for v in vertex.co))
        check('mesh_uvs',all(bool(o.data.uv_layers) for o in meshes))
        check('material_assignments',all(bool(o.data.materials) for o in meshes))
        # Imported glTF splits vertices along UV boundaries: weld a temporary BMesh for signed-volume inspection.
        negative=[];closed_count=0
        for ob in meshes:
            if ob.get('open_art_surface'):continue
            bm=bmesh.new();bm.from_mesh(ob.data)
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
            if all(e.is_manifold for e in bm.edges):
                closed_count+=1
                if bm.calc_volume(signed=True)<-1e-10:negative.append(ob.name)
            bm.free()
        check('closed_mesh_outward_normals',not negative,{"closed_meshes":closed_count,"negative_volume":negative})
        if sid.startswith('paper_'):
            check('paper_xy_size',abs(actual['size'][0]-.42)<.0001 and abs(actual['size'][1]-.60)<.0001)
            body=next(o for o in meshes if o.name.startswith(sid+'__paper_body'))
            body_signatures[sid]=sorted(set(tuple(round(v.co[i],6) for i in range(3)) for v in body.data.vertices))
            check('one_sheet_body',sum(o.name.startswith(sid+'__paper_body') for o in meshes)==1)
            red_layers=[o for o in meshes if o.get('ticket_layer')=='red_seal']
            check('red_layer_rule',len(red_layers)==(1 if sid=='paper_red' else 0),len(red_layers))
        if sid in ('paper_black','paper_red','tool_print_block'):
            ink=[o for o in meshes if o.get('ticket_layer')=='black_ink']
            check('formal_first_pair_art',len(ink)==1 and root.get('pair_key')==PAIR_KEY)
            overlap=0
            regions=[(x0/1024,1-y1/1536,x1/1024,1-y0/1536) for x0,y0,x1,y1 in RED_RECTS]
            for ob in ink:
                uv=ob.data.uv_layers.active.data
                for poly in ob.data.polygons:
                    points=[tuple(uv[li].uv) for li in poly.loop_indices]
                    for region in regions:overlap+=overlap_area(points,region)
            check('black_ink_omits_both_red_regions',overlap<1e-7,overlap)
        report['checks'].append(entry)
        print('VALIDATED',sid,'failures',len(report['failures']),flush=True)
    same=len(body_signatures)==4 and all(sig==body_signatures['paper_dry'] for sig in body_signatures.values())
    report['four_states_share_body_geometry']=same
    if not same:report['failures'].append('four states do not share the same body vertex geometry')
    report['asset_count']=len(report['checks']);report['all_passed']=not report['failures'] and report['asset_count']==15
    report['check_count']=sum(len(item['checks']) for item in report['checks'])+1
    (OUT/'道具实测验证_v01_20261111.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for item in manifest['assets']:item['validation_status']='passed actual GLB reimport' if report['all_passed'] else 'see validation report'
    manifest['headless_validation_passed']=report['all_passed'];manifest['headless_check_count']=report['check_count']
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('VALIDATION_COMPLETE',report['all_passed'],report['check_count'],report['failures'],flush=True)
    assert report['all_passed'],report['failures']


if __name__=='__main__':main()
