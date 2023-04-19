from email.quoprimime import unquote
from numpy import TooHardError
import requests
from hoshino import Service
from hoshino.typing import CQEvent
import base64
from loguru import logger
import re
import json
from hoshino import aiorequests
import io
from io import BytesIO
from PIL import Image
import sqlite3
import os
from hoshino.util import FreqLimiter, DailyNumberLimiter

####替换成自己的API URL
word2img_url = "http://91.217.139.190:5010/got_image"
img2img_url = "http://91.217.139.190:5010/got_image2image"
token = 'met80zci9w17aXS2bjFGN4ZA3DqvxW5R'

sv = Service('AI_image_gen', bundle='娱乐', help_='''
生成色图 
'''.strip())

sv_help='''
使用NAI API生成二次元图
使用方法：ai绘图 <tags>[&shape=Portrait/Landscape/Square|&scale=11|&seed=1234]
<tags>为必选参数  [ ]为可选参数，其中：
tags 图片含有的要素，使用大括号{}括住某些tag来增加此tag的权重，括号越多权重越高如{{{loli}}}
shape 分别为竖图、横图、方图 默认为横图
scale 细节等级，建议为11-24，太高会变奇怪
seed 随机种子，任意数字。相同的种子可能会有相同的结
'''.strip()


# sv_help='''
# 使用NAI API生成二次元图
# 使用方法：ai绘图 <tags>[&r18=0|&shape=Portrait/Landscape/Square|&scale=11|&seed=1234]
# <tags>为必选参数  [ ]为可选参数，其中：
# tags 图片含有的要素，使用大括号{}括住某些tag来增加此tag的权重，括号越多权重越高如{{{loli}}}
# r18 字面意思，默认为0,开启为1 请勿在公共群开启
# shape 分别为竖图、横图、方图 默认为横图
# scale 细节等级，建议为11-24，太高会变奇怪
# seed 随机种子，任意数字。相同的种子可能会有相同的结
# '''.strip()

@sv.on_fullmatch('ai绘图帮助')
async def gen_pic_help(bot, ev: CQEvent):
    # mes = f'使用NAI API生成二次元图\n'
    # mes += f'使用方法：生成色图 <tags>[&r18=0|&shape=Portrait/Landscape/Square|&scale=11|&seed=1234]\n'
    # mes += f'<tags>为必选参数  [ ]为可选参数，其中：\n'
    # mes += f'tags 图片含有的要素，使用大括号{{}}括住某些tag来增加此tag的权重，如' + '{{{'+'loli' + '}}}\n'
    # mes += f'r18 字面意思，默认为0,开启为1 请勿在公共群开启\n'
    # mes += f'shape 分别为竖图、横图、方图 默认为横图\n'
    # mes += f'scale 细节等级，建议为11-24，太高会变奇怪\n'
    # mes += f'seed 随机种子，任意数字。相同的种子可能会有相同的结果'
    await bot.send(ev, sv_help)




