# 引入 hoshino 相关库
from hoshino import Service, priv, config
from hoshino.typing import CQEvent

# 引入配置文件相关库
import rtoml
from pathlib import Path

# json
import json

# http 请求
import httpx

# 时间, 用于记录告警日志以及区分每日集会码
from datetime import datetime, timedelta

sv_help = """
怪猎集会码记录功能 详情请输入 [帮助mhw] 查阅
""".strip()

sv = Service(
    name="mhw",  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=False,  # 默认启用
    bundle="娱乐",  # 分组归类
    help_=sv_help,  # 帮助说明
)

# 获取启用了 mhw 功能的群组(暂时做不到,先写死)
GROUP_LIST = ["640596155", "433981507"]


# steam 用户信息 API
PLAYER_SUMMARY = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={}&steamids={}"

# 读取配置文件
CONFIG_PATH = Path(__file__).parent / "../steam_watcher/config.toml"
CONFIG = rtoml.load(CONFIG_PATH)
STEAM_APIKEY = CONFIG["STEAM_APIKEY"]

MH_GAME_NAME_LIST = ["Monster Hunter: World", "MONSTER HUNTER RISE"]

# 定义 json 文件路径
# 日期-集会码字典列表 json
date_code_json_path = Path(__file__).parent / "json/date_code.json"
# 订阅 UID - qq昵称 json
steamuid_qqnickname_json_path = (
    Path(__file__).parent / "json/subscribe_uid_nickname.json"
)
# 群组订阅 SteamUID 信息
group_subscribe_path = (
    Path(__file__).parent / "../steam_watcher/json/group_subscribe.json"
)
# SteamUID - 昵称信息
steam_uid_nickname_path = (
    Path(__file__).parent / "../steam_watcher/json/steam_uid_nickname.json"
)
# SteamUID - 正在玩的游戏信息
steam_uid_game_path = (
    Path(__file__).parent / "../steam_watcher/json/steam_uid_game.json"
)
# SteamUID - 正在游玩的mh游戏信息
steam_uid_mh_game_path = Path(__file__).parent / "json/steam_uid_mh_game.json"

json_path_list = [
    date_code_json_path,
    steamuid_qqnickname_json_path,
    group_subscribe_path,
    steam_uid_nickname_path,
    steam_uid_game_path,
    steam_uid_mh_game_path,
]

# 如果 json 文件不存在, 则创建
for json_path in json_path_list:
    if not json_path.exists():
        json_path.touch()
        json_path.write_text("{}")

# 读取 json 文件
# 日期-集会码字典列表 json
date_code_json = json.loads(date_code_json_path.read_text())
# 订阅 UID - qq昵称 json
steamuid_qqnickname_json = json.loads(steamuid_qqnickname_json_path.read_text())
# 群组订阅 SteamUID 信息
group_subscribe_json = json.load(open(group_subscribe_path, "r", encoding="utf-8"))
# SteamUID - 昵称信息
steam_uid_nickname_json = json.load(
    open(steam_uid_nickname_path, "r", encoding="utf-8")
)
# SteamUID - 正在玩的游戏信息
steam_uid_game_json = json.load(open(steam_uid_game_path, "r", encoding="utf-8"))
# SteamUID - 正在游玩的mh游戏信息
steam_uid_mh_game_json = json.load(open(steam_uid_mh_game_path, "r", encoding="utf-8"))


