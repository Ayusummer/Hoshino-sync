# import itertools
# from hoshino import util, R
# from hoshino.typing import CQEvent
# from . import sv
#
# p1 = R.img('priconne/quick/r16-5-tw-0.png').cqcode
# p2 = R.img('priconne/quick/r16-5-tw-1.png').cqcode
# p4 = R.img('priconne/quick/r17-5-jp-1.png').cqcode
# p5 = R.img('priconne/quick/r17-5-jp-2.png').cqcode
# p6 = R.img('priconne/quick/r17-5-jp-3.png').cqcode
# p7 = R.img('priconne/quick/r9-5-cn.png').cqcode
#
#
# @sv.on_rex(r'^(\*?([日台国陆b])服?([前中后]*)卫?)?rank(表|推荐|指南)?$')
# async def rank_sheet(bot, ev):
#     match = ev['match']
#     is_jp = match.group(2) == '日'
#     is_tw = match.group(2) == '台'
#     is_cn = match.group(2) and match.group(2) in '国陆b'
#     if not is_jp and not is_tw and not is_cn:
#         await bot.send(ev, '\n请问您要查询哪个服务器的rank表？\n*日rank表\n*台rank表\n*陆rank表', at_sender=True)
#         return
#     msg = [
#         '\n※表格仅供参考，升r有风险，强化需谨慎\n※一切以会长要求为准——',
#     ]
#     if is_jp:
#         msg.append('※不定期搬运自图中Q群\n※广告为原作者推广，与本bot无关\nR17-5 rank表：')
#         pos = match.group(3)
#         if not pos or '前' in pos:
#             msg.append(str(p4))
#         if not pos or '中' in pos:
#             msg.append(str(p5))
#         if not pos or '后' in pos:
#             msg.append(str(p6))
#         await bot.send(ev, '\n'.join(msg), at_sender=True)
#         await util.silence(ev, 60)
#     elif is_tw:
#         msg.append(f'※不定期搬运自漪夢奈特\n※油管频道有介绍视频及原文档\nR16-5 rank表：\n{p1} {p2}')
#         await bot.send(ev, '\n'.join(msg), at_sender=True)
#         await util.silence(ev, 60)
#     elif is_cn:
#         await bot.send(ev, '\n※参照图如下：', at_sender=True)
#         # await bot.send(ev, str(p7))
#         # await util.silence(ev, 60)
#
#
# @sv.on_fullmatch(('jjc', 'JJC', 'JJC作业', 'JJC作业网', 'JJC数据库', 'jjc作业', 'jjc作业网', 'jjc数据库'))
# async def say_arina_database(bot, ev):
#     await bot.send(ev, '公主连接Re:Dive 竞技场编成数据库\n日文：https://nomae.net/arenadb \n中文：https://pcrdfans.com/battle')
#
#
# OTHER_KEYWORDS = '【日rank】【台rank】【b服rank】【jjc作业网】【黄骑充电表】【一个顶俩】'
# PCR_SITES = f'''
# 【繁中wiki/兰德索尔图书馆】pcredivewiki.tw
# 【日文wiki/GameWith】gamewith.jp/pricone-re
# 【日文wiki/AppMedia】appmedia.jp/priconne-redive
# 【竞技场作业库(中文)】pcrdfans.com/battle
# 【竞技场作业库(日文)】nomae.net/arenadb
# 【论坛/NGA社区】bbs.nga.cn/thread.php?fid=-10308342
# 【iOS实用工具/初音笔记】bbs.nga.cn/read.php?tid=14878762
# 【安卓实用工具/静流笔记】bbs.nga.cn/read.php?tid=20499613
# 【台服卡池千里眼】bbs.nga.cn/read.php?tid=16986067
# 【日官网】priconne-redive.jp
# 【台官网】www.princessconnect.so-net.tw
#
# ===其他查询关键词===
# {OTHER_KEYWORDS}
# ※B服速查请输入【bcr速查】'''
#
# BCR_SITES = f'''
# 【PJJC防守阵容搭配思路】https://bbs.nga.cn/read.php?tid=22372410
# 【公会战排名网页端查询】https://kengxxiao.github.io/Kyouka/
# 【2020/6月Rank9-3推荐表】https://bbs.nga.cn/read.php?tid=22247310
# 【赫斯海德计轴器】https://bbs.nga.cn/read.php?tid=22236351
# 【角色动作帧数表】https://bbs.nga.cn/read.php?tid=21952354&_fp=2
# 【黄骑充电详解】https://bbs.nga.cn/read.php?tid=21913703&_fp=2
# 【仓鼠玩家pjjc登顶教程】https://bbs.nga.cn/read.php?tid=21850496&_fp=2
# 【如何写轴和打轴】https://bbs.nga.cn/read.php?tid=22461768
# 【5星小仓唯拆各种25星藏猫】https://bbs.nga.cn/read.php?tid=22109632&_fp=2
#
# ===其他查询关键词===
# {OTHER_KEYWORDS}
# ※日台服速查请输入【pcr速查】
# ※开服版本速查请输入【bcr萌新攻略】
# ※半月刊活动流程请输入【bcr半月刊】
# ※席巴鸽的rank推荐图请输入【rank_xbg】【rankData_xbg】
# ※酷乐pusi的伊莉亚拆与被拆手册请输入【guidance_yly】【guidance_counterattack_yly】
# '''
#
#
# @sv.on_fullmatch(('pcr速查', 'pcr图书馆', '图书馆'))
# async def pcr_sites(bot, ev: CQEvent):
#     await bot.send(ev, PCR_SITES, at_sender=True)
#     await util.silence(ev, 60)
#
#
# @sv.on_fullmatch(('bcr速查', 'bcr攻略'))
# async def bcr_sites(bot, ev: CQEvent):
#     await bot.send(ev, BCR_SITES, at_sender=True)
#     await util.silence(ev, 60)
#
#
# YUKARI_SHEET_ALIAS = map(lambda x: ''.join(x), itertools.product(('黄骑', '酒鬼'), ('充电', '充电表', '充能', '充能表')))
# YUKARI_SHEET = f'''
# {R.img('priconne/quick/黄骑充电.jpg').cqcode}
# ※大圈是1动充电对象 PvP测试
# ※黄骑四号位例外较多
# ※对面羊驼或中后卫坦 有可能歪
# ※我方羊驼算一号位
# ※图片搬运自漪夢奈特'''
#
#
# @sv.on_fullmatch(YUKARI_SHEET_ALIAS)
# async def yukari_sheet(bot, ev):
#     await bot.send(ev, YUKARI_SHEET, at_sender=True)
#     await util.silence(ev, 60)
#
#
# DRAGON_TOOL = f'''
# 拼音对照表：{R.img('priconne/KyaruMiniGame/注音文字.jpg').cqcode}{R.img('priconne/KyaruMiniGame/接龙.jpg').cqcode}
# 龍的探索者們小遊戲單字表 https://hanshino.nctu.me/online/KyaruMiniGame
# 镜像 https://hoshino.monster/KyaruMiniGame
# 网站内有全词条和搜索，或需科学上网'''
#
#
# @sv.on_fullmatch(('一个顶俩', '拼音接龙', '韵母接龙'))
# async def dragon(bot, ev):
#     await bot.send(ev, DRAGON_TOOL, at_sender=True)
#     await util.silence(ev, 60)
