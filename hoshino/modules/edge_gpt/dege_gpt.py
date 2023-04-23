
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

# 用于发图
import base64


import asyncio
from EdgeGPT import Chatbot, ConversationStyle


sv_help = """
Edge GPT 测试
""".strip()

sv = Service(
    name="edge_gpt",  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=False,  # 默认启用
    bundle="娱乐",  # 分组归类
    help_=sv_help,  # 帮助说明
)


async def main():
    bot = Chatbot(cookie_path="/home/ubuntu/Bot/EdgeGPT/cookies.json", proxy="socks5://127.0.0.1:7890")
    print(await bot.ask(prompt="Hello world", conversation_style=ConversationStyle.creative, wss_link="wss://sydney.bing.com/sydney/ChatHub"))
    await bot.close()


# 匹配 edge 开头的消息
@sv.on_prefix('edge')
async def edge_gpt(bot, ev: CQEvent):
    # 获取消息内容
    msg = ev.message.extract_plain_text()
    # 去除消息前缀
    msg = msg.replace('edge', '', 1)
    # 去除消息前后空格
    msg = msg.strip()
    # 判断消息是否为空
    if msg == '':
        # 如果为空则返回
        return
    botC = Chatbot(cookie_path="/home/ubuntu/Bot/EdgeGPT/cookies.json", proxy="socks5://127.0.0.1:7890")
    resp_dict = await botC.ask(prompt=msg, conversation_style=ConversationStyle.creative, wss_link="wss://sydney.bing.com/sydney/ChatHub")
    await botC.close()
    # 返回 resp.item.message 列表中的第2个元素中的 text 字段
    await bot.send(ev, resp_dict['item']['messages'][1]['text'])

    



# if __name__ == "__main__":
#     asyncio.run(main())
