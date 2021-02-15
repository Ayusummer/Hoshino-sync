from random import choice
import hoshino
import nonebot
from nonebot import scheduler
from nonebot import on_command, CommandSession
from hoshino import log, priv,Service
from .data_source import Check
sv = Service('check', enable_on_default=True)

MAX_PERFORMANCE_PERCENT = hoshino.config.check.MAX_PERFORMANCE_PERCENT
PROCESS_NAME_LIST = hoshino.config.check.PROCESS_NAME_LIST
SUPERUSERS = hoshino.config.SUPERUSERS[0]

logger = log.new_logger('check')
check = Check(hoshino.config.check.PROCESS_NAME_LIST)


@on_command('check', aliases=('自检', '自檢', '自我检查', '自我檢查'), only_to_me=True)
async def music_recommend(session: CommandSession):
    if not priv.check_priv(session.event, priv.SUPERUSER):
        check_report = await check.get_check_easy(MAX_PERFORMANCE_PERCENT)
        more_info = '[CQ:at,qq={}]'.format(choice(list(SUPERUSERS))) if (SUPERUSERS and session.event['message_type'] == 'group') else "\n……请使用反馈功能联系维护哦~"
        if check_report:
            await session.send(check_report + more_info)
            check_report_admin = await check.get_check_info()
            if check_report_admin and SUPERUSERS:
                for admin in SUPERUSERS:
                    await session.send_private_msg(user_id=admin, message='調子がよくないみたいね……')
                    await session.send_private_msg(user_id=admin, message=check_report_admin)
        else: 
            await session.send("大丈夫だよ。心配してくれてありがとう。(人''▽｀)")
    else:
        check_report_admin = await check.get_check_info()
        if check_report_admin:
            await session.send(check_report_admin)
        else:
            logger.error("Not found Check Report")
            await session.send("[ERROR]Not found Check Report")

@scheduler.scheduled_job('cron', hour='*', minute='13') 
async def check_task():
    bot = nonebot.get_bot()
    result = await check.get_check_info()        
    await bot.send_private_msg(user_id=SUPERUSERS, message=result)