# 添加集会码
@sv.on_prefix("添加集会码")
async def add_code(bot, ev: CQEvent):
    # 获取集会码 备注
    code_note = ev.message.extract_plain_text().strip()
    # 通过空格分割集会码和备注
    code_note_list = code_note.split(" ")
    # 如果备注为空, 则为 默认集会
    if len(code_note_list) == 1:
        code, note = code_note_list[0], "默认集会"
    else:
        code, note = code_note_list[0], code_note_list[1]
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    # 获取今日集会码字典列表
    today_code_dict_list = date_code_json.get(today, [])
    print(f"今日集会码字典列表: {today_code_dict_list}")
    # 如果集会码已存在, 则返回
    for code_dict in today_code_dict_list:
        if code_dict.get("code") == code:
            await bot.send(ev, "集会码已存在")
            return
    # 获取qq昵称
    nickname = ev.sender["card"] or ev.sender["nickname"]
    print(f"昵称: {nickname}")
    # 添加集会码
    today_code_dict_list.append({"code": code, "nickname": nickname, "note": note})
    # 更新 json 文件
    date_code_json[today] = today_code_dict_list
    date_code_json_path.write_text(json.dumps(date_code_json, indent=4))
    # 返回添加结果
    await bot.send(ev, f"添加集会码: {code} 成功, 由 {nickname} 添加, 备注: {note}")


# 通过集会码修改备注
@sv.on_prefix("修改集会备注")
async def change_note(bot, ev: CQEvent):
    print("正在尝试修改集会备注")
    # 获取集会码 备注
    code_note = ev.message.extract_plain_text().strip()
    # 通过空格分割集会码和备注
    code_note_list = code_note.split(" ")
    # 如果备注为空, 则为 默认集会
    if len(code_note_list) == 1:
        code, note = code_note_list[0], "默认集会"
    else:
        code, note = code_note_list[0], code_note_list[1]
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    # 获取今日集会码字典列表
    today_code_dict_list = date_code_json.get(today, [])
    # 如果集会码不存在, 则返回
    for code_dict in today_code_dict_list:
        if code_dict.get("code") == code:
            # 修改备注
            code_dict["note"] = note
            # 更新 json 文件
            date_code_json[today] = today_code_dict_list
            date_code_json_path.write_text(json.dumps(date_code_json, indent=4))
            # 返回修改结果
            await bot.send(ev, f"修改备注: {code} 成功, 备注: {note}")
            return
    # 返回修改结果
    await bot.send(ev, f"修改备注: {code} 失败, 集会码不存在")


# 今日集会码
@sv.on_fullmatch("今日集会码")
async def today_code(bot, ev: CQEvent):
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    # 获取今日集会码字典列表
    today_code_dict_list = date_code_json.get(today, [])
    # 如果今日集会码字典列表为空, 则返回
    if not today_code_dict_list:
        await bot.send(ev, "今日集会码为空")
        return
    # 返回今日集会码
    msg = "今日集会码:\n"
    for code_dict in today_code_dict_list:
        msg += f"{code_dict.get('note')}: {code_dict.get('code')}, 由 {code_dict.get('nickname')} 添加\n"
    msg += "集会码群聊间共通,若要区分请添加或修改备注"
    await bot.send(ev, msg)


# 删除集会码
@sv.on_prefix("删除集会码")
async def delete_code(bot, ev: CQEvent):
    # 获取集会码
    code = ev.message.extract_plain_text().strip()
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    # 获取今日集会码字典列表
    today_code_dict_list = date_code_json.get(today, [])
    # 如果集会码不存在, 则返回
    for code_dict in today_code_dict_list:
        if code_dict.get("code") == code:
            # 删除集会码
            today_code_dict_list.remove(code_dict)
            # 更新 json 文件
            date_code_json[today] = today_code_dict_list
            date_code_json_path.write_text(json.dumps(date_code_json, indent=4))
            # 返回删除结果
            await bot.send(ev, f"删除集会码: {code} 成功")
            return
    # 返回删除结果
    await bot.send(ev, f"删除集会码: {code} 失败, 集会码不存在")


