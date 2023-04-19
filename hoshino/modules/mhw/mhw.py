# 引入 hoshino 相关库
from hoshino import Service, priv, config
from hoshino.typing import CQEvent

# 引入配置文件相关库
import rtoml
from pathlib import Path
# json
import json

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


# 定义 json 文件路径
# 日期-集会码字典列表 json
date_code_json_path = Path(__file__).parent / "json/date_code.json"

json_path_list = [date_code_json_path]

# 如果 json 文件不存在, 则创建
for json_path in json_path_list:
    if not json_path.exists():
        json_path.touch()
        json_path.write_text("{}")

# 读取 json 文件
# 日期-集会码字典列表 json
date_code_json = json.loads(date_code_json_path.read_text())


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
    nickname = ev.sender['card'] or ev.sender['nickname']
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
    nickname = ev.sender['card'] or ev.sender['nickname']
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


# mhw 帮助
@sv.on_fullmatch("帮助mhw")
async def mhw_help(bot, ev: CQEvent):
    msg = "可使用的命令(请注意空格)(中括号表示其中的内容为可选项, 不输入的话将按照默认内容录入):\n"
    msg += "添加集会码 集会码 [备注]\n"
    msg += "今日集会码\n"
    msg += "删除集会码 集会码\n"
    msg += "删除我添加的集会码\n"
    msg += "昨日集会码\n"
    msg += "修改集会备注 集会码 备注\n"
    await bot.send(ev, msg)