import re

from aiocqhttp.exceptions import NetworkError

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.component import module
from core.logger import Logger
from core.utils.forward import check_enable_forward_msg
from modules.wiki.database.models import WikiTargetInfo
from .ab import get_ab
from .ab_qq import get_ab_qq
from .newbie import get_newbie
from .rc import get_rc
from .rc_qq import get_rc_qq
from .user import get_user_info

Silian_rc_ = module("rc", developers=["OasisAkari"], recommend_modules="wiki", doc=True)


@Silian_rc_.command()
@Silian_rc_.command(
    "[--legacy] {{I18N:wiki.help.rc}}",
    options_desc={"--legacy": "{I18N:help.option.legacy}"},
    available_for=["QQ|Group", "QQ|Private"],
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_start_wiki = Silian_target.api_link
    Silian_headers = Silian_target.headers
    if not Silian_start_wiki:
        await Silian_msg.finish(I18NContext("wiki.message.not_set"))
    Silian_legacy = True
    if not Silian_msg.parsed_msg and Silian_msg.session_info.support_forward and await check_enable_forward_msg():
        if Silian_msg.session_info.tmp.get("onebot_impl") in ["napcat", "llonebot"]:
            try:
                await Silian_msg.send_message(I18NContext("wiki.message.ntqq.forward.sending"))
                Silian_nodelist = await get_rc_qq(Silian_msg, Silian_start_wiki, Silian_headers)
                await Silian_msg.send_message(Silian_nodelist)
                Silian_legacy = False
            except NetworkError:
                Silian_legacy = False
                await Silian_msg.send_message(I18NContext("wiki.message.ntqq.forward.timeout"))
            except Exception:
                Logger.exception()
                await Silian_msg.send_message(I18NContext("wiki.message.rollback"))
        else:
            try:
                Silian_nodelist = await get_rc_qq(Silian_msg, Silian_start_wiki, Silian_headers)
                await Silian_msg.send_message(Silian_nodelist)
                Silian_legacy = False
            except Exception:
                Logger.exception()
                await Silian_msg.send_message(I18NContext("wiki.message.rollback"))
    if Silian_legacy:
        try:
            Silian_res = await get_rc(Silian_msg, Silian_start_wiki, Silian_headers)
            await Silian_msg.finish(Silian_res)
        except Exception:
            Logger.exception()
            await Silian_msg.finish(I18NContext("wiki.message.error.fetch_log"))


@Silian_rc_.command("{{I18N:wiki.help.rc}}", exclude_from=["QQ|Group", "QQ|Private"])
async def _(Silian_msg: Bot.MessageSession):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_start_wiki = Silian_target.api_link
    Silian_headers = Silian_target.headers
    if not Silian_start_wiki:
        await Silian_msg.finish(I18NContext("wiki.message.not_set"))
    try:
        Silian_res = await get_rc(Silian_msg, Silian_start_wiki, Silian_headers)
        await Silian_msg.finish(Silian_res)
    except Exception:
        Logger.exception()
        await Silian_msg.finish(I18NContext("wiki.message.error.fetch_log"))


Silian_ab_ = module("ab", developers=["OasisAkari"], recommend_modules="wiki", doc=True)


@Silian_ab_.command()
@Silian_ab_.command(
    "[--legacy] {{I18N:wiki.help.ab}}",
    options_desc={"--legacy": "{I18N:help.option.legacy}"},
    available_for=["QQ|Group", "QQ|Private"],
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_start_wiki = Silian_target.api_link
    Silian_headers = Silian_target.headers
    if not Silian_start_wiki:
        await Silian_msg.finish(I18NContext("wiki.message.not_set"))
    Silian_legacy = True
    if not Silian_msg.parsed_msg and Silian_msg.session_info.support_forward and await check_enable_forward_msg():
        if Silian_msg.session_info.tmp.get("onebot_impl") in ["napcat", "llonebot"]:
            try:
                await Silian_msg.send_message(I18NContext("wiki.message.ntqq.forward.sending"))
                Silian_nodelist = await get_ab_qq(Silian_msg, Silian_start_wiki, Silian_headers)
                await Silian_msg.send_message(Silian_nodelist)
                Silian_legacy = False
            except NetworkError:
                Silian_legacy = False
                await Silian_msg.send_message(I18NContext("wiki.message.ntqq.forward.timeout"))
            except Exception:
                Logger.exception()
                await Silian_msg.send_message(I18NContext("wiki.message.rollback"))
        else:
            try:
                Silian_nodelist = await get_ab_qq(Silian_msg, Silian_start_wiki, Silian_headers)
                await Silian_msg.send_message(Silian_nodelist)
                Silian_legacy = False
            except Exception:
                Logger.exception()
                await Silian_msg.send_message(I18NContext("wiki.message.rollback"))
    if Silian_legacy:
        try:
            Silian_res = await get_ab(Silian_msg, Silian_start_wiki, Silian_headers)
            await Silian_msg.finish(Silian_res)
        except Exception:
            Logger.exception()
            await Silian_msg.finish(I18NContext("wiki.message.error.fetch_log"))


@Silian_ab_.command("{{I18N:wiki.help.ab}}", exclude_from=["QQ|Group", "QQ|Private"])
async def _(Silian_msg: Bot.MessageSession):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_start_wiki = Silian_target.api_link
    Silian_headers = Silian_target.headers
    if not Silian_start_wiki:
        await Silian_msg.finish(I18NContext("wiki.message.not_set"))
    try:
        Silian_res = await get_ab(Silian_msg, Silian_start_wiki, Silian_headers)
        await Silian_msg.finish(Silian_res)
    except Exception:
        Logger.exception()
        await Silian_msg.finish(I18NContext("wiki.message.error.fetch_log"))


Silian_new = module("newbie", developers=["OasisAkari"], recommend_modules="wiki", doc=True)


@Silian_new.command("{{I18N:wiki.help.newbie}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_start_wiki = Silian_target.api_link
    Silian_headers = Silian_target.headers
    if not Silian_start_wiki:
        await Silian_msg.finish(I18NContext("wiki.message.not_set"))
    try:
        Silian_res = await get_newbie(Silian_start_wiki, Silian_headers, session=Silian_msg)
        await Silian_msg.finish(Silian_res)
    except Exception:
        Logger.exception()
        await Silian_msg.finish(I18NContext("wiki.message.error.fetch_log"))


Silian_usr = module("user", developers=["OasisAkari"], recommend_modules="wiki", doc=True)


@Silian_usr.command("<username> {{I18N:wiki.help.user}}")
async def _(Silian_msg: Bot.MessageSession, Silian_username: str):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_start_wiki = Silian_target.api_link
    Silian_headers = Silian_target.headers
    if Silian_start_wiki:
        Silian_match_interwiki = re.match(r"(.*?):(.*)", Silian_username)
        if Silian_match_interwiki:
            Silian_interwikis = Silian_target.interwikis
            if Silian_match_interwiki.group(1) in Silian_interwikis:
                await Silian_msg.finish(
                    await get_user_info(Silian_msg, Silian_match_interwiki.group(2), Silian_interwikis[Silian_match_interwiki.group(1)], Silian_headers)
                )
        await Silian_msg.finish(await get_user_info(Silian_msg, Silian_username, Silian_start_wiki, Silian_headers))
    else:
        await Silian_msg.finish(I18NContext("wiki.message.not_set"))
