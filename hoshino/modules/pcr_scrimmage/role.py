##可用角色

"""
##可用角色可自定义增加，详细看下面

基础属性：
	name			名字		string
	health			生命值		number
	distance		攻击距离	number
	attack			攻击力		number
	defensive		防御力		number
	tp				能量值		number
	active_skills	主动技能	list[dict]
	passive_skills	被动技能	list[dict] 依赖主动技能
		被动技能的主要作用，是为了让一个主动技能可以同时选择不同的触发对象
		例如：yly，砍别人一刀自己掉血
		被动技能优先级比主动高，可以先对自身增加攻击力后再进行攻击
		（其实，把这个 “被动技能” 说成是 “附带效果” 也可以，单纯为了区分不同的触发对象而已）

技能：
	name			技能名称	string
	text			技能描述	string
	tp_cost			消耗tp		number
	effect			技能效果	list[dict]
	trigger			触发对象	string
	passive			被动		list[number] 数字对应基础属性的passive_skill

	################（技能效果可增加，增加后在 skillEffect() 里做处理）################
	效果effect：(可选单个或多个) (被动技能：对自己和对目标的效果要分开)
		health_change			生命值改变，正数为回血，负数为造成伤害	tuple元组 (数值，加成比例, 是否是真实伤害)
		defensive_change		防御改变，正数为增加，负数为减少
		distance_change
		attack_change
		tp_change

		move				移动，正数为前进负数为后退	number
		move_goal			向目标移动（一个技能有多个效果且包括向目标移动，向目标移动效果必须最先触发）
							这个效果必须放在被动
		ignore_dist			无视距离，参数填啥都行，不会用到

		make_it_out_tp		令目标出局时tp变动
		make_it_out_turn	令目标出局时锁定回合

	################触发对象可继续增加，添加后在 skillTrigger() 里做处理################
	触发对象trigger：
		select				选择目标

		all					对所有人有效(包括自己)
		all_except_me		对所有人有效(除了自己)
		me					只对自己有效

		near				离自己最近

"""


EFFECT_HEALTH = "health_change"         # 生命值改变，正数为回血，负数为造成伤害		tuple元组 (数值，加成比例, 是否是真实伤害)

EFFECT_DEFENSIVE = "defensive_change"   # 防御改变，正数为增加，负数为减少 			number ↓同理
EFFECT_DISTANCE = "distance_change"
EFFECT_ATTACK = "attack_change"
EFFECT_TP = "tp_change"  # ↑同理

EFFECT_MOVE = "move"  # 移动，正数为前进负数为后退（触发跑道事件）	number
EFFECT_MOVE_GOAL = "move_goal"  # 向目标移动（一个技能有多个效果且包括向目标移动，向目标移动效果必须最先触发） tuple元组(移动距离，是否无视攻击范围)
# 这个效果必须放在被动（不触发跑道事件）
EFFECT_IGNORE_DIST = "ignore_dist"  # 无视距离效果，参数填啥都行，不会用到

EFFECT_OUT_TP = "make_it_out_tp"  # 令目标出局时tp变动		number
EFFECT_OUT_TURN = "make_it_out_turn"  # 令目标出局时锁定回合	number（锁定回合：不会切换到下一个玩家，当前玩家继续丢色子和放技能）

TRIGGER_SELECT = "select"  # 选择目标
TRIGGER_ALL = "all"  # 对所有人有效(包括自己)
TRIGGER_ALL_EXCEPT_ME = "all_except_me"  # 对所有人有效(除了自己)
TRIGGER_ME = "me"  # 只对自己有效
TRIGGER_NEAR = "near"  # 离自己最近的目标