# 删除我添加的集会码
@sv.on_fullmatch("删除我添加的集会码")
async def delete_my_code(bot, ev: CQEvent):
    # 获取qq昵称
    nickname = ev.sender["card"] or ev.sender["nickname"]
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    # 获取今日集会码字典列表
    today_code_dict_list = date_code_json.get(today, [])
    # 如果今日集会码字典列表为空, 则返回
    if not today_code_dict_list:
        await bot.send(ev, "今日集会码为空")
        return
    my_code_dict_list = ""
    # 删除我添加的集会码
    for code_dict in today_code_dict_list:
        if code_dict.get("nickname") == nickname:
            my_code_dict_list += f"{code_dict.get('code')}"
            # 删除集会码
            today_code_dict_list.remove(code_dict)
    # 更新 json 文件
    date_code_json[today] = today_code_dict_list
    date_code_json_path.write_text(json.dumps(date_code_json, indent=4))
    # 返回删除结果
    await bot.send(ev, f"删除{nickname}添加的集会码{my_code_dict_list}成功")


# 昨日集会码
@sv.on_fullmatch("昨日集会码")
async def yesterday_code(bot, ev: CQEvent):
    # 获取昨日日期
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    # 获取昨日集会码字典列表
    yesterday_code_dict_list = date_code_json.get(yesterday, [])
    # 如果昨日集会码字典列表为空, 则返回
    if not yesterday_code_dict_list:
        await bot.send(ev, "昨日集会码为空")
        return
    # 返回昨日集会码
    msg = "昨日集会码:\n"
    for code_dict in yesterday_code_dict_list:
        msg += f"{code_dict.get('note')}: {code_dict.get('code')}, 由 {code_dict.get('nickname')} 添加\n"
    msg += "集会码群聊间共通,若要区分请添加或修改备注"
    await bot.send(ev, msg)


# 定时任务, 每日 5 时删除前天的集会码
@sv.scheduled_job("cron", hour=5)
async def delete_code():
    # 获取前天日期
    before_yesterday = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    # 删除前天的集会码(如果存在)
    if before_yesterday in date_code_json:
        del date_code_json[before_yesterday]
    # 更新 json 文件
    date_code_json_path.write_text(json.dumps(date_code_json, indent=4))
    print(f"删除前天集会码: {before_yesterday}")


