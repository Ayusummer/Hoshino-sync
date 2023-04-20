# Steam Web API简易使用介绍: https://blog.imzy.ink/steamapi/
# Steam API KEY: https://steamcommunity.com/dev/apikey
# Steam Web API: https://developer.valvesoftware.com/wiki/Steam_Web_API
# 每分钟刷新一次, 不建议订阅太多用户, 目前暂定订阅人数超过 100 时不再支持继续订阅并向管理员发送警告
# 目前不太清楚 Steam Web API 的调用频率限制, 根据 https://partner.steamgames.com/doc/webapi_overview?l=schinese 中所述, 如果返回 403 则说明触发了频率限制

# 引入配置文件相关库
import rtoml
from pathlib import Path
# json
import json

# 引入 hoshino 相关库
from hoshino import Service, priv, config
from hoshino.typing import CQEvent
# 正则
import re


# 网络请求库 httpx
import httpx
# 时间, 用于记录警告日志
from datetime import datetime

# 用于发图
import base64


sv_help = """
监视群友steam游戏状态 详情请输入 [steam订阅说明] 或 [帮助steam_watcher] 查阅
""".strip()

sv = Service(
    name="steam_watcher",  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=False,  # 默认启用
    bundle="娱乐",  # 分组归类
    help_=sv_help,  # 帮助说明
)


# 读取配置文件
CONFIG_PATH = Path(__file__).parent / "config.toml"
CONFIG = rtoml.load(CONFIG_PATH)
STEAM_APIKEY = CONFIG["STEAM_APIKEY"]

ADMIN_QQID = config.SUPERUSERS[0]
print(ADMIN_QQID)


# 定义 json 文件路径
# 群组订阅 SteamUID 信息
group_subscribe_path = Path(__file__).parent / "json/group_subscribe.json"
# SteamUID - 昵称信息
steam_uid_nickname_path = Path(__file__).parent / "json/steam_uid_nickname.json"
# SteamUID - 正在玩的游戏信息
steam_uid_game_path = Path(__file__).parent / "json/steam_uid_game.json"


jsons_path_list = [group_subscribe_path, steam_uid_nickname_path, steam_uid_game_path]

# 如果文件不存在则创建
for path in jsons_path_list:
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            f.write("{}")

# 读取 json 文件
# 群组订阅 SteamUID 信息
group_subscribe_json = json.load(open(group_subscribe_path, "r", encoding="utf-8"))
# SteamUID - 昵称信息
steam_uid_nickname_json = json.load(open(steam_uid_nickname_path, "r", encoding="utf-8"))
# SteamUID - 正在玩的游戏信息
steam_uid_game_json = json.load(open(steam_uid_game_path, "r", encoding="utf-8"))

# 告警日志文件路径
warning_log_path = Path(__file__).parent / "warning_log.txt"
# 如果文件不存在则创建
if not warning_log_path.exists():
    with open(warning_log_path, "w", encoding="utf-8") as f:
        f.write("")


# steam 用户信息 API
PLAYER_SUMMARY = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={}&steamids={}"


# 通过 UID 获取该用户正在玩的游戏的名称(如果没有在玩游戏则返回 None)
async def get_game_name(id):
    # 尝试访问 steam API
    try:
        response = httpx.get(PLAYER_SUMMARY.format(STEAM_APIKEY, id))
        response_json = response.json()
    # 如果超时则记录日志并返回 None
    except httpx.TimeoutException:
        with open(warning_log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} 超时警告: steam API 超时\n")
        return None
    # 如果响应码为 403 则可能是触发了频率限制, 记录日志并返回 None
    if response.status_code == 403:
        with open(warning_log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} 警告: steam API 频率限制\n")
        return None
    # 如果 gameid 存在, 则说明有人在玩游戏
    if "gameid" in response_json["response"]["players"][0]:
        return response_json["response"]["players"][0]["gameextrainfo"]
    else:
        return None


