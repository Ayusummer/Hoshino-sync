import time

from nonebot import get_bot

from .data import Question

from hoshino import config

bot = get_bot()
answers = {}

ADMIN_QQID = config.SUPERUSERS[0]


def union(group_id, user_id):
    return (group_id << 32) | user_id


# recovery from database
for qu in Question.select():
    if qu.quest not in answers:
        answers[qu.quest] = {}
    answers[qu.quest][union(qu.rep_group, qu.rep_member)] = qu.answer

# xqa_admin_list = ['1369661643']


@bot.on_message("group")
async def handle(context):
    message = context["raw_message"]
    if message.startswith("我问"):
        msg = message[2:].split("你答", 1)
        if len(msg) == 1:
            return {"reply": "发送“我问xxx你答yyy”我才能记住", "at_sender": False}
        q, a = msg
        if q not in answers:
            answers[q] = {}
        answers[q][union(context["group_id"], context["user_id"])] = a
        Question.replace(
            quest=q,
            rep_group=context["group_id"],
            rep_member=context["user_id"],
            answer=a,
            creator=context["user_id"],
            create_time=time.time(),
        ).execute()
        return {"reply": "好的我记住了", "at_sender": False}
    elif message.startswith("大家问") or message.startswith("有人问"):
        if context["sender"]["role"] == "member" and context["user_id"] != ADMIN_QQID:
            # if str(context['user_id']) not in xqa_admin_list:
            return {"reply": f"只有管理员才可以用“{message[:3]}”", "at_sender": False}
        msg = message[3:].split("你答", 1)
        if len(msg) == 1:
            return {"reply": f"发送“{message[:3]}xxx你答yyy”我才能记住", "at_sender": False}
        q, a = msg
        if q not in answers:
            answers[q] = {}
        answers[q][union(context["group_id"], 1)] = a
        Question.replace(
            quest=q,
            rep_group=context["group_id"],
            rep_member=1,
            answer=a,
            creator=context["user_id"],
            create_time=time.time(),
        ).execute()
        return {"reply": "好的我记住了", "at_sender": False}
    elif message.startswith("不要回答"):
        q = context["raw_message"][4:]
        ans = answers.get(q)
        if ans is None:
            return {"reply": "我不记得有这个问题", "at_sender": False}

        specific = union(context["group_id"], context["user_id"])
        if a := ans.get(specific):
            Question.delete().where(
                Question.quest == q,
                Question.rep_group == context["group_id"],
                Question.rep_member == context["user_id"],
            ).execute()
            del ans[specific]
            if not ans:
                del answers[q]
            return {"reply": f"我不再回答“{a}”了", "at_sender": False}

        if context["sender"]["role"] == "member":
            return {"reply": "只有管理员可以删除别人的问题", "at_sender": False}

        wild = union(context["group_id"], 1)
        if a := ans.get(wild):
            Question.delete().where(
                Question.quest == q,
                Question.rep_group == context["group_id"],
                Question.rep_member == 1,
            ).execute()
            del ans[wild]
            if not ans:
                del answers[q]
            return {"reply": f"我不再回答“{a}”了", "at_sender": False}


# 看看有人问/大家问
@bot.on_message("group")
async def look(context):
    message = context["raw_message"]
    if message.startswith("看看有人问") or message.startswith("看看大家问"):
        # 从数据库中查看该群设置的有人问/大家问 的问题, 无需管理员权限
        group_id = context["group_id"]
        # 取出数据库中所有 rep_member 为 1 且 rep_group 为 group_id 的 quest 字段
        quests = Question.select(Question.quest).where(
            Question.rep_member == 1, Question.rep_group == group_id
        )
        # 如果没有设置有人问/大家问, 则返回提示
        if not quests:
            ans = "该群没有设置全局问题"
            return {"reply": ans, "at_sender": False}
        # 如果有设置有人问/大家问, 则返回所有问题
        ans = "该群设置的全局问题有: " + "| ".join(q.quest for q in quests)
        return {"reply": ans, "at_sender": False}


# 看看我问
@bot.on_message("group")
async def look_myself(context):
    message = context["raw_message"]
    if message.startswith("看看我问"):
        # 从数据库中查看该群设置的我问 的问题, 无需管理员权限
        group_id = context["group_id"]
        user_id = context["user_id"]
        # 取出数据库中所有 rep_member 为 user_id 且 rep_group 为 group_id 的 quest 字段
        quests = Question.select(Question.quest).where(
            Question.rep_member == user_id, Question.rep_group == group_id
        )
        # 如果没有设置我问, 则返回提示
        if not quests:
            ans = "您在此群聊没有设置问题"
            return {"reply": ans, "at_sender": False}
        # 如果有设置我问, 则返回所有问题
        ans = "你在此群聊设置的问题有: " + "| ".join(q.quest for q in quests)
        return {"reply": ans, "at_sender": False}



@bot.on_message("group")
async def answer(context):
    if ans := answers.get(context["raw_message"]):
        if a := ans.get(union(context["group_id"], context["user_id"])):
            return {"reply": a, "at_sender": False}
        if a := ans.get(union(context["group_id"], 1)):
            return {"reply": a, "at_sender": False}