# 添加mh订阅 steamUID
@sv.on_prefix("添加mh订阅")
async def add_mh_subscribe(bot, ev: CQEvent):
    await bot.send(ev, "steam订阅功能维护中......")
    # # 获取订阅 UID
    # steam_uid = ev.message.extract_plain_text().strip()
    # # 获取群昵称
    # qqnickname = ev.sender["card"] or ev.sender["nickname"]
    # # 如果 steam_uid 不在steam_uid_game_json 中, 则说明当前不在订阅该用户 steam 状态， 此时其也必定不在 steam_uid_qqnickname_json 中
    # if steam_uid not in steam_uid_game_json:
    #     response = httpx.get(PLAYER_SUMMARY.format(STEAM_APIKEY, steam_uid)).json()
    #     # 获取 steam 昵称
    #     steam_nickname = response["response"]["players"][0]["personaname"]
    #     # 如果 steam_uid 也不在 steam_uid_nickname_json 中, 则说明从未订阅过该用户 steam 状态, 需要更新一下 steam_uid_nickname_json
    #     if steam_uid not in steam_uid_nickname_json:
    #         # 将 steam 昵称添加到 steam_uid_nickname_json 映射中
    #         steam_uid_nickname_json[steam_uid] = steam_nickname
    #         # 更新 json 文件
    #         steam_uid_nickname_path.write_text(
    #             json.dumps(steam_uid_nickname_json, indent=4)
    #         )
    #     # 将 steam_uid 和 qqnickname 添加到 steamuid_qqnickname_json 映射中
    #     steamuid_qqnickname_json[steam_uid] = qqnickname
    #     # 获取该用户正在玩的游戏的名称(如果没有在玩游戏则为 "没在玩游戏", 然后将其添加到 steam_uid_game_json 映射中)
    #     if "gameid" in response["response"]["players"][0]:
    #         steam_game = response["response"]["players"][0]["gameextrainfo"]
    #         # 如果 steam_game 不在 MH_GAME_NAME_LIST 中, 则说明该用户不在玩 MH, 则 MH_game 状态为 None
    #         if steam_game not in MH_GAME_NAME_LIST:
    #             mh_game = None
    #         else:
    #             mh_game = steam_game
    #             await bot.send(ev, f"{steam_nickname}, 正在玩: {steam_game}")
    #     else:
    #         steam_game = None
    #         mh_game = None
    #     steam_uid_game_json[steam_uid] = steam_game
    #     steam_uid_mh_game_json[steam_uid] = mh_game
    #     # 更新 json 文件
    #     steamuid_qqnickname_json_path.write_text(
    #         json.dumps(steamuid_qqnickname_json, indent=4)
    #     )
    #     steam_uid_game_path.write_text(json.dumps(steam_uid_game_json, indent=4))
    #     steam_uid_mh_game_path.write_text(json.dumps(steam_uid_mh_game_json, indent=4))
    #     await bot.send(ev, f"> {qqnickname} \n 怪猎动态订阅成功, steam 昵称为 {steam_nickname}")
    # # 如果 steam_uid 在 steam_uid_game_json 中, 但是不在 steamuid_qqnickname_json 中, 则说明当前订阅了该用户的steam状态但是没有订阅怪猎状态
    # elif steam_uid not in steamuid_qqnickname_json:
    #     steamuid_qqnickname_json[steam_uid] = qqnickname
    #     steamuid_qqnickname_json_path.write_text(
    #         json.dumps(steamuid_qqnickname_json, indent=4)
    #     )
    #     steam_uid_mh_game_json[steam_uid] = steam_uid_game_json[steam_uid]
    #     steam_uid_mh_game_path.write_text(json.dumps(steam_uid_mh_game_json, indent=4))
    #     await bot.send(
    #         ev,
    #         f"> {qqnickname} \n steam动态已订阅, 添加怪猎动态订阅成功, steam 昵称为 {steam_uid_nickname_json[steam_uid]})",
    #     )
    #     return
    # elif qqnickname == steamuid_qqnickname_json[steam_uid]:
    #     await bot.send(ev, f"已经订阅过该群友, steam 昵称为 {steam_uid_nickname_json[steam_uid]}")
    # else:
    #     steamuid_qqnickname_json[steam_uid] = qqnickname
    #     steamuid_qqnickname_json_path.write_text(
    #         json.dumps(steamuid_qqnickname_json, indent=4)
    #     )
    #     await bot.send(
    #         ev,
    #         f"> {qqnickname} \n 修改订阅群名片成功, 已更正为 {steamuid_qqnickname_json[steam_uid]})",
    #     )

    # return


# 删除mh订阅 steamUID
@sv.on_prefix("删除mh订阅")
async def delete_mh_subscribe(bot, ev: CQEvent):
    # # 获取订阅 UID
    # steam_uid = ev.message.extract_plain_text().strip()
    # # 获取群昵称
    # nickname = ev.sender["card"] or ev.sender["nickname"]
    # # 如果没有订阅过该 UID, 则返回
    # if steam_uid not in steamuid_qqnickname_json:
    #     await bot.send(ev, "没有订阅过该群友怪猎动态")
    # else:
    #     del steamuid_qqnickname_json[steam_uid]
    #     steamuid_qqnickname_json_path.write_text(
    #         json.dumps(steamuid_qqnickname_json, indent=4)
    #     )
    #     # 同时取消掉 steam_uid_game_json 中的订阅
    #     del steam_uid_game_json[steam_uid]
    #     steam_uid_game_path.write_text(json.dumps(steam_uid_game_json, indent=4))
    #     # 同时取消掉 steam_uid_mh_game_json 中的订阅
    #     del steam_uid_mh_game_json[steam_uid]
    #     steam_uid_mh_game_path.write_text(json.dumps(steam_uid_mh_game_json, indent=4))
    #     await bot.send(ev, f"> {nickname} \n 怪猎动态取消订阅成功")
    # return
    await bot.send(ev, "steam订阅功能维护中......")



