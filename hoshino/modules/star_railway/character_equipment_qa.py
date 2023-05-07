# 似乎看到过云崽的 *char 指令, 会返回角色的推荐装备信息, 不过没有找到源码在哪里, 所以这里直接关键词+抄图做个简陋的qa
from pathlib import Path
# base64, 用于发图
import base64
# 引入 hoshino 相关库
from hoshino import Service, priv, config
from hoshino.typing import CQEvent
# 时间, 用于记录日志
from datetime import datetime
# 用于读取角色昵称信息
import json


sv_help = """
似乎看到过云崽的 *char 指令, 会返回角色的推荐装备信息, 不过没有找到源码在哪里, 所以这里直接关键词+抄图做个简陋的qa  

""".strip()

sv = Service(
    name="star_railway",  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    bundle="娱乐",  # 分组归类
    help_=sv_help,  # 帮助说明
)

# 定义 json 文件路径
character_nickname_path = Path(__file__).parent / "character_nickname.json"

# 读取 json 文件
character_nickname_json = json.load(open(character_nickname_path, "r", encoding="utf-8"))

# 合并转发消息测试
@sv.on_prefix("*")
async def character_equipment_simple_qa(bot, ev: CQEvent):
    # 获取 * 后的角色昵称
    char_nickname = ev.message.extract_plain_text()
    char_name = next(
        (
            char_prename
            for char_prename in character_nickname_json
            if char_nickname in character_nickname_json[char_prename]
        ),
        str(),
    )
    if char_name == "":
        return
    # 根据 char_name 拼接角色装备推荐图片路径
    img_42_path = Path(__file__).parent / "res/character_equipment" / f"{char_name}.png"
    img = open(img_42_path, "rb").read()
    image_b64 = f"base64://{str(base64.b64encode(img).decode())}"
    msg = f"[CQ:image,file={image_b64}]"
    await bot.send(ev, msg)