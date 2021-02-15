import time

from nonebot import get_bot

from .data import Question

bot = get_bot()
answers = {}


def union(group_id, user_id):
    return (group_id << 32) | user_id


# recovery from database
for qu in Question.select():
    if qu.quest not in answers:
        answers[qu.quest] = {}
    answers[qu.quest][union(qu.rep_group, qu.rep_member)] = qu.answer


@bot.on_message('group')
async def handle(context):
    message = context['raw_message']
    if message.startswith('我问'):
        msg = message[2:].split('你答', 1)
        if len(msg) == 1:
            return {'reply': '发送“我问xxx你答yyy”我才能记住', 'at_sender': False}
        q, a = msg
        if q not in answers:
            answers[q] = {}
        answers[q][union(context['group_id'], context['user_id'])] = a
        Question.replace(
            quest=q,
            rep_group=context['group_id'],
            rep_member=context['user_id'],
            answer=a,
            creator=context['user_id'],
            create_time=time.time(),
        ).execute()
        return {'reply': '好的我记住了', 'at_sender': False}
    elif message.startswith('大家问') or message.startswith('有人问'):
        if context['sender']['role'] == 'member':
            return {'reply': f'只有管理员才可以用“{message[:3]}”', 'at_sender': False}
        msg = message[3:].split('你答', 1)
        if len(msg) == 1:
            return {'reply': f'发送“{message[:3]}xxx你答yyy”我才能记住', 'at_sender': False}
        q, a = msg
        if q not in answers:
            answers[q] = {}
        answers[q][union(context['group_id'], 1)] = a
        Question.replace(
            quest=q,
            rep_group=context['group_id'],
            rep_member=1,
            answer=a,
            creator=context['user_id'],
            create_time=time.time(),
        ).execute()
        return {'reply': '好的我记住了', 'at_sender': False}
    elif message.startswith('不要回答'):
        q = context['raw_message'][4:]
        ans = answers.get(q)
        if ans is None:
            return {'reply': '我不记得有这个问题', 'at_sender': False}

        specific = union(context['group_id'], context['user_id'])
        a = ans.get(specific)
        if a:
            Question.delete().where(
                Question.quest == q,
                Question.rep_group == context['group_id'],
                Question.rep_member == context['user_id'],
            ).execute()
            del ans[specific]
            if not ans:
                del answers[q]
            return {'reply': f'我不再回答“{a}”了', 'at_sender': False}

        if context['sender']['role'] == 'member':
            return {'reply': f'只有管理员可以删除别人的问题', 'at_sender': False}

        wild = union(context['group_id'], 1)
        a = ans.get(wild)
        if a:
            Question.delete().where(
                Question.quest == q,
                Question.rep_group == context['group_id'],
                Question.rep_member == 1,
            ).execute()
            del ans[wild]
            if not ans:
                del answers[q]
            return {'reply': f'我不再回答“{a}”了', 'at_sender': False}


@bot.on_message('group')
async def answer(context):
    ans = answers.get(context['raw_message'])
    if ans:
        a = ans.get(union(context['group_id'], context['user_id']))
        if a:
            return {'reply': a, 'at_sender': False}
        a = ans.get(union(context['group_id'], 1))
        if a:
            return {'reply': a, 'at_sender': False}