# 角色字典
ROLE = {
    # 注意 :id要和 _pcr_data.py 里对应角色一样
    1060: {
        "name": "凯露",

        "health": 800,
        "distance": 10,
        "attack": 100,
        "defensive": 60,
        "tp": 0,

        "active_skills": [
            {
                "name": "闪电球",
                "text": "对目标造成100(+0.5攻击力)伤害并减少50防御，自身增加20点攻击力",
                "tp_cost": 20,
                "trigger": TRIGGER_SELECT,
                "passive": [0],
                "effect": {
                    EFFECT_HEALTH: (-100, 0.5, False),
                    EFFECT_DEFENSIVE: -50,
                }
            },
            {
                "name": "格林爆裂",
                "text": "对所有人造成100(+1.5攻击力)伤害",
                "tp_cost": 50,
                "trigger": TRIGGER_ALL_EXCEPT_ME,
                "passive": [],
                "effect": {
                    EFFECT_HEALTH: (-100, 1.5, False),
                }
            }
        ],
        "passive_skills": [
            {
                "trigger": TRIGGER_ME,
                "effect": {
                    EFFECT_ATTACK: 20,
                }
            }
        ]
    },
    1059: {
        "name": "可可萝",

        "health": 1000,
        "distance": 6,
        "attack": 50,
        "defensive": 70,
        "tp": 0,

        "active_skills": [
            {
                "name": "三连击",
                "text": "向目标移动3格，并对目标造成100(+1.0攻击力)伤害",
                "tp_cost": 20,
                "trigger": TRIGGER_SELECT,
                "passive": [0],
                "effect": {
                    EFFECT_HEALTH: (-100, 1, False)
                }
            },
            {
                "name": "光之守护",
                "text": "自身回复250点生命值，并增加50点攻击力",
                "tp_cost": 50,
                "trigger": TRIGGER_ME,
                "passive": [],
                "effect": {
                    EFFECT_HEALTH: (250, 0, False),
                    EFFECT_ATTACK: 50
                }
            }
        ],
        "passive_skills": [
            {
                "trigger": TRIGGER_SELECT,
                "effect": {
                    EFFECT_MOVE_GOAL: (3, False),
                }
            }
        ]
    },
    1058: {
        "name": "佩可",

        "health": 1500,
        "distance": 5,
        "attack": 60,
        "defensive": 100,
        "tp": 0,

        "active_skills": [
            {
                "name": "普通攻击",
                "text": "对目标造成0(+1.0攻击力)伤害",
                "tp_cost": 0,
                "trigger": TRIGGER_SELECT,
                "passive": [],

                "effect": {
                    EFFECT_HEALTH: (0, 1, False)
                }
            },
            {
                "name": "超大饭团",
                "text": "回复自身150生命值",
                "tp_cost": 20,
                "trigger": TRIGGER_ME,
                "passive": [],

                "effect": {
                    EFFECT_HEALTH: (100, 0, False),
                }
            },
            {
                "name": "公主突袭",
                "text": "向目标移动5格，对目标造成150(+1.0攻击力)伤害，并增加自身100防御",
                "tp_cost": 50,
                "trigger": TRIGGER_SELECT,
                "passive": [0, 1],  # 一个技能有多个效果且包括向目标移动，向目标移动效果必须最先触发

                "effect": {
                    EFFECT_HEALTH: (-150, 1.0, False),
                }
            }
        ],
        "passive_skills": [
            {  # 一个技能有多个效果且包括向目标移动，向目标移动效果必须最先触发
                "trigger": TRIGGER_SELECT,
                "effect": {
                    EFFECT_MOVE_GOAL: (5, False),
                }
            },
            {
                "trigger": TRIGGER_ME,
                "effect": {
                    EFFECT_DEFENSIVE: 100,
                }
            }
        ]
    },
    1003: {
        "name": "怜",
        "health": 900,
        "distance": 5,
        "attack": 100,
        "defensive": 70,
        "tp": 0,

        "active_skills": [
            {
                "name": "破甲突刺",
                "text": "无视距离，对离自己最近的目标造成100(+1.0攻击力)伤害，并降低目标50点防御力",
                "tp_cost": 20,
                "trigger": TRIGGER_NEAR,
                "passive": [],

                "effect": {
                    EFFECT_HEALTH: (-100, 1.0, False),
                    EFFECT_DEFENSIVE: -50
                }
            },
            {
                "name": "极·鬼剑术-暴风式",
                "text": "对自己以外的所有人造成200(+1.0 攻击力)真实伤害",
                "tp_cost": 60,
                "trigger": TRIGGER_ALL_EXCEPT_ME,
                "passive": [],

                "effect": {
                    EFFECT_HEALTH: (-200, 1.0, True)
                }
            }
        ],
        "passive_skills": []
    },
    1002: {
        "name": "优衣",
        "health": 1000,
        "distance": 8,
        "attack": 80,
        "defensive": 60,
        "tp": 10,

        "active_skills": [
            {
                "name": "花瓣射击",
                "text": "对目标造成100(+1.5攻击力)伤害，并降低目标10点攻击力和10点TP",
                "tp_cost": 20,
                "trigger": TRIGGER_SELECT,
                "passive": [],

                "effect": {
                    EFFECT_HEALTH: (-100, 1.5, False),
                    EFFECT_ATTACK: -10,
                    EFFECT_TP: -10
                }
            },
            {
                "name": "全体治愈",
                "text": "全体回复100生命值，自己额外回复100生命值，除自己外减少3点攻击距离",
                "tp_cost": 50,
                "trigger": TRIGGER_ALL,
                "passive": [0, 1],

                "effect": {
                    EFFECT_HEALTH: (100, 0, False)
                }
            }
        ],
        "passive_skills": [
            {
                "trigger": TRIGGER_ALL_EXCEPT_ME,
                "effect": {
                    EFFECT_DISTANCE: -3,
                }
            },
            {
                "trigger": TRIGGER_ME,
                "effect": {
                    EFFECT_HEALTH: (100, 0, False)
                }
            }
        ],
    },
    1001: {
        "name": "日和莉",
        "health": 900,
        "distance": 5,
        "attack": 100,
        "defensive": 60,
        "tp": 0,

        "active_skills": [
            {
                "name": "普通攻击",
                "text": "对目标造成0(+1.0攻击力)伤害",
                "tp_cost": 0,
                "trigger": TRIGGER_SELECT,
                "passive": [],

                "effect": {
                    EFFECT_HEALTH: (0, 1, False)
                }
            },
            {
                "name": "勇气迸发",
                "text": "自身增加50点攻击力和1点攻击距离",
                "tp_cost": 20,
                "trigger": TRIGGER_ME,
                "passive": [],

                "effect": {
                    EFFECT_ATTACK: 70,
                    EFFECT_DISTANCE: 1
                }
            },
            {
                "name": "日和莉烈焰冲击",
                "text": "对目标造成300(+2.0攻击力)伤害，若目标被击倒，自身回复60点tp并继续下一回合",
                "tp_cost": 100,
                "trigger": TRIGGER_SELECT,
                "passive": [],

                "effect": {
                    EFFECT_HEALTH: (-300, 2, False),
                    EFFECT_OUT_TP: 60,
                    EFFECT_OUT_TURN: 1
                }
            }
        ],
        "passive_skills": []

    }

}
