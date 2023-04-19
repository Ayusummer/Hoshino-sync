from hoshino import Service, priv 
import asyncio
from revChatGPT.revChatGPT import Chatbot
import time

config = {
        "Authorization": "<Your Bearer Token Here>", # This is optional
        "session_token": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..Dy6Wlh4RLe7bpY3c.sxh6ZRDvH3zfnl4QzQGiWvOVCULKOyYGvZ0OFkHyqxR8y6gGS7qHBAZ8xvFRHt9PwmAJnHp8ql-eZl0VqzzAihaMjq8U2RCmBFY4H6mgBvv0zS32qcCMhUmq3owDtLOkB7Ivgm3tmNFG_w7JGItSGJhtzJ_oOaTkW8IOwrDE7jgp3QB8WqTNBehcnR7JQ9nlqyBOXtAYPa87PNAIV_uU_0wlTp6CaUSqfQJjQsImfiEkl6dT7sS6aozxQO086x1fD8pIHydtZdesX4gZAy_ORsaqM7FExhGo74N-KBq00SwOgaB74cyoNm1B-YdN6ts1mkbq1R8dvRfFGnnkaMGcsWc815mlW8aTA21wW1yXSfljAlqr8X6WDKGfL0Xm3lsUhZ4k-ZijtaHq_IZstJr10deuE6ChiW3XcnwSPyGcuLY9U1FIhCgTBW0KON2yWFJM24p8I8wq_xer7Gd16tSSHrVU9aTKpUX4BSvp8wFsp3mqF4g4utpqXjX-TJIu2bsz_AgzhDprt01tego-EGKRarUkmqtoqCYEW_MR0IYURiWGmgS17fMQKowqGkpC6URW-IgMda70WjjcFJXacoASWn8y4AJFPY6DWsCVy9Ss_B9K8xZ53zaadXuwngPvICJd-jPqZZzw3C_W528exTd9qioIok1fy4W7O--6VmNPPKBuT9zByffHFbeokgFysT-2aQaBKgYuRo6_EXU82abe2knMj0KbJm-fBtXXpKAramWRdgo7uV53ULcQCO6I7qV8ey7k_vTTAOBsO1GPEOpx3mnwjprgQ0CV_Tgx_vdEKrLiW4FN4IW7WhfPGVZdsF4ZQdYdKTacUXb1a4aCrhAg6k6KfaYPo6WEH2czZ1WmLW9u4G5PDtdC-M5z1wr4mh9DC91AgonJnaTqhd80GD3z_BGK2D2o2_gXkC_mbt_0G2OQSpt9lcCiZF9mIjOqMGAJbUq5XFs6Tr0vRoWexWseKv3jmR97ItrEyZBvRrFhwOmH1twyLZTsnJIIaBvaAd4XsmEY0wBSu1B9HJhWdT48jH4zXG1UQv6xg9fq_hVfECIHLJNae4aKkXEgiWjjk8W-812ow8ct1948d0osM2OV8lEfHhGdYBcmyci6tC1RyzaR9vteZW1Peiolm_MocviLexvkw2gBnAKKmKYKHc5sE1X1Jr_plWNHV4VaKecPjXv-u19laxO99AhLEkcy8ljgq47KTH_jNTObJ88z2sHFeMZEAjo0t_8VQ4xkSsjF-7Js4Q71ttsYPnZNU1DfUW5NG4CkO-xHvH-qcHNsIOYDZOKw4OfpbpdIEtIwU1OXJD-XKiJckVM6zpYqyeP-fyuQzcp8TQIy5PlWGPIjbveeL57CjLACQjmAaDHO_HZBgvLyXrJaHPF8pLjduT-wIFDLvgE5dgZ6E3R7Jow587XaMlBcHlcbzSkfRwx7WubLq16Qsv4IrNC1KYKVgZjqw93prWEpl1hwU5zBsw9oSflCMEMTvgcsYPiU4EeA5HFp6odHKmcZ2bDoc6doprAfNr4to6WD_vGlr66BvhhlWsy0OK0EDTS2749vyhyA-4KOu_7_UHtpjr8Shg-ya0qlQg8r2aPbg7hLzPDk4hgDHKGgqSA80FqJGbxgqDg-7jPRwVhUjIhTwLqKJU1Vh7HwRLW-1p41XJFoVystzpH5-trh-8mssYAGAXtb8zT2vDMvtEOTx5hO10WmbJtFAg0BbaJ1fgitC_mkl-E19SMO3T3WiJBSujWofMGm9Z5323WGyozmOeCExhfR2jqDUtaNTtmPAKviAUb3-uwTxuhK3ZFuGTPZxgObiT_H1hktKLfW1CAlbz8VnJfypjgs76oWdhhb9fsCUx-fVtaq4yBPpymDt5ZCRydeNj-qJOQznYQTF_rqNIpOtxzaiuf-6hbZNWsJI8bP2p7yLrT9peE9GRWG0cFYr4zYJpptMrIwWOGWuLjs7ukq_YySJYPWRqcZJpiHmmQd5d1tZ8KLzh7m-ZGghfV9CiSa6w5GQ7sCKDgDD-v_wDK-_lu1GrOQ-EWVi4vcCM-o24hnO8dCsgVOe2cfEBl1AlrYYqY6SUpqlgTdVokmQkXAydNi8dd4zKcjVou3fYmrVCYmfE_VtCU344p0VbDuzdSb5FBbznDlIUWeEbugi3uz67FkhfMGiAfdkoku7i9juGbz3lsTYMpCJMJLtUCkJZWjDJpD3TlaQlkDLv0LIqIYkcIweI8xv32_Tx7KGuwJzc2jqwfakdiqXu9_xEq9c0vHWJP_GHrffRKUtw1Uf6NQ5KgAHkmJomBZMRrENrHC4bhj-e8997lpsuDqP5Nu0113eC5GtWZVtnPe-oyUG4vbZ5qYdVs.6MfOeCzDKRchp_rY8i6M_A"
        }

user_session = dict()
chatbot = Chatbot(config)

sv_help = """ gpt + 内容可以发送聊天
"""
sv = Service(
    name="chatGPT",  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.SUPERUSER,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    bundle="娱乐",  # 分组归类
    help_=sv_help  # 帮助说明
) 


def get_chat_response(session_id, prompt):
    if session_id in user_session:
        # 如果在三分钟内再次发起对话则使用相同的会话ID
        if time.time() < user_session[session_id]['timestamp'] + 60 * 3:
            chatbot.conversation_id = user_session[session_id]['conversation_id']
            chatbot.parent_id = user_session[session_id]['parent_id']
        else:
            chatbot.reset_chat()
    else:
        chatbot.reset_chat() 
    try:
        resp = chatbot.get_chat_response(prompt, output="text") 
        user_cache = dict()
        user_cache['timestamp'] = time.time()
        user_cache['conversation_id'] = resp['conversation_id']
        user_cache['parent_id'] = resp['parent_id']
        user_session[session_id] = user_cache

        return resp['message']
    except Exception as e:
        return f"发生错误: {str(e)}"
 

@sv.on_prefix(("gpt"))
async def chatGPT_method(bot, ev): 
    uid = ev.user_id
    gid = ev.group_id
    name = ev.sender['nickname'] 
    msg = str(ev.message.extract_plain_text()).strip()
    resp = await asyncio.get_event_loop().run_in_executor(None, get_chat_response, uid, msg)
    await bot.send(ev, resp, at_sender = True)

 # 定时刷新seesion_token
@sv.scheduled_job("interval", minutes=10)
async def refresh_session(): 
    chatbot.refresh_session()