# Monster Hunter: World
# MONSTER HUNTER RISE


# 没半分钟执行一次查询, 查询 steam_uid_game_json 中的用户游戏状态
# @sv.scheduled_job("cron", second="*/30")
# async def mh_subscribe():
#     print("开始查询怪猎动态")
#     # 重新读取 steam_uid_game_json
#     steam_uid_game_json = json.loads(steam_uid_game_path.read_text())
#     # 比较 steam_uid_game_json 和 steam_uid_mh_game_json 中的用户游戏状态
#     for steam_uid in steam_uid_mh_game_json:
#         # 获取群昵称
#         qqnickname = steamuid_qqnickname_json[steam_uid]
#         # 获取 steam 昵称
#         steam_nickname = steam_uid_nickname_json[steam_uid]
#         if steam_uid_mh_game_json[steam_uid] == steam_uid_game_json[steam_uid]:
#             continue
#         # 如果 steam_uid_mh_game_json 中的用户游戏状态为 None
#         if steam_uid_mh_game_json[steam_uid] is None:
#             # 如果 steam_uid_game_json 中的用户游戏状态在 MH_GAME_NAME_LIST 中
#             if steam_uid_game_json[steam_uid] in MH_GAME_NAME_LIST:
#                 # 更新 steam_uid_mh_game_json 中的用户游戏状态
#                 steam_uid_mh_game_json[steam_uid] = steam_uid_game_json[steam_uid]
#                 # 推送 qqnickname - steam nickname 正在玩 steam_uid_game_json[steam_uid]
#                 msg = f"{qqnickname}-{steam_nickname}, 正在玩: {steam_uid_game_json[steam_uid]}"
#                 for gid in GROUP_LIST:
#                     await sv.bot.send_group_msg(group_id=int(gid), message=msg)
#         elif steam_uid_game_json[steam_uid] in MH_GAME_NAME_LIST:
#             # 推送 qqnickname - steam nickname 正在玩 steam_uid_game_json[steam_uid]
#             msg = f"{qqnickname}-{steam_nickname}, 不玩 {steam_uid_mh_game_json[steam_uid]} 了, 目前正在玩: {steam_uid_game_json[steam_uid]}"
#             for gid in GROUP_LIST:
#                 await sv.bot.send_group_msg(group_id=int(gid), message=msg)
#             # 更新 steam_uid_mh_game_json 中的用户游戏状态
#             steam_uid_mh_game_json[steam_uid] = steam_uid_game_json[steam_uid]
#         else:
#             # 推送 qqnickname - steam nickname 不在玩怪猎
#             msg = f"{qqnickname}-{steam_nickname}, 不玩 {steam_uid_mh_game_json[steam_uid]} 了"
#             for gid in GROUP_LIST:
#                 await sv.bot.send_group_msg(group_id=int(gid), message=msg)
#             # 更新 steam_uid_mh_game_json 中的用户游戏状态
#             steam_uid_mh_game_json[steam_uid] = None
#     # 更新 steam_uid_mh_game_json
#     steam_uid_mh_game_path.write_text(json.dumps(steam_uid_mh_game_json, indent=4))
#     print("怪猎动态查询结束")


# 谁在打猎?
@sv.on_fullmatch("谁在打猎")
async def who_is_playing_mh(bot, ev: CQEvent):
    # # 读取 steam_uid_mh_game_json
    # steam_uid_mh_game_json = json.loads(steam_uid_mh_game_path.read_text())
    # # 匹配非 null 的 UID
    # playing_mh_uid_list = [
    #     steam_uid
    #     for steam_uid in steam_uid_mh_game_json
    #     if steam_uid_mh_game_json[steam_uid] is not None
    # ]
    # # 如果没有人在打猎
    # if not playing_mh_uid_list:
    #     await bot.send(ev, "当前没有群友在打猎")
    #     return
    # # 如果有人在打猎
    # msg = "====Monster Hunter====\n"
    # for steam_uid in playing_mh_uid_list:
    #     # 获取群昵称
    #     qqnickname = steamuid_qqnickname_json[steam_uid]
    #     # 获取 steam 昵称
    #     steam_nickname = steam_uid_nickname_json[steam_uid]
    #     # 获取游戏名称
    #     game_name = steam_uid_mh_game_json[steam_uid]
    #     msg += f"{qqnickname}-{steam_nickname} 正在玩 {game_name}\n"
    # await bot.send(ev, msg)
    await bot.send(ev, "steam订阅功能维护中......")


