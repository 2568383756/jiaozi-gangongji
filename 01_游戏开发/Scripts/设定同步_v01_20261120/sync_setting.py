from pathlib import Path
from zipfile import ZipFile
from itertools import combinations
import xml.etree.ElementTree as ET
import hashlib,json,shutil,re

ROOT=Path('E:/codex-jiaozi/交子赶工记_项目总库_20261104')
OUT=ROOT/'01_游戏开发/Docs/设定同步_v01_20261120'
SRC=OUT/'来源'
SRC.mkdir(parents=True,exist_ok=True)
original=Path('C:/Users/wangjingjing/Desktop/交子赶工记_世界观与开场动画剧本.docx')
copy=SRC/'交子赶工记_世界观与开场动画剧本_用户原件_20261120.docx'
if copy.exists():
    assert copy.read_bytes()==original.read_bytes()
else: shutil.copy2(original,copy)
with ZipFile(original) as z:
    doc=ET.fromstring(z.read('word/document.xml'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
paras=doc.findall('.//w:p',ns)
texts=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in paras]
assert len(texts)==143
(SRC/'用户剧本_正文提取_20261120.md').write_text('# 用户剧本原件正文提取\n\n未替换暂名或原有描述；段号为 OOXML 正文段落顺序，包含表格内段落。\n\n'+'\n\n'.join(f'{i}：{t}' for i,t in enumerate(texts,1) if t.strip())+'\n',encoding='utf-8')

aliases={'阿绒':'烘栗','金豆':'递蕉','墨墨':'墨墩','沐沐':'泡泡'}
overrides={
1:'交子赶工记四动物世界观与开场动画统一剧本',
2:'版本 v01 2026年11月20日　世界观采用用户新剧本　角色正式名与技能沿用旧版四动物',
12:'这时，来自屏幕外的一份好奇响起：“这么薄的一张纸，为什么能当钱？”疑问化成微光，唤醒了长卷。财神暂时稳住入口，让四个钱灵带着玩家的意志进入北宋益州的记忆世界。画面不出现孩子或实体人类。',
21:'玩家的好奇心与四灵建立联系，形成一枚悬浮在画面中的方孔光印。玩家在操作中决定谁先加工、何时抄纸、怎样交接，钱灵用自己的爪子执行。玩家是屏幕外的学徒与见证者，画面不出现玩家身体。',
22:'这种联系直接对应操控动物角色的玩法。两位玩家在开局各选一名不同钱灵，局内不切换。四灵既是可操作角色，也是互相提醒、吐槽和帮忙的伙伴；玩家的代入通过镜头、声音与光印建立，不另加实体人类主角。',
30:'四个钱灵统一使用项目正式名泡泡、递蕉、墨墩、烘栗。递蕉与烘栗为男角色，墨墩与泡泡为女角色；外形沿用原动物设计，性别仅由细微眉眼、发结与声线区分。全片仅四灵具象登场，财神用画外音、祥云与金印表现；现代场景和街市不出现人类、手部或人形剪影。',
34:'烘栗 小熊猫 男',
35:'晾纸与传纸，兼顾工序协调。沿用旧技能：对当前高亮的一个湿纸槽按住加工键扇风，该槽总干燥速率为普通的2倍，松手或移开恢复；折扇为演出工具。',
37:'递蕉 金丝猴 男',
38:'搬运与灵活交接。沿用旧技能：向空手搭档递交距离2米，工位仍为1.2米，遵守朝向和墙体遮挡；不新增跳台、翻墙或远程投掷。',
40:'墨墩 大熊猫 女',
41:'上墨与印刷，也在剧情中核对印样和登记。沿用旧技能：自己印刷需1.4秒，普通2秒；核验是剧情与交付反馈，不新增专属核验技能或独立工位。',
43:'泡泡 水獭 女',
44:'打浆与抄纸，掌握纸浆状态。沿用旧技能：自己抄纸需1.4秒，普通2秒；打浆与搅匀纤维并入抄纸演出，不新增拖拽输入。',
47:'剧情呈现为核对委托、备料打浆、抄纸、压水晾干、印制、核验登记和送验。实际可操作流程维持抄纸槽→双槽晾纸架→印刷台→盖印台→交付窗口，另有单槽共享台。',
48:'四灵各有擅长，也都能完成全部普通工序。两位玩家开局各选一名不同钱灵，固定操控至本局结束；不按任务切换角色。每人只持一件、同时一份订单。关卡压力来自工序顺序、移动与沟通。',
49:'每个订单有固定要求与数量。核验与登记融入盖印和交付反馈；交付后的短街市表现只使用器物、纸票与声音，不出现人类。知识节点与记忆恢复作为剧情反馈规划，不把现有订单分数改为刷量灵气，也不声称新知识系统已实现。',
54:'画面与动作  早餐铺收银台、公交刷卡器、小店终端三个无人物特写。屏幕亮起“支付成功”，手机与生活器物用剪纸式转场衔接；不拍手部或人物剪影。最后一道屏幕亮光，接到书桌上自行翻开的图册。',
59:'画面与动作  第一人称镜头靠近图册中的交子图样，但不显示玩家身体。一粒暖金色光点停在纸上印纹，屏幕外的提问落下。镜头贴近纸面，穿过细小纸纤维，进入藏在纹样里的作坊。',
60:'屏幕外声音：“这么薄的一张纸，为什么能当钱？”',
83:'画面与动作  卷轴金铃响起，财神声音从云纹间传来，只见祥云和稳住纸页的金印。悬浮微光分成四道细线，连接四灵，再汇成屏幕前的方孔光印；不出现人形财神、玩家手指或手掌。',
87:'声音与转场  金铃与弦乐回应。光线连接时，四灵各做一个小动作，表达他们都是可选动物角色；正式开局由两位玩家各选一名，不表示局内四角色即时切换。',
91:'画面与动作  方孔光印触及长卷，纸面浮出“北宋·益州”。大张纸沿左下、中央卷口和右侧外弧兜起，形成宽阔通路。财神金印留在卷外压住入口，四灵登上纸面。不出现玩家伸手。',
103:'画面与动作  纸路落在作坊门前。布货、装满铁钱的木车和被压弯的车轴表达交易与重量，不出现搬运者。递蕉提起一小袋铁钱，神气的姿势逐渐被重量坠低。镜头转到风中轻薄纸样，建立对比。',
106:'声音与转场  沉沉铁钱落地声接轻轻纸响；远处叫卖用环境声音表达。画面不出现人类或其他拟人路人，四只动物始终是角色主体。',
129:'玩家点击“开始游戏”后进入首关与双人选角，两位玩家从四灵中各选不同角色。确认后进入停表教学，镜头推向抄纸槽；提示为“靠近抄纸槽，按住加工键抄纸（P1 G／P2 .）”。搅浆仅为原抄纸动作演出，不要求拖动木棒，也不强制把已选角色换成泡泡。',
130:'所选动物完成第一次抄纸，湿纸留槽待取，泡泡用画外讲解：“看，这些细纤维，已经抱成一张纸了。”纸面亮起灵光、局部颜色恢复，并规划展示“纸从哪里来”故事条目。该表现需后续制作，不改教学不计分、不解锁组合的规则。',
135:'开场让玩家记住三件事：钱灵正在褪色；亲手理解交子能帮它们恢复；两人马上可以各选一只动物协作。历史知识通过铁钱重量、印样、账册与兑换凭据出现，其他细节留在关卡中。',
138:'回到现代的无人物书桌，修复后的交子故事出现在数字图鉴上。手机提示一位朋友点开故事，长卷多亮起一点微光。四灵明白：故事继续被理解和分享，就能在今天找到新的工作方式。镜头不出现玩家、朋友或其他人类身体。',
}
updated=[]
for i,t in enumerate(texts,1):
    s=overrides.get(i,t)
    for a,b in aliases.items():s=s.replace(a,b)
    updated.append(s)
# Preserve the source table as a Markdown table instead of flattening cells.
heads={4,14,29,50,68,88,107,127,139}
shot_heads={52,57,62,69,75,81,89,95,101,108,114,120}
subheads={6,9,15,18,20,23,26,46,128,131,134,137}
out=['# '+updated[0], '', '> 本版按2026年11月20日直接要求统一：新世界观、旧版动物技能、四动物且无可见人类。原件不改写；改动依据见[统一设定](世界观角色与技能统一设定_v01_20261120.md)。本文件是剧本，尚未制作新动画。','']
for i,t in enumerate(updated,1):
    if i==1: continue
    if i==31:
        out+=['| 角色 | 职责与旧技能 | 性格和表演 |','|---|---|---|']
        for start in (34,37,40,43):out.append('| '+' | '.join(updated[start-1:start+2])+' |')
        out.append('')
    if 31<=i<=45:continue
    prefix='## ' if i in heads else '### ' if i in shot_heads or i in subheads else ''
    out += [prefix+t,'']
out+=['## 近期聊天的美术衔接','', '按最近可读聊天中的用户要求，四灵采用国风手绘墨线与简洁平涂，轮廓比例极端可爱并有体量和几何对比。纸卷边线连续，折面稍硬，近大远小、前后遮挡清楚；少量环境衬托猴子与水獭，不用跳脱背景绿或整体降饱和。烘栗开屏构图可突出，但助手提出的“掌印钱灵”不改变本日明确沿用的扇风技能。人类设定表只作画法排版参考，不纳入角色。详见[聊天附件索引](../../Art/四动物聊天参考_v01_20261120/从这里开始.md)。','']
(OUT/'开场动画剧本_四动物统一版_v01_20261120.md').write_text('\n'.join(out),encoding='utf-8')
characters=[
 dict(id='paopao',name='泡泡',species='水獭',gender='女',source_alias='沐沐',skill=dict(id='papermaking_fast',station='papermaking',duration_seconds=1.4,normal_duration_seconds=2,work_threshold=2,work_rate=2/1.4)),
 dict(id='dijiao',name='递蕉',species='金丝猴',gender='男',source_alias='金豆',skill=dict(id='partner_pass_range',partner_range_m=2,station_range_m=1.2,line_of_sight_required=True,recipient_empty_required=True)),
 dict(id='modun',name='墨墩',species='大熊猫',gender='女',source_alias='墨墨',skill=dict(id='printing_fast',station='printing',duration_seconds=1.4,normal_duration_seconds=2,work_threshold=2,work_rate=2/1.4)),
 dict(id='hongli',name='烘栗',species='小熊猫',gender='男',source_alias='阿绒',skill=dict(id='active_fanning',target='one_highlighted_wet_drying_slot',hold_work_required=True,total_drying_rate_multiplier=2,normal_drying_seconds=4,release_restores_normal_rate=True,stacks_with_natural_rate=False))
]
ids=sorted(c['id'] for c in characters)
contract={
 'schema_version':2,'version':'v01_20261120','status':'design_contract_only_not_runtime_implemented',
 'authority':'2026-11-20 用户要求新世界观、仅四动物、用旧版本技能；旧参数源自11-10设计第6节',
 'characters':characters,'active_character_ids':ids,'retired_character_ids':['zhituan','yintao'],
 'selection':{'players':2,'distinct_required':True,'in_round_switching':False,'human_player_avatar':False},
 'input':{'P1':{'move':'WASD','take_place_pass':'F','hold_work':'G'},'P2':{'move':'ArrowKeys','take_place_pass':'Slash','hold_work':'Period'},'pause':'Escape'},
 'rules':{'held_item_capacity':1,'active_orders':1,'workstations':5,'shared_table_slots':1,'drying_slots':2,'round_seconds':180,'order_quantities':[1,1,2],'points_per_sheet':10,'points_per_order':10,'star_order_thresholds':[2,4,6]},
 'combinations':{'key_rule':'sort two distinct stable IDs lexicographically and join with underscore','keys':['_'.join(pair) for pair in combinations(ids,2)],'count':6,'portrait_target_count':4,'fixed_first_pair':None,'only_formal_delivery_followed_by_settlement_unlocks':True},
 'save_migration':{'backup_before_migration':True,'human_collection_keys_to_archive':['yintao_zhituan'],'automatic_human_to_animal_mapping':False,'allowlist_active_ids_and_pair_keys':True,'runtime_migration_implemented':False},
 'skill_parameters_status':'旧效果采用，原始调试数值保留，动物联调与平衡未验收',
 'world':{'location':'财神府纸币司与钱币长卷中的北宋益州忆境','threat':'空白风','energy':'新的理解与传递，不由反复印纸无限增加','visible_characters':'only_four_animal_spirits','deity_representation':'voice_cloud_and_seal_only','historical_boss_active':False},
 'intro':{'duration_seconds':180,'shot_durations_seconds':[10,12,14,14,18,20,14,14,18,18,16,12],'human_hands_or_silhouettes':False,'runtime_gameplay_input_unchanged':True},
 'asset_status':{'new_animal_models_completed':False,'old_human_ui_active':False,'new_animal_ui_generated_this_update':False,'new_intro_rendered':False,'unity_runtime_tested':False}
}
(OUT/'当前角色与组合合同_v01_20261120.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
evidence={
 'version':'v01_20261120','source_docx':{'original':str(original),'project_copy':str(copy.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(copy.read_bytes()).hexdigest(),'bytes':copy.stat().st_size,'paragraphs_including_table_cells':len(texts),'unchanged_copy':copy.read_bytes()==original.read_bytes()},
 'shared_chat':{'url':'https://chatgpt.com/share/6b0000e2-2654-83ea-b1ca-d0ff20021b7f','status':'shared_snapshot_unreadable_same_title_account_chat_recent_turns_retrieved','observed_web':'Only generic title and share link returned','observed_browser':'Tab title 制作国画开屏图 observed; body access timed out','recovered_via':'codex_app list_threads and read_thread','account_thread_id':'6afd6707-a620-83e9-bbd0-6e7394912f45','account_thread_title':'制作国画开屏图','retrieved_turns':5,'retrieved_attachments':9,'record':'来源/制作国画开屏图_最近可读记录_20261120.json','not_claimed_full_shared_history_review':True},
 'direct_user_decisions':['世界观用新确定的','人物名字技能有出入统一','只保留四个动物角色，不要人类','用旧版本的角色技能'],
 'normalization':{'aliases':aliases,'modified_source_paragraphs':sorted(overrides),'original_docx_modified':False,'historical_assets_rewritten':False},
 'validation':{'character_count':len(ids),'combination_count':len(contract['combinations']['keys']),'intro_seconds':sum(contract['intro']['shot_durations_seconds']),'old_skills_retained':True,'unity_runtime_tested':False}
}
(OUT/'来源与核验_v01_20261120.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert len(set(contract['combinations']['keys']))==6 and sum(contract['intro']['shot_durations_seconds'])==180
assert not any(a in '\n'.join(out) for a in aliases)
print(json.dumps(evidence['validation'],ensure_ascii=False))