# 每 1min 执行一次轮询, 更新 SteamUID - 正在玩的游戏信息 steam_uid_game_json 中的数据, 如果有变化则发送消息
# @sv.scheduled_job("cron", minute="*/1")
@sv.scheduled_job("cron", second="*/30")
async def steam_watch():
    print("正在更新 SteamUID - 正在玩的游戏信息")
    # 如果 steam_uid_game_json 中的项数大于 100, 则可能会触发风控, 保险起见每次轮询
    # 遍历 steam_uid_game_json 中的 steam_uid 与 game_name
    for steam_uid, game_name in steam_uid_game_json.items():
        # 获取该 steam_uid 的昵称
        steam_nickname = steam_uid_nickname_json[steam_uid]
        # 访问 steam API 获取该 steam_uid 正在玩的游戏名称
        game_name_now = await get_game_name(steam_uid)
        # 如果正在玩的游戏名称与之前不同, 则更新 steam_uid_game_json 中的数据, 并发送消息
        if game_name != game_name_now:
            # 如果当前没有在玩游戏, 则发送 steam_nikename 不玩 game_name 了
            if game_name_now is None:
                # 如果 game_name 为 None, 则不发送消息
                if game_name is None:
                    message = None
                # 如果 game_name 不为 None, 则发送 steam_nickname 不玩 game_name 了
                else:
                    print(f"当前 game_name 为 {game_name}, game_name_now 为 {game_name_now}")
                    message = f"{steam_nickname} 不玩 {game_name} 了"
            # 如果当前在玩游戏, 
            else:
                # 如果 game_name 为 None, 则发送 steam_nickname 现在在玩 game_name_now
                if game_name is None:
                    message = f"{steam_nickname} 正在玩 {game_name_now}"
                # 如果 game_name 不为 None, 则发送 steam_nickname 不玩 game_name 了, 现在在玩 game_name_now
                else:
                    message = f"{steam_nickname} 不玩 {game_name} 了, 现在在玩 {game_name_now}"
            # 遍历 group_subscribe_json 中的 group_id 与 steam_uid_list, 如果 steam_uid 在 steam_uid_list 中, 则发送消息
            for group_id, steam_uid_list in group_subscribe_json.items():
                if steam_uid in steam_uid_list:
                    # 如果 message 为 None, 则不发送消息
                    if message is not None:
                        await sv.bot.send_group_msg(group_id=int(group_id), message=message)
            # 更新 steam_uid_game_json 中的数据
            steam_uid_game_json[steam_uid] = game_name_now
            # 保存 steam_uid_game_json
            json.dump(steam_uid_game_json, open(steam_uid_game_path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    print("更新完成")



@sv.on_rex((r'(怎么|如何)(绑定steam|添加steam订阅|订阅steam)'))
async def bind_steam(bot, ev: CQEvent):
    # await bot.send(ev, '请在群内发送 "steam 绑定"')
    await bot.send(ev, '请在群内发送 "添加steam订阅 UID" 以添加订阅 \n\
例如: "添加steam订阅 76561198846049157" \n\
在网页上登录Steam, 点击右上角的头像, 在网址栏中可以看到你的 Steam UID \n\
也即是 "https://steamcommunity.com/profiles/76561198846049157" 中的 "76561198846049157" \n\
有些用户的 Steam UID 为 "https://steamcommunity.com/id/xxx" 的形式, \n\
此时可以点击右上角头像旁边的昵称下拉菜单 -> 账户明细 \n\
然后就可以在 XXX 的账户字样下看到你的 Steam UID 了\n\
手机端steam同样可以在账户明细页面查看到steam UID\n\
不管是电脑端还是手机端都可以用UU免费酵素\n\
其他说明请发送 "steam订阅说明" 来获取帮助')

# steam订阅说明
@sv.on_rex((r'(steam订阅说明|帮助steam_watcher)'))
async def steam_subscribe_help(bot, ev: CQEvent):
    await bot.send(ev, "订阅Steam状态 --- [添加steam订阅 UID] ---详情请发送 [怎么绑定steam] 获取帮助 \n\
删除订阅 --- [删除steam订阅 UID] \n\
查看当前群内steam订阅情况 --- [steam订阅列表] \n\
谁在玩游戏? --- [谁在玩游戏]")                   
                   


# 添加steam订阅 UID
@sv.on_prefix("添加steam订阅")
async def add_steam(bot, ev: CQEvent):
    # 如果当前订阅人数大于 100, 则可能会触发风控, 保险起见不让添加订阅, 发送提示消息并向管理员发送警告
    if len(steam_uid_game_json) > 100:
        await bot.send(ev, "当前订阅人数过多, 请稍后再试")
        await bot.send_private_msg(user_id=ADMIN_QQID, message=f"steam订阅人数过多, 请排查问题")
        return
    # 获取订阅 UID
    steam_uid = ev.message.extract_plain_text()
    # 获取群号
    group_id = ev.group_id
    # 如果群号不在 group_subscribe 中, 则添加群号json, 其中为一个空列表
    if str(group_id) not in group_subscribe_json:
        group_subscribe_json[str(group_id)] = []
    # 如果群号在 group_subscribe 中, 则判断是否已经订阅过该 UID(group_subscribe[str(group_id)]为 json, 存储了该群订阅的 UID 列表)
    else:
        if steam_uid in group_subscribe_json[str(group_id)]:
            # 获取昵称
            steam_nickname = steam_uid_nickname_json[steam_uid]
            await bot.send(ev, f"本群已经订阅过该用户, 昵称为 {steam_nickname}")
            return
    # 如果群号在 group_subscribe 中, 且没有订阅过该 UID, 则添加到 group_subscribe_json 中
    response = httpx.get(PLAYER_SUMMARY.format(STEAM_APIKEY, steam_uid)).json()
    # 获取昵称, 将其添加到 steam_uid_nickname_json 映射中
    steam_nickname = response["response"]["players"][0]["personaname"]
    steam_uid_nickname_json[steam_uid] = steam_nickname
    # 将 steamUID 添加到 group_subscribe 群组订阅中
    group_subscribe_json[str(group_id)].append(steam_uid)
    # 获取该用户正在玩的游戏的名称(如果没有在玩游戏则为 "没在玩游戏", 然后将其添加到 steam_uid_game_json 映射中)
    if "gameid" in response["response"]["players"][0]:
        steam_game = response["response"]["players"][0]["gameextrainfo"]
        await bot.send(ev, f"{steam_nickname}, 正在玩: {steam_game}")
    else:
        steam_game = None
    steam_uid_game_json[steam_uid] = steam_game

    # 保存到 json 文件
    with open(group_subscribe_path, "w", encoding="utf-8") as f:
        json.dump(group_subscribe_json, f, ensure_ascii=False, indent=4)
    with open(steam_uid_nickname_path, "w", encoding="utf-8") as f:
        json.dump(steam_uid_nickname_json, f, ensure_ascii=False, indent=4)
    with open(steam_uid_game_path, "w", encoding="utf-8") as f:
        json.dump(steam_uid_game_json, f, ensure_ascii=False, indent=4)
    await bot.send(ev, f"添加成功, 订阅 UID: {steam_uid}, 昵称: {steam_nickname}")



# 删除steam订阅 UID
@sv.on_prefix("删除steam订阅")
async def delete_steam(bot, ev: CQEvent):
    # 获取订阅 UID
    steam_uid = ev.message.extract_plain_text()
    # 获取群号
    group_id = ev.group_id
    # 如果群号不在 group_subscribe 中, 则添加群号json, 其中为一个空列表
    if str(group_id) not in group_subscribe_json:
        await bot.send(ev, "本群没有订阅该用户")
        return
    # 如果群号在 group_subscribe 中, 则判断是否已经订阅过该 UID(group_subscribe[str(group_id)]为 json, 存储了该群订阅的 UID 列表)
    else:
        # 如果没有订阅过该 UID, 则返回
        if steam_uid not in group_subscribe_json[str(group_id)]:
            await bot.send(ev, "本群没有订阅该用户")
            return
    # 如果群号在 group_subscribe 中, 且订阅过该 UID, 则从 group_subscribe_json 中删除
    group_subscribe_json[str(group_id)].remove(steam_uid)
    # 如果没有其他群订阅该 UID, 则删除 steamUID - 正在玩的游戏 的映射
    for group in group_subscribe_json:
        if steam_uid in group_subscribe_json[group]:
            break
    else:
        del steam_uid_game_json[steam_uid]

    # 保存到 json 文件
    with open(group_subscribe_path, "w", encoding="utf-8") as f:
        json.dump(group_subscribe_json, f, ensure_ascii=False, indent=4)
    with open(steam_uid_game_path, "w", encoding="utf-8") as f:
        json.dump(steam_uid_game_json, f, ensure_ascii=False, indent=4)
    await bot.send(ev, f"删除成功, UID: {steam_uid}, 昵称: {steam_uid_nickname_json[steam_uid]}")



# 查看steam订阅列表
@sv.on_fullmatch("steam订阅列表")
async def check_steam(bot, ev: CQEvent):
    # 获取群号
    group_id = ev.group_id
    # 如果群号不在 group_subscribe 中, 则添加群号json, 其中为一个空列表
    if str(group_id) not in group_subscribe_json:
        await bot.send(ev, "本群没有订阅任何用户")
        return
    # 如果群号在 group_subscribe 中, 则判断是否已经订阅过该 UID(group_subscribe[str(group_id)]为 json, 存储了该群订阅的 UID 列表)
    else:
        # 如果没有订阅过该 UID, 则返回
        if len(group_subscribe_json[str(group_id)]) == 0:
            await bot.send(ev, "本群没有订阅任何用户")
            return
    # 如果群号在 group_subscribe 中, 且订阅过该 UID, 则从 group_subscribe_json 中删除
    msg = "=======Steam订阅列表=======\n"
    for steam_uid in group_subscribe_json[str(group_id)]:
        # 获取该用户正在游玩的游戏名称
        game_name = steam_uid_game_json[steam_uid]
        # 如果为 null, 则表示没有在玩游戏
        if game_name == None:
            msg += f"{steam_uid_nickname_json[steam_uid]} 没在玩游戏\n"
        else:
            msg += f"{steam_uid_nickname_json[steam_uid]} 正在玩 {steam_uid_game_json[steam_uid]}\n"
    await bot.send(ev, msg)

# 谁在玩游戏
@sv.on_fullmatch("谁在玩游戏")
async def who_is_playing(bot, ev: CQEvent):
    # 获取群号
    group_id = ev.group_id
    # 如果群号不在 group_subscribe 中, 则添加群号json, 其中为一个空列表
    if str(group_id) not in group_subscribe_json:
        await bot.send(ev, "本群没有订阅任何用户")
        return
    # 如果群号在 group_subscribe 中, 则判断是否已经订阅过该 UID(group_subscribe[str(group_id)]为 json, 存储了该群订阅的 UID 列表)
    else:
        # 如果没有订阅过该 UID, 则返回
        if len(group_subscribe_json[str(group_id)]) == 0:
            await bot.send(ev, "本群没有订阅任何用户")
            return
    # 如果群号在 group_subscribe 中, 且订阅过该 UID, 则从 group_subscribe_json 中删除
    msg = "=======Steam======\n"
    for steam_uid in group_subscribe_json[str(group_id)]:
        # 获取该用户正在游玩的游戏名称
        game_name = steam_uid_game_json[steam_uid]
        # 如果为 null, 则表示没有在玩游戏
        if game_name == None:
            continue
        else:
            msg += f"{steam_uid_nickname_json[steam_uid]} 正在玩 {steam_uid_game_json[steam_uid]}\n"
    # 如果没有人在玩游戏, 则返回
    if msg == "=======Steam======\n":
        await bot.send(ev, "当前没有已订阅的群友在玩游戏")
        return
    await bot.send(ev, msg)




#### 测试与分析代码 ####


# 私聊消息测试
@sv.on_fullmatch("steam_slcs")
async def slcs(bot, ev: CQEvent):
    await bot.send_private_msg(user_id=ADMIN_QQID, message=f"由于没有大于100的实际用例, 这条信息仅用来测试私聊消息")

# 群聊消息示例
@sv.on_fullmatch("steam_gcs")
async def gcs(bot, ev: CQEvent):
    await bot.send(ev, f"群聊消息测试")

# 合并转发消息测试
@sv.on_fullmatch("steam_hf")
async def hf(bot, ev: CQEvent):
    img_42_path = Path(__file__).parent / "42.jpg"
    img = open(img_42_path, "rb").read()
    image_b64 = f"base64://{str(base64.b64encode(img).decode())}"
    data = {"type": "node", "data": {"name": "合并转发测试", "uin": "2854196310", "content": f"[CQ:image,file={image_b64}]"}}
    await bot.send_group_forward_msg(group_id=ev["group_id"], messages=data)

# # 获取游戏在线状态
# async def get_game_status(id_list):
#     print("开始轮询")
#     for id in id_list:
#         response = httpx.get(PLAYER_SUMMARY.format(STEAM_APIKEY, id)).json()
#         print(response)
#         # 如果 gameid 存在, 则说明有人在玩游戏
#         if "gameid" in response["response"]["players"][0]:
#             print("有人在玩游戏")
#             msg = (
#                 response["response"]["players"][0]["personaname"]
#                 + " 正在玩 "
#                 + response["response"]["players"][0]["gameextrainfo"]
#             )
#             await sv.bot.send_group_msg(group_id=297972329, message=msg)
#         else:
#             print("没人在玩游戏")


# # 轮询测试, 每 30 秒执行一次
# @sv.scheduled_job("cron", second="*/30")
# async def async_test():
#     print("Hello World")
#     # await sv.bot.send_group_msg(group_id=297972329, message="Hello World")
#     await get_game_status(id_list)