# mh订阅列表
@sv.on_rex(r"^mh订阅列表$")
async def mh_subscribe_list(bot, ev: CQEvent):
    # # 读取 steam_uid_mh_game_json
    # steam_uid_mh_game_json = json.loads(steam_uid_mh_game_path.read_text())
    # msg = "====Monster Hunter====\n"
    # for steam_uid in steam_uid_mh_game_json:
    #     # 获取群昵称
    #     qqnickname = steamuid_qqnickname_json[steam_uid]
    #     # 获取 steam 昵称
    #     steam_nickname = steam_uid_nickname_json[steam_uid]
    #     # 获取游戏名称
    #     game_name = steam_uid_mh_game_json[steam_uid]
    #     if game_name is None:
    #         msg += f"{qqnickname}-{steam_nickname} 当前不在打猎\n"
    #     else:
    #         msg += f"{qqnickname}-{steam_nickname} 正在玩 {game_name}\n"
    # await bot.send(ev, msg)
    await bot.send(ev, "steam订阅功能维护中......")



# 帮助mh订阅
@sv.on_fullmatch("怎么订阅mh")
async def mh_subscribe_help(bot, ev: CQEvent):
#     await bot.send(
#         ev,
#         '请在群内发送 "添加mh订阅 UID" 以添加订阅 \n\
# 例如: "添加mh订阅 76561198846049157" \n\
# 此处的UID为steam的UID, 在网页上登录Steam, 点击右上角的头像, 在网址栏中可以看到你的 Steam UID \n\
# 也即是 "https://steamcommunity.com/profiles/76561198846049157" 中的 "76561198846049157" \n\
# 有些用户的 Steam UID 为 "https://steamcommunity.com/id/xxx" 的形式, \n\
# 此时可以点击右上角头像旁边的昵称下拉菜单 -> 账户明细 \n\
# 然后就可以在 XXX 的账户字样下看到你的 Steam UID 了\n\
# 手机端steam同样可以在账户明细页面查看到steam UID\n\
# 不管是电脑端还是手机端都可以用UU免费加速\n\
# 其他说明请发送 "帮助mhw" 来获取帮助',
#     )
    await bot.send(ev, "steam订阅功能维护中......")



# mhw 帮助
@sv.on_fullmatch("帮助mhw")
async def mhw_help(bot, ev: CQEvent):
    msg = "可使用的命令(请注意空格)(中括号表示其中的内容为可选项, 不输入的话将按照默认内容录入):\n" + "添加集会码 集会码 [备注]\n"
    msg += "今日集会码\n"
    msg += "删除集会码 集会码\n"
    msg += "删除我添加的集会码\n"
    msg += "昨日集会码\n"
    msg += "修改集会备注 集会码 备注\n"
    # msg += "添加mh订阅 steamUID\n"
    # msg += "删除mh订阅 steamUID\n"
    # msg += "怎么订阅mh\n"
    # msg += "mh订阅列表\n"
    # msg += "谁在打猎\n"
    # msg += "mh订阅(怪猎[世界,崛起]在线状态)会同步订阅者的qq群名片, 因此最好亲自订阅, 否则会串群名片, 或者在其他群友帮忙订阅后再自己重复订阅一遍以更新群名片\n"
    await bot.send(ev, msg)
