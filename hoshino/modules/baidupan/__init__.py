import re

from nonebot import *
from . import util, api, dupan_link, share, ru
from hoshino import Service  # 如果使用hoshino的分群管理取消注释这行

#
sv = Service('baidupan')  # 如果使用hoshino的分群管理取消注释这行

# 初始化配置文件
config = util.get_config()

# 初始化nonebot
_bot = get_bot()


@sv.on_message('group')  # 如果使用hoshino的分群管理取消注释这行 并注释下一行的 @_bot.on_message("group")
# @_bot.on_message  # nonebot使用这
async def pan_main(*params):
    bot, ctx = (_bot, params[0]) if len(params) == 1 else params

    msg = str(ctx['message']).strip()
    # 获取下载直链
    keyword = util.get_msg_keyword(config.comm.keyword, msg, True)
    if keyword:
        try:
            return await bot.send(ctx, await get_share(ctx, keyword, *keyword.split(config.comm.split)))
        except TypeError as e:
            print(e)
            await bot.send(ctx, '如果是秒传链接请尝试使用 %s' % config.comm.link2bdlink)

    # 获取秒传链接和直链
    keyword = util.get_msg_keyword(config.comm.get_all, msg, True)
    if keyword:
        return await bot.send(ctx, await get_share(ctx, keyword, *keyword.split(config.comm.split),
                                                   is_get_ru=True))

    # 仅获取秒传链接
    keyword = util.get_msg_keyword(config.comm.get_ru, msg, True)
    if keyword:
        return await bot.send(ctx, await get_share(ctx, keyword, *keyword.split(config.comm.split),
                                                   is_get_url=False,
                                                   is_get_ru=True))

    # 获取度盘秒传的兼容模式
    keyword = util.get_msg_keyword(config.comm.link2bdlink, msg, True)
    if keyword:
        return await bot.send(ctx, await get_share(ctx, keyword, 'OK'))

    # 获取帮助信息
    keyword = util.get_msg_keyword(config.comm.help, msg, True)
    if isinstance(keyword, str):
        for x in config.str.help:
            await bot.send(ctx, x)


# 获取分享信息
async def get_share(ctx, keyword, pan_url: str,
                    pwd=None, dir_str=None,
                    is_get_url=True,
                    is_get_ru=None):
    if not pan_url:
        return '文件无法创建下载链接..\n'

    tip = f'发送 panhelp 查看使用方法\n'
    file_r = dupan_link.pan_parse(keyword)
    sp = util.send_process(ctx, 0, 3)

    if file_r and keyword:
        is_local = None
        msg = ''
        for info in file_r:
            is_ok = ru.rapidupload(
                info.md5,
                info.md5s,
                info.size,
                info.name,
                dir_name=share.get_dir_str(ctx.user_id) + '/'
            )
            if not is_ok:
                msg += f'{info.name} 获取失败啦\n'
                continue
            await sp.send(f'秒传文件获取成功 [{info.name}]')
            # 大于50M 需要分享后处理
            if int(info.size) > 52428800:
                await sp.send('正在转存.')
                s_url, shareid = share.set_share(is_ok['fs_id'])
                if config.rules.auto_cancel_share:
                    share.auto_cancel_share(shareid, is_ok['path'])  # 自动取消分享
                if s_url:
                    await sp.send()
                    msg += await get_share(ctx, '', s_url, pwd='erin')
                    continue
                else:
                    await sp.send('尝试创建本地下载地址..')
                    urls = api.get_local_download_link(is_ok['path'])
                    if not urls:
                        msg += f'\n——————————\n文件 {info.name} 获取失败\n——————————\n'
                        continue
                    # url = api.get_real_url_by_dlink(urls[0], urls=urls, ua=api.get_pan_ua())
                    url = urls[0]
                    is_local = True

            else:
                url = '\n'.join(api.get_web_file_url([is_ok['fs_id']]))

            if not url:
                await _bot.send(ctx, f'{info.name} 获取下载地址失败啦\n')
                continue
            msg += '——————————\n'
            msg += f'文件名: {info.name}\n'
            msg += f'大小: {util.size_format(int(info.size))}\n'
            msg += f'下载地址: {url}\n'
            msg += '——————————\n'
        return msg + '请设置这个UA下载 %s' % api.get_pan_ua() if is_local else msg

    surl, s_pwd = share.get_surl(pan_url)
    if not surl:
        return f'链接格式不正确啦\n{tip}'

    if not pwd and s_pwd:
        pwd = s_pwd

    if pwd:
        pwd = re.search(r'[a-zA-Z0-9]+', pwd).group()

    surl = surl[1:]
    # await _bot.send(ctx, f'{sp.send(1, 4)} 网盘分享链接获取成功 [1{surl}]')
    randsk = share.verify(surl, pwd)
    if not randsk:
        return f'啊这 提取码错误或者是文件失效\n{tip}'
    await sp.send('正在获取分享信息')
    yun_data = share.get_yun_data(surl, randsk)
    if not yun_data:
        return '分享过期或者被取消'
    if yun_data.get('share_uk'):
        yun_data.uk = yun_data.share_uk
    file_list = share.get_file_list(yun_data.shareid, yun_data.uk, randsk, dir_str=dir_str)

    if not file_list.errno == 0:
        return '文件失效或者分享被取消'
    await sp.send('正在获取文件信息')

    msg_dir_str, file_info = share.handle_file_list(surl, file_list, yun_data, randsk)
    if not msg_dir_str and not file_info:
        return '获取文件列表失败'

    if is_get_url:
        for file_i in file_info:
            await _bot.send(ctx, '文件名: %s\n大小: %s\n地址: %s' % (
                file_i['name'], util.size_format(file_i['size']), file_i['url']))

    if is_get_ru:
        for file_i in file_info:
            if isinstance(yun_data.file_list, list):
                yun_data.file_list = util.dict_to_object({'list': file_list.list})
            ru_link = await get_ru(ctx, file_i['url'], yun_data, randsk)
            await _bot.send(ctx, ru_link)
    await sp.send()
    return f'找到以下目录(在原有的命令后加上{config.comm.split}目录进入)：\n' + '\n'.join(
        msg_dir_str) if msg_dir_str else f'发送 {config.comm.help} 查看下载方法\n使用ru#来获取秒传地址'


# 获取秒传信息
async def get_ru(ctx, url_str, yun_data, randsk):
    sp = util.send_process(ctx, 0, 3)
    info = ru.get_rapidupload_info(url_str)
    if not info:
        await sp.send('秒传信息获取失败,正在尝试修复')
        files = share.transfer(yun_data, randsk, dir_str=share.get_dir_str(ctx.user_id))
        if not files:
            return '转存失败.修复失败'
        await sp.send('转存成功,正在修复')
        info = []
        for file_path in files:
            urls = api.get_local_download_link(file_path)
            if not urls:
                await _bot.send(ctx, f'{file_path} 修复失败')
                continue
            real_url = api.get_real_url_by_dlink(urls[0])
            if not real_url:
                # await _bot.send(ctx, f'{file_path} 本地下载地址获取失败,过段时间在试吧')
                real_url = urls[0]
            ru_info = ru.get_rapidupload_info(real_url, ua=api.get_pan_ua())
            if not ru_info:
                await _bot.send(ctx, f'{file_path} 修复失败,获取内部下载失败')
                continue
            info.append(ru_info)
    await sp.send()
    return '秒传链接: %s' % dupan_link.to_bdlink(info)