XP_DB_PATH = os.path.expanduser('~/.hoshino/AI_image_xp.db')
class XpCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(XP_DB_PATH), exist_ok=True)
        self._create_table()
    def _connect(self):
        return sqlite3.connect(XP_DB_PATH)
        
    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS XP_NUM
                          (UID             INT    NOT NULL,
                           KEYWORD         TEXT   NOT NULL,
                           NUM             INT    NOT NULL,
                           PRIMARY KEY(UID,KEYWORD));''')
        except:
            raise Exception('创建表发生错误')
            
    def _add_xp_num(self, uid, keyword):
        try:
        
            num = self._get_xp_num(uid, keyword)
            if num == None:
                num = 0
            num += 1
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO XP_NUM (UID,KEYWORD,NUM) \
                                VALUES (?,?,?)", (uid, keyword, num)
                )
                  
        except:
            raise Exception('更新表发生错误')
            
    def _get_xp_num(self, uid, keyword):
        try:
            r = self._connect().execute("SELECT NUM FROM XP_NUM WHERE UID=? AND KEYWORD=?", (uid, keyword)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')
    
    def _get_xp_list(self, uid, num):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT KEYWORD,NUM FROM XP_NUM WHERE UID={uid} ORDER BY NUM desc LIMIT {num}").fetchall()
        return r if r else {}

def get_xp_list(uid):
    XP = XpCounter()
    xp_list = XP._get_xp_list(uid, 15)
    if len(xp_list)>0:
        data = sorted(xp_list,key=lambda cus:cus[1],reverse=True)
        new_data = []
        for xp_data in data:
            keyword, num = xp_data
            new_data.append((keyword,num))
        rankData = sorted(new_data,key=lambda cus:cus[1],reverse=True)
        return rankData
    else:
        return []

def add_xp_num(uid, keyword):
    XP = XpCounter()
    XP._add_xp_num(uid, keyword)



@sv.on_fullmatch(['我的XP'])
async def get_my_xp(bot, ev: CQEvent):
    xp_list = get_xp_list(ev.user_id)
    uid = ev.user_id
    msg = '您的XP信息为：\n'
    if len(xp_list)>0:
        for xpinfo in xp_list:
            keyword, num = xpinfo
            msg += f'关键词：{keyword}；查询次数：{num}\n'
    else:
        msg += '暂无您的XP信息'
    await bot.send(ev, msg)

black_list = ['nsfw', 'naked', 'sex', 'spread leg', 'cum_on_facial']
group_list = [624986896, 297972329, 744306731]
active_list = [297972329, 744306731]


@sv.on_prefix(('ai绘图'))
async def gen_pic(bot, ev: CQEvent):
    try:
        print(f'群号为:{ev.group_id}')
        if ev.group_id not in group_list:
                pass
        else:
            await bot.send(ev, f"正在生成", at_sender=True)
            text = ev.message.extract_plain_text()
            taglist = [chr.lower() for chr in text.split(',')]
            # 遍历 taglist, 如果在 black_list 中则删除
            for i in taglist: 
                if i in black_list:
                    taglist.remove(i)
            # print(taglist)
            uid = ev.user_id
            for tag in taglist:
                add_xp_num(uid, tag)
            tags = ','.join(str(i) for i in taglist)
            get_url = word2img_url + "?r18=0&tags=" + tags + f'&token={token}'
            print(f'正在请求{get_url}')
            # image = await aiorequests.get(get_url)
            res = await aiorequests.get(get_url)
            image = await res.content
            load_data = json.loads(re.findall('{"steps".+?}', str(image))[0])
            image_b64 = f"base64://{str(base64.b64encode(image).decode())}"
            print("开始合并转发消息")
            mes = f"[CQ:image,file={image_b64}]\n"
            mes += f'seed:{load_data["seed"]}   '
            mes += f'scale:{load_data["scale"]}\n'
            # mes += f'tags:{text}'
            data = {
                "type": "node", 
                "data": {
                    "name": "QQ小冰", 
                    "uin": "2854196310", 
                    "content": mes
                }
            }
            print("抓发消息合并完成,开始发送转发消息")
            await bot.send_group_forward_msg(group_id=ev["group_id"], messages=data)

    except:
        await bot.send(ev, "生成失败…")


@sv.on_prefix(('aigen'))
async def gen_pic(bot, ev: CQEvent):
    try:
        print(f'群号为:{ev.group_id}')
        if ev.group_id not in active_list:
            pass
        else:
            await bot.send(ev, f"正在生成", at_sender=True)
            text = ev.message.extract_plain_text()
            get_url = word2img_url + "?r18=1&tags=" + text + f'&token={token}'
            print(f'正在请求{get_url}')
            # image = await aiorequests.get(get_url)
            res = await aiorequests.get(get_url)
            image = await res.content
            load_data = json.loads(re.findall('{"steps".+?}', str(image))[0])
            image_b64 = 'base64://' + str(base64.b64encode(image).decode())
            mes = f"[CQ:image,file={image_b64}]\n"
            mes += f'seed:{load_data["seed"]}   '
            mes += f'scale:{load_data["scale"]}\n'
            mes += f'tags:{text}'
            await bot.send(ev, mes, at_sender=True)
    except:
        await bot.send(ev, "生成失败…")



@sv.on_prefix("以图生图")
async def img2img(bot, ev):
    tag = ev.message.extract_plain_text()
    if tag == "":
        url = ev.message[0]["data"]["url"]
    else:
        url = ev.message[1]["data"]["url"]
    await bot.send(ev, "正在生成", at_sender=True)
    image = Image.open(io.BytesIO(requests.get(url, timeout=20).content))
    # img_x, img_y = int(image.size[0] * (768 / image.size[1])), 768
    # image = image.resize((img_x, img_y))
    thumbSize = (768, 768)
    image = image.convert("RGB")
    if (image.size[0] > image.size[1]):
        image_shape = "Landscape"
    elif (image.size[0] == image.size[1]):
        image_shape = "Square"
    else:
        image_shape = "Portrait"

    image.thumbnail(thumbSize, resample=Image.ANTIALIAS)
    b_io = io.BytesIO()
    image.save(b_io, format="JPEG")
    posturl =  img2img_url + (f"?tags={tag}&token={token}" if tag != "" else f"?token={token}") 
    resp = await aiorequests.post(
        posturl,
        data=base64.b64encode(b_io.getvalue()),
    )
    print(f'正在向{posturl}发起请求')
    img = await resp.content
    # print(f'返回结果:{img}')
    image_b64 = f"base64://{str(base64.b64encode(img).decode())}"
    data = {"type": "node", "data": {"name": "ai绘图", "uin": "2854196310", "content": f"[CQ:image,file={image_b64}]"}}
    await bot.send_group_forward_msg(group_id=ev["group_id"], messages=data)
