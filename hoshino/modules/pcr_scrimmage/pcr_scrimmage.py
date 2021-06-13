"""
<A little game base on hoshino_bot, gameplay like RichMan>
Copyright (C) <2021/06/11>  <eggggi>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from typing import List
import os
import asyncio
import math
import random
import re

from PIL import Image, ImageFont, ImageDraw
from hoshino.typing import CQEvent
from hoshino import R, Service, priv, log
from hoshino.modules.priconne import chara

from .role import (ROLE,
                   EFFECT_DEFENSIVE, EFFECT_ATTACK, EFFECT_DISTANCE, EFFECT_HEALTH, EFFECT_MOVE, EFFECT_TP,
                   EFFECT_MOVE_GOAL, EFFECT_OUT_TP, EFFECT_OUT_TURN, EFFECT_IGNORE_DIST,
                   TRIGGER_ME, TRIGGER_ALL_EXCEPT_ME, TRIGGER_ALL, TRIGGER_SELECT, TRIGGER_NEAR)
from .runway_case import (CASE_NONE, CASE_ATTACK, CASE_DEFENSIVE, CASE_HEALTH,
                          CASE_MOVE, CASE_TP, RUNWAY_CASE)

sv = Service('pcr_scrimmage', manage_priv=priv.ADMIN, enable_on_default=True, visible=False)
FILE_PATH = os.path.dirname(__file__)

IMAGE_PATH = R.img('pcr_scrimmage').path
logger = log.new_logger('pcr_scrimmage')
if not os.path.exists(IMAGE_PATH):
    os.mkdir(IMAGE_PATH)
    logger.info('create folder succeed')


async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card'] != '' else m['nickname']
    return d


def uid2card(uid, user_card_dict):
    return str(uid) if uid not in user_card_dict.keys() else user_card_dict[uid]


# 防御力计算机制。
# 100点防御力内，每1点防御力增加0.1%伤害减免；
# 100点防御力后，每1点防御力增加0.05%伤害减免；
# 最高有效防御力为1000
# （防御力可无限提升，但最高只能获得55%伤害减免）
def hurt_defensive_calculate(hurt, defensive):
    percent = 0.0
    if defensive <= 100:
        percent = defensive * 0.001
    else:
        if defensive <= 1000:
            percent = 100 * 0.001 + (defensive - 100) * 0.0005
        else:
            percent = 100 * 0.001 + 900 * 0.0005
    return hurt - hurt * percent


###显示偏移###	（可以改）
OFFSET_X = 45  # 整体右移
OFFSET_Y = 50  # 整体下移

###线宽###		（别改）
RUNWAY_LINE_WDITH = 4  # 跑道线宽
STATU_LINE_WDITH = 2  # 状态条线宽 血条tp条

###常用颜色###
COLOR_BLACK = (0, 0, 0)
COLOR_WRITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_CAM_GREEN = (30, 230, 100)  # 血条填充色
COLOR_CAM_BLUE = (30, 144, 255)  # tp条填充色

###当前房间状态###
NOW_STATU_WAIT = 0
NOW_STATU_SELECT_ROLE = 1
NOW_STATU_OPEN = 2
NOW_STATU_END = 3
NOW_STATU_WIN = 4

###当前玩家处于什么阶段###
NOW_STAGE_WAIT = 0  # 等待
NOW_STAGE_DICE = 1  # 丢色子
NOW_STAGE_SKILL = 2  # 释放技能
NOW_STAGE_OUT = 3  # 出局

MAX_PLAYER = 4  # 最大玩家数量
MAX_TP = 100  # tp值上限
MAX_DIST = 15  # 最大攻击距离
ONE_ROUND_TP = 10  # 单回合获得tp量
FOUR_ROUND_DISTANCE = 2  # 每隔4回合增加的攻击距离
FOUR_ROUND_ATTACK = 10  # 每隔4回合增加的攻击力
HIT_DOWN_TP = 20  # 击倒获得的tp

RET_ERROR = -1  # 错误
RET_SUCCESS = 1  # 成功


# 角色
class Role:
    def __init__(self, user_id) -> None:
        self.user_id = user_id  # 玩家的qq号
        self.role_id = 0  # pcr角色编号
        self.role_icon = None  # 角色头像
        self.player_num = 0  # 玩家在这个房间的编号
        self.room_obj = None  # 房间对象

        self.name = ''  # 角色名
        self.max_health = 0  # 生命值
        self.distance = 0  # 攻击距离
        self.attack = 0  # 攻击力
        self.defensive = 0  # 防御力
        self.tp = 0  # tp值（能量值）
        self.save_tp = 0  # 保存的tp值

        self.active_skills = []  # 技能列表
        self.passive_skills = []  # 被动列表

        self.now_health = 0  # 当前生命值
        self.now_location = 0  # 当前位置
        self.now_stage = NOW_STAGE_WAIT  # 当前处于什么阶段

    # 选择角色后对数据的初始化
    def initData(self, role_id, role_info, room_obj):
        role_data = ROLE[role_id]
        if role_data:
            self.role_id = role_id
            self.role_icon = role_info.icon.open()
            self.room_obj = room_obj

            self.name = role_data['name']
            self.max_health = role_data['health']
            self.distance = role_data['distance']
            self.attack = role_data['attack']
            self.defensive = role_data['defensive']
            self.tp = role_data['tp']

            self.active_skills = role_data['active_skills']
            self.passive_skills = role_data['passive_skills']

            self.now_health = self.max_health

    # 属性数值改变的统一处理
    def healthChange(self, num):
        if self.now_stage == NOW_STAGE_OUT:
            return
        if num < 0:  # 如果生命值减少，则按百分比回复tp
            hurt_tp = math.floor(abs(num) / self.max_health * 100 / 2)
            self.tpChange(hurt_tp)
        self.now_health += num
        if self.now_health > self.max_health:
            self.now_health = self.max_health
        elif self.now_health <= 0:
            self.now_health = 0
            self.room_obj.outDispose(self)

    def distanceChange(self, num):
        self.distance += num
        if self.distance > MAX_DIST:
            self.distance = MAX_DIST
        elif self.distance < 0:
            self.distance = 0

    def attackChange(self, num):
        if self.now_stage == NOW_STAGE_OUT:
            return
        self.attack += num
        if self.attack < 0:
            self.attack = 0

    def defensiveChange(self, num):
        if self.now_stage == NOW_STAGE_OUT:
            return
        self.defensive += num
        if self.defensive < 0:
            self.defensive = 0

    def tpChange(self, num, is_save=False):
        if self.now_stage == NOW_STAGE_OUT:
            return
        if is_save:
            self.save_tp += num
            return
        self.tp += num
        self.tp += self.save_tp
        self.save_tp = 0
        if self.tp > MAX_TP:
            self.tp = MAX_TP
        elif self.tp < 0:
            self.tp = 0

    def locationChange(self, num, runway):
        if self.now_stage == NOW_STAGE_OUT:
            return
        runway[self.now_location]["players"].remove(self.user_id)
        self.now_location += num
        if self.now_location >= len(runway):
            self.now_location -= len(runway)
        elif self.now_location < 0:
            self.now_location = len(runway) + self.now_location
        runway[self.now_location]["players"].append(self.user_id)

    def stageChange(self, stage):
        self.now_stage = stage

    # 检查当前状态
    def checkStatu(self, scrimmage):
        msg = [f"玩家：{uid2card(self.user_id, scrimmage.user_card_dict)}",
               f"角色：{self.name}",
               f"生命值：{self.now_health}/{self.max_health}",
               f"TP：{self.tp}",
               f"攻击距离：{self.distance}",
               f"攻击力：{self.attack}",
               f"防御力：{self.defensive}",
               f'位置：{self.now_location}']
        return msg


# 公主连结大乱斗
class PCRScrimmage:
    # 初始化
    def __init__(self, gid, manager, room_master, across_range=10, vertical_range=10, grid_size=50) -> None:
        ##核心数据
        self.gid = gid  # 群号
        self.mgr = manager  # 管理器
        self.room_master = room_master  # 房主
        self.player_list = {}  # 玩家列表  ####这个东西不能迭代values，不懂原理
        self.now_statu = NOW_STATU_WAIT  # 当前游戏状态
        self.now_turn = 0  # 现在是玩家x的回合
        self.dice_num = 0  # 已丢色子次数的总数
        self.lock_turn = 0  # 回合锁定，x回合内都是同个玩家
        self.now_playing_players = []  # 当前正在游玩的玩家id	[xxx, xxx]
        self.rank = {}  # 结算排行	{1:xxx,2:xxx}

        self.user_card_dict = {}  # 群内所有成员信息

        # 初始化跑道，总共36个格子
        self.runway = [{"players": [], "case": 0} for i in range((across_range - 1) * 4)]
        for runway_case in self.runway:
            runway_case["case"] = random.choice(range(len(RUNWAY_CASE)))

        ##显示数据	注意：显示数据别乱改
        self.grid_size = grid_size  ##本来想做自定义跑道数量的，但显示适配太麻烦了，躺平
        self.vertical_range_x = vertical_range
        self.across_range_y = across_range
        width = (self.vertical_range_x + 2) * self.grid_size
        height = (self.across_range_y + 2) * self.grid_size

        # 基础图片，初始化完成后不会再改变
        self.base_image = Image.new('RGB', (width, height), COLOR_WRITE)
        self.draw = ImageDraw.Draw(self.base_image)

        # 当前状态图片，会随着游戏进度一直改变
        self.now_image = Image.new('RGB', (width, height), COLOR_WRITE)
        self.now_draw = ImageDraw.Draw(self.now_image)

        FONTS_PATH = os.path.join(FILE_PATH, 'fonts')
        FONTS = os.path.join(FONTS_PATH, 'msyh.ttf')
        self.runwayTextFont = ImageFont.truetype(FONTS, 30)
        self.font = ImageFont.truetype(FONTS, 15)
        pass

    def __enter__(self):
        self.mgr.playing[self.gid] = self
        self.displayInit()
        self.ready(self.room_master)
        return self

    def __exit__(self, type_, value, trace):
        del self.mgr.playing[self.gid]

    # 加入房间准备
    def ready(self, user_id):
        if self.getPlayerNum() < MAX_PLAYER:
            self.player_list[user_id] = Role(user_id)
        pass

    # 检查是否全部玩家都选择了角色
    def checkAllPlayerSelectRole(self):
        num = 0
        for player_id in self.player_list:
            if self.getPlayerObj(player_id).role_id != 0:
                num += 1
        if num >= len(self.player_list):
            return True
        else:
            return False

    # 游戏正式开始需要做的处理
    def gameOpen(self):
        num = 0
        for player_id in self.player_list:
            offset_x, offset_y = 0, 0
            if num == 1:
                offset_x = 1
            elif num == 2:
                offset_y = 1
            elif num == 3:
                offset_x, offset_y = 1, 1

            self.now_playing_players.append(player_id)
            player = self.getPlayerObj(player_id)
            player.now_location = num * 9  # 玩家保存的位置
            self.runway[num * 9]["players"].append(player_id)  # 跑道保存的位置
            player.player_num = num  # 玩家编号
            head = player.role_icon  # 玩家头像

            after_head = head.resize((95, 97))

            # 放置玩家头像
            self.base_image.paste(after_head,
                                  (OFFSET_X + self.grid_size * 2 + offset_x * 200 + 3,
                                   OFFSET_Y + math.floor(self.grid_size * 1.5) + offset_y * 190 + 2))
            # 显示玩家名字
            self.playerInfoText(offset_x, offset_y, 12, text=f'name：{uid2card(player.user_id, self.user_card_dict)}')
            # 攻击距离
            self.playerInfoText(offset_x, offset_y, 28, text=f'dist   ：{player.distance}')

            num += 1

        # 房主的状态改为丢色子状态
        self.getPlayerObj(self.room_master).stageChange(NOW_STAGE_DICE)

        # 更新当前显示状态
        self.refreshNowImageStatu()

    # 回合改变，到下一个玩家
    def turnChange(self):
        now_turn_player = self.getNowTurnPlayerObj()
        if now_turn_player.now_stage != NOW_STAGE_OUT:  # 如果当前玩家已经出局，则不改变状态
            now_turn_player.stageChange(NOW_STAGE_WAIT)  # 已结束的玩家
        else:
            self.lock_turn = 0  # 如果玩家已出局，则取消回合锁定

        # 游戏胜利或结束则直接退出
        if (self.now_statu == NOW_STATU_WIN or
                self.now_statu == NOW_STATU_END):
            return

        # 寻找下一回合的玩家
        for i in range(len(self.player_list)):
            self.now_turn += 1
            if self.now_turn >= len(self.player_list):
                self.now_turn = 0
            next_turn_player = self.getNowTurnPlayerObj()  # 下一个玩家
            if next_turn_player.now_stage != NOW_STAGE_OUT:  # 跳过已出局的玩家
                if self.lock_turn > 0:  # 检查是否锁定了当前回合
                    now_turn_player.stageChange(NOW_STAGE_DICE)
                    self.now_turn = now_turn_player.player_num
                    self.lock_turn -= 1
                    return
                next_turn_player.stageChange(NOW_STAGE_DICE)
                return
        # 找不到直接结束游戏
        self.now_statu = NOW_STATU_END

    # 玩家出局处理
    def outDispose(self, player: Role):
        player.stageChange(NOW_STAGE_OUT)
        self.rank[len(self.now_playing_players)] = player.user_id
        self.now_playing_players.remove(player.user_id)
        if len(self.now_playing_players) == 1:
            self.rank[1] = self.now_playing_players[0]
            self.now_statu = NOW_STATU_WIN

    # 丢色子
    async def throwDice(self, player_id, step, bot, ev):
        player = self.getPlayerObj(player_id)

        player.locationChange(step, self.runway)

        for iter_player_id in self.player_list:  # 每丢1次色子，所有玩家增加10点tp
            self.getPlayerObj(iter_player_id).tpChange(ONE_ROUND_TP)
        self.dice_num += 1
        if self.dice_num > 4:
            for iter_player_id in self.player_list:  # 每丢4次色子，所有玩家增加2点攻击距离
                self.getPlayerObj(iter_player_id).distanceChange(FOUR_ROUND_DISTANCE)
                self.getPlayerObj(iter_player_id).attackChange(FOUR_ROUND_ATTACK)
            self.dice_num = 1

        await self.caseTrigger(player, bot, ev)

    # 触发跑道事件
    async def caseTrigger(self, player: Role, bot, ev: CQEvent):
        case_num = self.runway[player.now_location]["case"]
        str1, num = "", 0
        if case_num == CASE_NONE:
            pass
        elif case_num == CASE_HEALTH:
            numRange = RUNWAY_CASE[CASE_HEALTH]["range"]
            num = random.choice(range(numRange[0], numRange[1]))
            player.healthChange(num)
        elif case_num == CASE_DEFENSIVE:
            numRange = RUNWAY_CASE[CASE_DEFENSIVE]["range"]
            num = random.choice(range(numRange[0], numRange[1]))
            player.defensiveChange(num)
        elif case_num == CASE_ATTACK:
            numRange = RUNWAY_CASE[CASE_ATTACK]["range"]
            num = random.choice(range(numRange[0], numRange[1]))
            player.attackChange(num)
        elif case_num == CASE_TP:
            numRange = RUNWAY_CASE[CASE_TP]["range"]
            num = random.choice(range(numRange[0], numRange[1]))
            player.tpChange(num)
        elif case_num == CASE_MOVE:
            numRange = RUNWAY_CASE[CASE_MOVE]["range"]
            num = random.choice(range(numRange[0], numRange[1]))
            if num == 0:
                num += 1
            player.locationChange(num, self.runway)

        if num > 0:
            if case_num == CASE_MOVE:
                str1 = "前"
            else:
                str1 = "增加"
        else:
            if case_num == CASE_MOVE:
                str1 = "后"
            else:
                str1 = "减少"
        text = "触发事件，"
        text += RUNWAY_CASE[case_num]["text"].format(str1, abs(num))
        if case_num != CASE_NONE and num == 0:
            text += "，所以什么都不会发生"
        elif case_num == CASE_NONE:
            text = "什么也没发生"
        await bot.send(ev, text)

        if case_num == CASE_MOVE and num != 0:
            self.refreshNowImageStatu()
            image_path = R.img(f'{IMAGE_PATH}/{ev.group_id}.jpg').path
            img = self.getNowImage()
            img.save(image_path)
            await bot.send(ev, R.img(image_path).cqcode)
            await asyncio.sleep(1)
            await self.caseTrigger(player, bot, ev)
        if player.now_stage == NOW_STAGE_OUT:
            await bot.send(ev, f'{uid2card(player.user_id, self.user_card_dict)}出局')
            self.turnChange()  # 回合切换
            self.refreshNowImageStatu()  # 刷新当前显示状态
        else:
            player.stageChange(NOW_STAGE_SKILL)

    # 使用技能
    # noinspection PyTypeChecker
    async def useSkill(self, skill_id, use_player_id, goal_player_id, bot, ev):
        if skill_id != 0:
            use_player_obj = self.getPlayerObj(use_player_id)
            if skill_id > len(use_player_obj.active_skills) or skill_id <= 0:
                return await bot.send(ev, '技能编号不正确')

            real_skill_id = skill_id - 1  # 实际技能id
            skill = use_player_obj.active_skills[real_skill_id]
            skill_tp_cost = skill["tp_cost"]  # tp消耗
            if skill_tp_cost > use_player_obj.tp:  # 检查tp是否足够
                await bot.send(ev, 'tp不足，无法使用这个技能')
                return RET_ERROR

            use_player_name = uid2card(use_player_obj.user_id, self.user_card_dict)
            use_skill_nale = use_player_obj.active_skills[real_skill_id]["name"]
            await bot.send(ev, f'{use_player_name}尝试使用{use_skill_nale}')

            back_msg = []
            ret, msg = self.skillTrigger(use_player_obj, goal_player_id, real_skill_id, False, back_msg)
            if ret == RET_ERROR:
                await bot.send(ev, msg)
                return ret
            await bot.send(ev, '\n'.join(back_msg))
            use_player_obj.tpChange(-skill_tp_cost)

        self.turnChange()  # 回合切换
        self.refreshNowImageStatu()  # 刷新当前显示状态
        return RET_SUCCESS

    # 技能释放对象选择
    def skillTrigger(self, use_skill_player: Role, goal_player_id, skill_id, is_passive, back_msg):

        if is_passive:
            skill = use_skill_player.passive_skills[skill_id]  # 被动技能详细数据
        else:
            skill = use_skill_player.active_skills[skill_id]  # 主动技能详细数据
        skill_trigger = skill["trigger"]  # 技能的触发对象
        skill_effect = skill["effect"]  # 技能效果

        if skill_trigger == TRIGGER_SELECT:  # 选择触发对象
            if goal_player_id > 0:
                goal_player_obj = self.getPlayerObj(goal_player_id)
                if not goal_player_obj:
                    return RET_ERROR, '目标不在房间里'
                if goal_player_obj.now_stage == NOW_STAGE_OUT:
                    return RET_ERROR, '目标已出局'

                # 检查被动技能里是否带有无视距离的技能效果
                disregard_dist = False
                if "passive" in skill and len(skill["passive"]) != 0:
                    for passive_skill_id in skill["passive"]:
                        passive_skill_effect = use_skill_player.passive_skills[passive_skill_id]["effect"]
                        if (EFFECT_MOVE_GOAL in passive_skill_effect or
                                EFFECT_IGNORE_DIST in passive_skill_effect):
                            disregard_dist = True
                            break

                # 计算攻击距离
                dist = self.getTwoPlayerDist(use_skill_player, goal_player_obj)
                if dist > use_skill_player.distance and not disregard_dist and not is_passive:
                    return RET_ERROR, '攻击距离不够'

                # 先触发被动技能
                if "passive" in skill and len(skill["passive"]) != 0:
                    for passive_skill_id in skill["passive"]:
                        ret, msg = self.skillTrigger(use_skill_player, goal_player_id, passive_skill_id, True, back_msg)
                        if ret == RET_ERROR:
                            return ret, msg
                # 后触发主动技能
                return self.skillEffect(use_skill_player, goal_player_obj, skill_effect, back_msg)
            else:
                return RET_ERROR, '该技能需要选择一个目标'

        # 先触发被动技能
        if "passive" in skill and len(skill["passive"]) != 0:
            for passive_skill_id in skill["passive"]:
                ret, msg = self.skillTrigger(use_skill_player, goal_player_id, passive_skill_id, True, back_msg)
                if ret == RET_ERROR:
                    return ret, msg

        if skill_trigger == TRIGGER_ME:  # 自己
            ret, msg = self.skillEffect(use_skill_player, use_skill_player, skill_effect, back_msg)
            if ret == RET_ERROR:
                return ret, msg
        elif skill_trigger == TRIGGER_ALL:  # 所有人
            for player_id in self.player_list:
                goal_player = self.getPlayerObj(player_id)
                ret, msg = self.skillEffect(use_skill_player, goal_player, skill_effect, back_msg)
                if ret == RET_ERROR:
                    return ret, msg
        elif skill_trigger == TRIGGER_ALL_EXCEPT_ME:  # 除了自己的其它人
            for player_id in self.player_list:
                if player_id == use_skill_player.user_id:
                    continue
                goal_player = self.getPlayerObj(player_id)
                ret, msg = self.skillEffect(use_skill_player, goal_player, skill_effect, back_msg)
                if ret == RET_ERROR:
                    return ret, msg
        elif skill_trigger == TRIGGER_NEAR:  # 离自己最近的目标
            goal_player = self.getNearPlayer(use_skill_player)
            ret, msg = self.skillEffect(use_skill_player, goal_player, skill_effect, back_msg)
            if ret == RET_ERROR:
                return ret, msg
        else:
            return RET_ERROR, '技能配置出错'

        return RET_SUCCESS, msg

    # 技能效果生效
    def skillEffect(self, use_skill_player: Role, goal_player: Role, skill_effect, back_msg: List):
        if goal_player.now_stage == NOW_STAGE_OUT:
            return

        use_player_name = uid2card(use_skill_player.user_id, self.user_card_dict)
        goal_player_name = uid2card(goal_player.user_id, self.user_card_dict)

        # 向目标移动
        if EFFECT_MOVE_GOAL in skill_effect:
            num = skill_effect[EFFECT_MOVE_GOAL][0]
            ignore_dist = skill_effect[EFFECT_MOVE_GOAL][1]

            # 向目标移动的效果，在触发时才计算攻击距离
            distance = use_skill_player.now_location - goal_player.now_location
            half_circle = len(self.runway) / 2
            dist = self.getTwoPlayerDist(use_skill_player, goal_player)
            if not ignore_dist and dist > use_skill_player.distance + num:
                return RET_ERROR, '攻击距离不够'

            if distance > 0:
                if distance > half_circle:
                    use_skill_player.locationChange(num, self.runway)
                else:
                    use_skill_player.locationChange(-num, self.runway)
            else:
                if abs(distance) < half_circle:
                    use_skill_player.locationChange(num, self.runway)
                else:
                    use_skill_player.locationChange(-num, self.runway)
            back_msg.append(f'{use_player_name}往离{goal_player_name}较近的方向移动了{num}步')

        # 攻击力改变
        if EFFECT_ATTACK in skill_effect:
            num = skill_effect[EFFECT_ATTACK]
            goal_player.attackChange(num)
            if num < 0:
                back_msg.append(f'{goal_player_name}降低了{abs(num)}点攻击力')
            else:
                back_msg.append(f'{goal_player_name}增加了{num}点攻击力')

        # 防御力改变
        if EFFECT_DEFENSIVE in skill_effect:
            num = skill_effect[EFFECT_DEFENSIVE]
            goal_player.defensiveChange(num)
            if num < 0:
                back_msg.append(f'{goal_player_name}降低了{abs(num)}点防御力')
            else:
                back_msg.append(f'{goal_player_name}增加了{num}点防御力')

        # 攻击距离改变
        if EFFECT_DISTANCE in skill_effect:
            num = skill_effect[EFFECT_DISTANCE]
            goal_player.distanceChange(num)
            if num < 0:
                back_msg.append(f'{goal_player_name}降低了{abs(num)}点攻击距离')
            else:
                back_msg.append(f'{goal_player_name}增加了{num}点攻击距离')

        # tp值改变
        if EFFECT_TP in skill_effect:
            num = skill_effect[EFFECT_TP]
            goal_player.tpChange(num)
            if num < 0:
                back_msg.append(f'{goal_player_name}降低了{abs(num)}点TP')
            else:
                back_msg.append(f'{goal_player_name}增加了{num}点TP')

        # 位置改变
        if EFFECT_MOVE in skill_effect:
            num = skill_effect[EFFECT_MOVE]
            goal_player.locationChange(num, self.runway)
            if num < 0:
                back_msg.append(f'{goal_player_name}后退了{abs(num)}步')
            else:
                back_msg.append(f'{goal_player_name}前进了{num}步')

        # 生命值改变
        if EFFECT_HEALTH in skill_effect:
            num = skill_effect[EFFECT_HEALTH][0]  # 基础数值
            addition = skill_effect[EFFECT_HEALTH][1]  # 加成比例
            is_real = skill_effect[EFFECT_HEALTH][2]  # 是否是真实伤害
            use_player_atk = use_skill_player.attack  # 自身攻击力
            goal_player_def = goal_player.defensive  # 目标防御力
            if num <= 0:  # 扣血
                num = abs(num) + use_player_atk * addition  # 计算加成后的数值
                # 如果是真实伤害则不计算目标的防御
                if not is_real:
                    num = hurt_defensive_calculate(num, goal_player_def)  # 计算目标防御力后的数值
                num = math.floor(num)  # 小数数值向下取整
                num = 0 - num  # 变回负数，代表扣血
            else:  # 回血
                num = num + use_player_atk * addition  # 计算加成后的数值

            goal_player.healthChange(num)

            if num < 0:
                back_msg.append(f'{goal_player_name}受到了{abs(num)}点伤害')
            else:
                back_msg.append(f'{goal_player_name}增加了{num}点生命值')

        # 通用击倒tp
        if goal_player.now_stage == NOW_STAGE_OUT:
            use_skill_player.tpChange(HIT_DOWN_TP, True)
            back_msg.append(f'[CQ:at,qq={goal_player.user_id}]出局')

        # 效果击倒tp
        if EFFECT_OUT_TP in skill_effect:
            if goal_player.now_stage == NOW_STAGE_OUT:
                num = skill_effect[EFFECT_OUT_TP]
                use_skill_player.tpChange(num, True)
                if num < 0:
                    back_msg.append(f'{goal_player_name}被击倒，{use_player_name}降低了{abs(num)}点TP')
                else:
                    back_msg.append(f'{goal_player_name}被击倒，{use_player_name}增加了{num}点TP')

        # 回合锁定效果
        if EFFECT_OUT_TURN in skill_effect:
            if goal_player.now_stage == NOW_STAGE_OUT:
                num = skill_effect[EFFECT_OUT_TURN]
                self.lock_turn = num
                back_msg.append(f'{use_player_name}锁定了{num}回合')

        if len(back_msg) == 0:
            back_msg.append('什么都没发生')
        return RET_SUCCESS, ''

    # 阶段提醒，丢色子/放技能阶段
    async def stageRemind(self, bot, ev: CQEvent):
        player = self.getNowTurnPlayerObj()
        stage = player.now_stage
        if stage == NOW_STAGE_DICE:
            await bot.send(ev, f'[CQ:at,qq={player.user_id}]的丢色子阶段(发送 丢色子)')
        elif stage == NOW_STAGE_SKILL:
            msg = [f'[CQ:at,qq={player.user_id}]的放技能阶段：\n(发送技能编号，如需选择目标则@目标)']
            skill_list = player.active_skills
            skill_num = 0
            for skill in skill_list:
                tp_cost = skill["tp_cost"]
                msg.append(f'  技能{skill_num + 1}:{skill["name"]}({tp_cost}TP):\n   {skill["text"]}')
                skill_num += 1
            msg.append('(发送"跳过"跳过出技能阶段)')
            await bot.send(ev, "\n".join(msg))

    # 获取基础图片
    def getBaseImage(self):
        return self.base_image

    # 获取当前状态图片
    def getNowImage(self):
        return self.now_image

    # 获取当前玩家数量
    def getPlayerNum(self):
        return len(self.player_list)

    def getPlayerObj(self, player_id):
        player: Role = self.player_list[player_id]
        return player

    # 获取当前回合的玩家对象
    def getNowTurnPlayerObj(self):
        for player_id in self.player_list:
            player = self.getPlayerObj(player_id)
            if player.player_num == self.now_turn:
                return player

    # 获取两个玩家之间的距离
    def getTwoPlayerDist(self, p1: Role, p2: Role):
        dist = abs(p1.now_location - p2.now_location)
        half_circle = len(self.runway) / 2
        if abs(dist) > half_circle:
            dist = half_circle - abs(half_circle - dist)
        return dist

    # 获取离玩家最近的一个目标玩家id
    def getNearPlayer(self, own_player: Role):
        dist_list = []  # 距离列表 [[玩家id,距离],[]]
        for player_id in self.player_list:
            player = self.getPlayerObj(player_id)
            if player == own_player:
                continue
            if player.now_stage == NOW_STAGE_OUT:
                continue
            dist_list.append([player.user_id, self.getTwoPlayerDist(own_player, player)])
        # 极其低效的排序算法，时间复杂度为O(n^2)，数据量小，懒得改了_(:3)∠)_
        for i in range(len(dist_list)):  # 类似插入排序，从小到大
            save_info = dist_list[i]
            save_location = -1
            del dist_list[i]
            for j in range(len(dist_list)):
                comp_info = dist_list[j]
                if save_info[1] > comp_info[1]:
                    save_location = j
            dist_list.insert(save_location + 1, save_info)
        return self.getPlayerObj(dist_list[0][0])

    # 刷新当前状态图片
    def refreshNowImageStatu(self):
        self.now_image = self.base_image.copy()
        self.now_draw = ImageDraw.Draw(self.now_image)

        # 遍历玩家列表，刷新玩家当前状态
        num = 0
        for player_id in self.player_list:
            offset_x, offset_y = 0, 0
            if num == 1:
                offset_x = 1
            elif num == 2:
                offset_y = 1
            elif num == 3:
                offset_x, offset_y = 1, 1

            player = self.getPlayerObj(player_id)
            health_line_length = 96 * (player.now_health / player.max_health)
            tp_line_length = 96 * (player.tp / MAX_TP)

            self.statuLineFill(health_line_length, offset_x, offset_y, -16, COLOR_CAM_GREEN)  # 血条填充
            self.statuLineFill(tp_line_length, offset_x, offset_y, 1, COLOR_CAM_BLUE)  # tp条填充
            self.roleStatuText(offset_x, offset_y, -23, text=str(player.now_health))  # 血条数值
            self.roleStatuText(offset_x, offset_y, -5, text=str(player.tp))  # tp条数值
            self.playerInfoText(offset_x, offset_y, 28, text=f'dist   ：{player.distance}')  # 攻击距离
            self.playerInfoText(offset_x, offset_y, 12,
                                text=f'name：{uid2card(player.user_id, self.user_card_dict)}')  # 玩家名字

            if self.now_turn == player.player_num:  # 当前回合的玩家，头像框为绿色
                self.drawBox(100, 100, self.grid_size * 2 + offset_x * 200, self.grid_size * 1.5 + offset_y * 190,
                             COLOR_GREEN, is_now=True)
            if player.now_stage == NOW_STAGE_OUT:  # 已出局的玩家，头像框为黑色，且跑道旁不显示头像
                self.drawBox(100, 100, self.grid_size * 2 + offset_x * 200, self.grid_size * 1.5 + offset_y * 190,
                             COLOR_BLACK, is_now=True)
            else:
                self.roleIconLocation(player.role_icon, player.now_location)  # 显示玩家角色位置
            num += 1

    # 显示初始化
    def displayInit(self):
        j = 0
        for i in range(self.across_range_y + 1):  # 画横线
            self.draw.line((0 + OFFSET_X, j + OFFSET_Y) +
                           (self.grid_size * self.vertical_range_x + OFFSET_X, j + OFFSET_Y),
                           fill=COLOR_BLACK, width=RUNWAY_LINE_WDITH)
            j += self.grid_size
        j = 0
        for i in range(self.vertical_range_x + 1):  # 画竖线
            self.draw.line((j + OFFSET_X, 0 + OFFSET_Y) +
                           (j + OFFSET_X, self.grid_size * self.across_range_y + OFFSET_Y),
                           fill=COLOR_BLACK, width=RUNWAY_LINE_WDITH)
            j += self.grid_size
        # 中间遮掩
        self.draw.rectangle(
            (RUNWAY_LINE_WDITH + self.grid_size + OFFSET_X - 1, RUNWAY_LINE_WDITH + self.grid_size + OFFSET_Y - 1,
             self.grid_size - (RUNWAY_LINE_WDITH / 2) + (self.vertical_range_x - 2) * self.grid_size + OFFSET_X,
             self.grid_size - (RUNWAY_LINE_WDITH / 2) + (self.across_range_y - 2) * self.grid_size + OFFSET_Y),
            fill=COLOR_WRITE)
        # 画框
        for i in range(2):
            for j in range(2):
                self.drawBox(100, 100, self.grid_size * 2 + i * 200, self.grid_size * 1.5 + j * 190, COLOR_RED)  # 头像框
                self.drawBox(100, 10, self.grid_size * 2 + i * 200, self.grid_size * 4 + j * 190 - 17, COLOR_BLACK,
                             STATU_LINE_WDITH)  # 血条框
                self.drawBox(100, 10, self.grid_size * 2 + i * 200, self.grid_size * 4 + j * 190, COLOR_BLACK,
                             STATU_LINE_WDITH)  # TP框
        # 填充跑道事件文字
        self.fillCaseText()

    # 画盒子（画框）
    def drawBox(self, length, width, offset_x, offset_y, color=COLOR_BLACK, line_width=RUNWAY_LINE_WDITH, is_now=False):
        draw = self.draw
        if is_now:
            draw = self.now_draw
        draw.line(((OFFSET_X + offset_x, OFFSET_Y + offset_y),
                   (OFFSET_X + offset_x, OFFSET_Y + width + offset_y),
                   (OFFSET_X + length + offset_x, OFFSET_Y + width + offset_y),
                   (OFFSET_X + length + offset_x, OFFSET_Y + offset_y),
                   (OFFSET_X + offset_x, OFFSET_Y + offset_y)),
                  fill=color, width=line_width)

    # 填充跑道事件文字
    def fillCaseText(self):
        i = 0
        for runway in self.runway:
            runway_case = RUNWAY_CASE[runway["case"]]
            name = runway_case["name"]
            color = runway_case["color"]
            if i <= 9:
                self.fillText(i, 0, color, name)
            elif i <= 18:
                self.fillText(9, i - 9, color, name)
            elif i <= 27:
                self.fillText(9 - (i - 9 * 2), 9, color, name)
            else:
                self.fillText(0, 9 - (i - 9 * 3), color, name)
            i += 1

    # 同上，封装一下
    def fillText(self, grid_x, grid_y, textColor=COLOR_BLACK, text=''):
        self.draw.text((grid_x * self.grid_size + OFFSET_X + 10, grid_y * self.grid_size + OFFSET_Y + 5),
                       text, font=self.runwayTextFont, fill=textColor)

    # 状态条填充   最大长度96  血条offset填-16，tp条填1
    def statuLineFill(self, length, offset_x, offset_y, offset, color=COLOR_BLACK, width=8):
        self.now_draw.rectangle((OFFSET_X + self.grid_size * 2 + offset_x * 200 + 2,
                                 OFFSET_Y + self.grid_size * 4 + offset_y * 190 + offset,
                                 OFFSET_X + length + self.grid_size * 2 + offset_x * 200 + 2,
                                 OFFSET_Y + width + self.grid_size * 4 + offset_y * 190 + offset),
                                fill=color)

    # 角色当前状态数字（血量/tp）
    def roleStatuText(self, offset_x, offset_y, offset, textColor=COLOR_BLACK, text=''):
        self.now_draw.text((OFFSET_X + 100 + self.grid_size * 2 + offset_x * 200 + 2,
                            OFFSET_Y + self.grid_size * 4 + offset_y * 190 + offset),
                           text, font=self.font, fill=textColor)

    # 玩家信息文字
    def playerInfoText(self, offset_x, offset_y, offset, textColor=COLOR_BLACK, text=''):
        self.now_draw.text((OFFSET_X + self.grid_size * 2 + offset_x * 200 + 2,
                            OFFSET_Y + self.grid_size * 4 + offset_y * 190 + offset),
                           text, font=self.font, fill=textColor)

    # 角色头像位置
    def roleIconLocation(self, icon, location):
        small_icon = icon.resize((25, 25))
        if location <= 9:
            self.now_image.paste(small_icon, (OFFSET_X + 14 + self.grid_size * location,
                                              OFFSET_Y - 30))
        elif location <= 18:
            self.now_image.paste(small_icon, (OFFSET_X + 10 + self.grid_size * 10,
                                              OFFSET_Y + 14 + self.grid_size * (location - 9)))
        elif location <= 27:
            self.now_image.paste(small_icon, (OFFSET_X + 14 + self.grid_size * (9 - (location - 9 * 2)),
                                              OFFSET_Y + 10 + self.grid_size * 10))
        else:
            self.now_image.paste(small_icon, (OFFSET_X - 30,
                                              OFFSET_Y + 14 + self.grid_size * (9 - (location - 9 * 3))))


# 管理器
class manager:
    def __init__(self):
        self.playing: List[PCRScrimmage] = {}

    def is_playing(self, gid):
        return gid in self.playing

    def start(self, gid, uid):
        return PCRScrimmage(gid, self, uid)

    def get_game(self, gid):
        return self.playing[gid] if gid in self.playing else None


mgr = manager()
WAIT_TIME = 3
PROCESS_WAIT_TIME = 1


@sv.on_fullmatch('创建大乱斗')
async def game_create(bot, ev: CQEvent):
    if mgr.is_playing(ev.group_id):
        await bot.finish(ev, '游戏仍在进行中…')

    image_path = R.img(f'{IMAGE_PATH}/{ev.group_id}.jpg').path
    if os.path.exists(image_path):
        os.remove(image_path)
    gid, uid = ev.group_id, ev.user_id

    with mgr.start(gid, uid) as scrimmage:
        await bot.send(ev, f'大乱斗房间已创建，等待加入中。。。\n当前人数({scrimmage.getPlayerNum()}/{MAX_PLAYER})\n（发送“加入大乱斗”加入）')
        scrimmage.user_card_dict = await get_user_card_dict(bot, gid)

        while True:  # 从等待到正式开始的循环等待
            await asyncio.sleep(WAIT_TIME)
            if scrimmage.now_statu == NOW_STATU_OPEN:
                scrimmage.gameOpen()
                img = scrimmage.getNowImage()
                img.save(image_path)
                await bot.send(ev, R.img(image_path).cqcode)
                await asyncio.sleep(PROCESS_WAIT_TIME)
                await scrimmage.stageRemind(bot, ev)
                break
            elif scrimmage.now_statu == NOW_STATU_END:
                break

        if scrimmage.now_statu == NOW_STATU_OPEN:
            while True:  # 开始后的循环等待
                await asyncio.sleep(WAIT_TIME)
                if (scrimmage.now_statu == NOW_STATU_END or
                        scrimmage.now_statu == NOW_STATU_WIN):
                    break
        if scrimmage.now_statu == NOW_STATU_WIN:
            msg = ['大乱斗已结束，排名如下：']
            for i in range(len(scrimmage.rank)):
                user_card = uid2card(scrimmage.rank[i + 1], scrimmage.user_card_dict)
                msg.append(f'第{i + 1}名：{user_card}')
            await bot.send(ev, '\n'.join(msg))
        else:
            await bot.send(ev, f'游戏结束')


@sv.on_fullmatch('加入大乱斗')
async def game_join(bot, ev: CQEvent):
    gid, uid = ev.group_id, ev.user_id
    scrimmage = mgr.get_game(gid)
    if not scrimmage or scrimmage.now_statu != NOW_STATU_WAIT:
        return
    if uid in scrimmage.player_list:
        await bot.finish(ev, '您已经在准备房间里了', at_sender=True)
    if scrimmage.getPlayerNum() >= MAX_PLAYER:
        await bot.finish(ev, '人数已满，无法继续加入', at_sender=True)

    scrimmage.ready(uid)

    msg = []
    for user_id in scrimmage.player_list:
        user_card = uid2card(user_id, scrimmage.user_card_dict)
        msg.append(user_card)
    await bot.send(ev, f'已加入\n当前人数({scrimmage.getPlayerNum()}/{MAX_PLAYER})\n{" ".join(msg)}')
    if scrimmage.getPlayerNum() == MAX_PLAYER:
        await bot.send(ev, '人数已满，可开始游戏。\n（发送“开始大乱斗”开始）')


@sv.on_fullmatch('开始大乱斗')
async def game_start(bot, ev: CQEvent):
    gid, uid = ev.group_id, ev.user_id
    scrimmage = mgr.get_game(gid)
    if not scrimmage or scrimmage.now_statu != NOW_STATU_WAIT:
        return
    if not uid == scrimmage.room_master:
        await bot.finish(ev, '只有房主才能开始', at_sender=True)
    if scrimmage.getPlayerNum() < 2:
        await bot.finish(ev, '要两个人以上才能开始', at_sender=True)

    scrimmage.now_statu = NOW_STATU_SELECT_ROLE
    role_list = '游戏开始，请选择角色，当前可选角色：\n（'
    for role in ROLE.values():
        role_list += f'{role["name"]} '
    role_list += ')\n输入“角色详情 角色名” 可查看角色属性和技能\n（所有人都选择角色后自动开始）'
    await bot.send(ev, role_list)


@sv.on_message()  # 选择角色
async def select_role(bot, ev: CQEvent):
    gid, uid = ev.group_id, ev.user_id
    scrimmage = mgr.get_game(gid)
    if not scrimmage or scrimmage.now_statu != NOW_STATU_SELECT_ROLE:
        return
    # 已加入房间的玩家才能选择角色
    if uid not in scrimmage.player_list:
        return

    image_path = R.img(f'{IMAGE_PATH}/{ev.group_id}.png').path

    character = chara.fromname(ev.message.extract_plain_text())
    if character.id != chara.UNKNOWN and character.id in ROLE:
        player = scrimmage.getPlayerObj(uid)
        player.initData(character.id, character, scrimmage)

        img = player.role_icon
        img.save(image_path)
        await bot.send(ev, f"您选择的角色是：{player.name}\n{R.img(image_path).cqcode}", at_sender=True)

        if scrimmage.checkAllPlayerSelectRole():
            await asyncio.sleep(PROCESS_WAIT_TIME)
            await bot.send(ev, "所有人都选择了角色，大乱斗即将开始！\n碾碎他们")
            await asyncio.sleep(PROCESS_WAIT_TIME)
            scrimmage.now_statu = NOW_STATU_OPEN


@sv.on_fullmatch(('扔色子', '扔骰子', '丢色子', '丢骰子', '丢', '扔'))
async def throw_dice(bot, ev: CQEvent):
    gid, uid = ev.group_id, ev.user_id

    scrimmage = mgr.get_game(gid)
    if not scrimmage or scrimmage.now_statu != NOW_STATU_OPEN:
        return
    # 已加入房间的玩家才能丢色子
    if uid not in scrimmage.player_list:
        return
    # 不是当前回合的玩家无法丢色子
    if scrimmage.getNowTurnPlayerObj().user_id != uid:
        return
    # 当前回合不是丢色子状态无法丢色子
    if scrimmage.getPlayerObj(uid).now_stage != NOW_STAGE_DICE:
        return

    step = random.choice(range(1, 6))
    await bot.send(ev, '色子结果为：' + str(step))
    await scrimmage.throwDice(uid, step, bot, ev)
    scrimmage.refreshNowImageStatu()

    image_path = R.img(f'{IMAGE_PATH}/{ev.group_id}.jpg').path
    img = scrimmage.getNowImage()
    img.save(image_path)
    await bot.send(ev, R.img(image_path).cqcode)
    await asyncio.sleep(PROCESS_WAIT_TIME)
    await scrimmage.stageRemind(bot, ev)


@sv.on_message()  # 使用技能
async def use_skill(bot, ev: CQEvent):
    gid, uid = ev.group_id, ev.user_id

    msg_text = ev.raw_message
    match = re.match(r'^(\d+)( |) *(?:\[CQ:at,qq=(\d+)])?', msg_text)
    if not match and msg_text != '跳过':
        return
    scrimmage = mgr.get_game(gid)
    if not scrimmage or scrimmage.now_statu != NOW_STATU_OPEN:
        return
    # 已加入房间的玩家才能释放技能
    if uid not in scrimmage.player_list:
        return
    # 不是当前回合的玩家无法释放技能
    if scrimmage.getNowTurnPlayerObj().user_id != uid:
        return
    # 当前回合不是放技能状态无法放技能
    if scrimmage.getPlayerObj(uid).now_stage != NOW_STAGE_SKILL:
        return

    skill_id = ''
    goal_player_id = ''
    if match:
        skill_id = match.group(1)
        goal_player_id = match.group(3) or '0'
    else:
        skill_id = '0'
        goal_player_id = '0'

    ret = await scrimmage.useSkill(int(skill_id), uid, int(goal_player_id), bot, ev)
    if ret == RET_ERROR:
        return

    image_path = R.img(f'{IMAGE_PATH}/{ev.group_id}.jpg').path
    img = scrimmage.getNowImage()
    img.save(image_path)
    await bot.send(ev, R.img(image_path).cqcode)
    await asyncio.sleep(PROCESS_WAIT_TIME)
    await scrimmage.stageRemind(bot, ev)


@sv.on_fullmatch(('认输', '投降', '不玩了'))
async def throw_dice(bot, ev: CQEvent):
    gid, uid = ev.group_id, ev.user_id

    scrimmage = mgr.get_game(gid)
    if not scrimmage or scrimmage.now_statu != NOW_STATU_OPEN:
        return
    # 已加入房间的玩家才能投降
    if uid not in scrimmage.player_list:
        return
    # 不是当前回合的玩家无法投降
    if scrimmage.getNowTurnPlayerObj().user_id != uid:
        return

    player = scrimmage.getPlayerObj(uid)
    scrimmage.outDispose(player)
    await bot.send(ev, f'{uid2card(uid, scrimmage.user_card_dict)}已投降')
    if scrimmage.now_statu == NOW_STATU_OPEN:
        scrimmage.turnChange()
        scrimmage.refreshNowImageStatu()
        image_path = R.img(f'{IMAGE_PATH}/{ev.group_id}.jpg').path
        img = scrimmage.getNowImage()
        img.save(image_path)
        await bot.send(ev, R.img(image_path).cqcode)
        await asyncio.sleep(PROCESS_WAIT_TIME)
        await scrimmage.stageRemind(bot, ev)


@sv.on_fullmatch('查看属性')
async def check_property(bot, ev: CQEvent):
    gid, uid = ev.group_id, ev.user_id

    scrimmage = mgr.get_game(gid)
    if not scrimmage or scrimmage.now_statu != NOW_STATU_OPEN:
        return
    player = scrimmage.getPlayerObj(uid)
    msg = player.checkStatu(scrimmage)
    await bot.send(ev, "\n".join(msg))


@sv.on_rex(r'^角色详情( |)([\s\S]*)')
async def check_role(bot, ev: CQEvent):
    match = ev['match']
    if not match:
        return

    role_name = match.group(2)
    character = chara.fromname(role_name)
    if character.id != chara.UNKNOWN and character.id in ROLE:
        role_info = ROLE[character.id]
        msg = [f"名字：{role_info['name']}",
               f"生命值：{role_info['health']}",
               f"TP：{role_info['tp']}",
               f"攻击距离：{role_info['distance']}",
               f"攻击力：{role_info['attack']}",
               f"防御力：{role_info['defensive']}",
               f"技能："]
        for skill in role_info['active_skills']:
            msg.append(f"{skill['name']}({skill['tp_cost']}tp)：{skill['text']}")
        return await bot.send(ev, "\n".join(msg))

    await bot.send(ev, '不存在的角色')


@sv.on_fullmatch('结束大乱斗')
async def game_end(bot, ev: CQEvent):
    gid, uid = ev.group_id, ev.user_id

    scrimmage = mgr.get_game(gid)
    if not scrimmage or scrimmage.now_statu == NOW_STATU_END:
        return
    if not priv.check_priv(ev, priv.ADMIN) and not uid == scrimmage.room_master:
        await bot.finish(ev, '只有群管理或房主才能强制结束', at_sender=True)

    scrimmage.now_statu = NOW_STATU_END
    await bot.send(ev, f"您已强制结束大乱斗，请等待结算")


@sv.on_fullmatch(('PCR大乱斗', 'pcr大乱斗', '大乱斗帮助', 'PCR大乱斗帮助', 'pcr大乱斗帮助'))
async def game_help(bot, ev: CQEvent):
    msg = '''《PCR大乱斗帮助》
    基础命令：
    1、大乱斗规则
    可查看大乱斗相关规则
    2、大乱斗角色
    可查看所有可用角色
    3、角色详情 （角色名）
    如：角色详情 黑猫
    可查看角色的基础属性和技能
    4、结束大乱斗
    可以强制结束正在进行的大乱斗游戏
    （该命令只有管理员和房主可用）
    一、创建阶段：
    1、创建大乱斗
    2、加入大乱斗
    3、开始大乱斗
    二、选择角色阶段：
    1、（角色名）
    如：凯露 / 黑猫
    （名字和外号都行）
    三、对战阶段：
    1、丢色子
    2、（技能编号） @xxx
    如：1 @xxx
    发送技能编号并@目标，如果这个技能不需要指定目标，直接发送技能编号即可
    3、查看属性
    可查看自己当前角色详细属性
    4、投降 / 认输
    '''
    await bot.send(ev, msg)


@sv.on_fullmatch('大乱斗规则')
async def game_help_all_role(bot, ev: CQEvent):
    msg = '''《PCR大乱斗规则》
1、和大富翁类似，一个正方形环形跑道，跑道上有多个事件，通过丢色子走到特定的位置触发事件
2、可多个玩家同时玩，最多4个，最少2个。每个玩家可选择一个pcr里的角色，不同的角色有不同的属性、技能
3、角色有tp值，每次投掷色子，所有玩家都会增加tp值，tp达到技能的要求可释放技能
4、需要选择目标的技能释放范围有距离限制，以角色属性的攻击距离为准
5、避免游戏时长过长，每4回合增加一次攻击力和攻击距离
6、可投降
7、活到最后获胜（吃鸡？）
'''
    await bot.send(ev, msg)


@sv.on_fullmatch('大乱斗角色')
async def game_help_rule(bot, ev: CQEvent):
    msg = '当前可选角色有：\n'
    for role in ROLE.values():
        msg += f'{role["name"]} '
    msg += f'\n共{len(ROLE)}位角色'
    await bot.send(ev, msg)
