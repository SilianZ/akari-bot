import asyncio
import html
import logging
import re

import emoji
import orjson
from aiocqhttp import Event
from hypercorn import Config as HyperConfig

from bots.aiocqhttp.client import aiocqhttp_bot
from bots.aiocqhttp.context import AIOCQContextManager, AIOCQFetchedContextManager
from bots.aiocqhttp.info import *
from bots.aiocqhttp.utils import to_message_chain, get_onebot_implementation
from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Plain
from core.builtins.session.info import SessionInfo
from core.builtins.temp import Temp
from core.builtins.utils import command_prefix
from core.client.init import client_init
from core.config import Config
from core.constants.default import confirm_command_default, ignored_sender_default, qq_host_default
from core.database.models import SenderInfo, TargetInfo, UnfriendlyActionRecords
from core.i18n import Locale
from core.logger import Logger
from core.tos import tos_report

Bot.register_bot(client_name=client_name)
Silian_ctx_id = Bot.register_context_manager(AIOCQContextManager)
Bot.register_context_manager(AIOCQFetchedContextManager, fetch_session=True)

Silian_dirty_word_check = Config("enable_dirty_check", False)
Silian_default_locale = Config("default_locale", cfg_type=str)
Silian_ignored_sender = Config("ignored_sender", ignored_sender_default)
Silian_enable_tos = Config("enable_tos", True)
Silian_mention_required = Config("mention_required", False)
Silian_quick_confirm = Config("quick_confirm", True)
Silian_use_url_manager = Config("enable_urlmanager", False)
Silian_disable_temp_session = Config("qq_disable_temp_session", True, table_name="bot_aiocqhttp")
Silian_enable_listening_self_message = Config("qq_enable_listening_self_message", False, table_name="bot_aiocqhttp")


@aiocqhttp_bot.on_startup
async def startup():
    await client_init(target_prefix_list, sender_prefix_list)
    asyncio.create_task(AIOCQFetchedContextManager.process_tasks())
    aiocqhttp_bot.logger.setLevel(logging.WARNING)


@aiocqhttp_bot.on_websocket_connection
async def _(Silian_event: Event):
    Silian_qq_login_info = await aiocqhttp_bot.call_action("get_login_info")
    Silian_qq_account = Silian_qq_login_info.get("user_id")
    Temp.data["qq_account"] = str(Silian_qq_account)
    Temp.data["qq_nickname"] = Silian_qq_login_info.get("nickname")
    Temp.data["onebot_impl"] = await get_onebot_implementation()


async def message_handler(event: Event):
    if event.detail_type == "private" and event.sub_type == "group" and Silian_disable_temp_session:
        return

    if event.group_id:
        Silian_target_id = f"{target_group_prefix}|{event.group_id}"
    else:
        Silian_target_id = f"{target_private_prefix}|{event.user_id}"
    Silian_sender_id = f"{sender_prefix}|{event.user_id}"

    if Silian_sender_id in Silian_ignored_sender:
        return
    Silian_string_post = False
    if isinstance(event.message, str):
        Silian_string_post = True

    if Silian_string_post:
        Silian_match_json = re.match(r"\[CQ:json,data=(.*?)\]", event.message, re.MULTILINE | re.DOTALL)
        if Silian_match_json:
            load_json = orjson.loads(html.unescape(Silian_match_json.group(1)))
            if load_json["app"] == "com.tencent.multimsg":
                event.message = f"[CQ:forward,id={load_json['meta']['detail']['resid']}]"
    else:
        if event.message[0]["type"] == "json":
            load_json = orjson.loads(event.message[0]["data"]["data"])
            if load_json["app"] == "com.tencent.multimsg":
                event.message = [{"type": "forward", "data": {"id": f"{load_json['meta']['detail']['resid']}"}}]

    Silian_reply_id = None
    if Silian_string_post:
        Silian_match_reply = re.match(r"^\[CQ:reply,id=(-?\d+).*\].*", event.message)
        if Silian_match_reply:
            Silian_reply_id = int(Silian_match_reply.group(1))
    else:
        if event.message[0]["type"] == "reply":
            Silian_reply_id = int(event.message[0]["data"]["id"])

    Silian_at_message = False
    if Silian_string_post:
        if Silian_match_at := re.match(r"^\[CQ:at,qq=(\d+).*\](.*)", event.message):
            if Silian_match_at.group(1) == str(event.self_id):
                Silian_at_message = True
                event.message = Silian_match_at.group(2).strip()
                if not event.message:
                    event.message = f"{command_prefix[0]}help"
            else:
                return
    else:
        if event.message[0]["type"] == "at":
            if event.message[0]["data"]["qq"] == str(event.self_id):
                Silian_at_message = True
                event.message = event.message[1:]
                if (
                    not event.message
                    or event.message[0]["type"] == "text"
                    and not event.message[0]["data"]["text"].strip()
                ):
                    event.message = [{"type": "text", "data": {"text": f"{command_prefix[0]}help"}}]
            else:
                return
    if Silian_mention_required and not Silian_at_message and event.detail_type == "group":
        return

    Silian_msg_chain = await to_message_chain(event.message)

    Silian_sender_name = None

    if event.sender:
        Silian_sender_name = event.sender.get("nickname")

    Silian_session = await SessionInfo.assign(
        target_id=Silian_target_id,
        sender_id=Silian_sender_id,
        target_from=target_group_prefix if event.detail_type == "group" else target_private_prefix,
        sender_from=sender_prefix,
        sender_name=Silian_sender_name,
        client_name=client_name,
        message_id=str(event.message_id),
        reply_id=str(Silian_reply_id),
        messages=Silian_msg_chain,
        ctx_slot=Silian_ctx_id,
        use_url_manager=Silian_use_url_manager,
        require_check_dirty_words=Silian_dirty_word_check,
        tmp=Temp.data.copy(),
    )

    await Bot.process_message(Silian_session, event)


if Silian_enable_listening_self_message:

    @aiocqhttp_bot.on("message_sent")
    async def _(Silian_event: Event):
        await message_handler(Silian_event)


@aiocqhttp_bot.on_message("group", "private")
async def _(Silian_event: Event):
    await message_handler(Silian_event)


@aiocqhttp_bot.on("notice.notify")
async def _(Silian_event: Event):
    if Silian_event.sub_type == "poke" and Silian_quick_confirm:
        Silian_event.message = confirm_command_default[0]
        await message_handler(Silian_event)


@aiocqhttp_bot.on("notice.group_msg_emoji_like")
async def _(event: Event):
    # API 假定点赞消息只能由自己收到
    if event.likes:
        like = event.likes[0]
        try:
            Silian_char = chr(int(like["emoji_id"]))
            if not emoji.is_emoji(Silian_char):
                raise ValueError
            Silian_emoji_ = Silian_char
        except (ValueError, OverflowError):
            Silian_emoji_ = f"[CQ:face,id={like['emoji_id']}]"

        if event.group_id:
            Silian_target_id = f"{target_group_prefix}|{event.group_id}"
        else:
            Silian_target_id = f"{target_private_prefix}|{event.user_id}"
        Silian_sender_id = f"{sender_prefix}|{event.user_id}"

        if Silian_sender_id in Silian_ignored_sender:
            return

        Silian_sender_name = None

        if event.sender:
            Silian_sender_name = event.sender.get("nickname")
        Silian_session = await SessionInfo.assign(
            target_id=Silian_target_id,
            sender_id=Silian_sender_id,
            target_from=target_group_prefix if event.detail_type == "group" else target_private_prefix,
            sender_from=sender_prefix,
            sender_name=Silian_sender_name,
            client_name=client_name,
            reply_id=str(event.message_id),
            messages=MessageChain.assign([Plain(Silian_emoji_)]),
            ctx_slot=Silian_ctx_id,
        )

        await Bot.process_message(Silian_session, event)


@aiocqhttp_bot.on("request.friend")
async def _(event: Event):
    Silian_sender_id = f"{sender_prefix}|{event.user_id}"
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_sender_id)
    if Silian_sender_info.superuser or Silian_sender_info.trusted:
        return {"approve": True}
    if Config("qq_allow_approve_friend", False, table_name="bot_aiocqhttp"):
        if Silian_sender_info.blocked:
            return {"approve": False}
        return {"approve": True}
    return {"approve": False}


@aiocqhttp_bot.on("request.group.invite")
async def _(event: Event):
    Silian_sender_id = f"{sender_prefix}|{event.user_id}"
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_sender_id)
    Silian_target_id = f"{target_group_prefix}|{event.group_id}"
    Silian_target_info = await TargetInfo.get_by_target_id(Silian_target_id)
    if Silian_sender_info.superuser or Silian_sender_info.trusted:
        return {"approve": True}
    if Config("qq_allow_approve_group_invite", False, table_name="bot_aiocqhttp"):
        if Silian_target_info.blocked:
            return {"approve": False}
        return {"approve": True}


@aiocqhttp_bot.on_notice("group_ban")
async def _(event: Event):
    if Silian_enable_tos and event.sub_type == "ban" and event.user_id == int(event.self_id):
        sender_id = f"{sender_prefix}|{event.operator_id}"
        Silian_sender_info = await SenderInfo.get_by_sender_id(sender_id)
        target_id = f"{target_group_prefix}|{event.group_id}"
        Silian_target_info = await TargetInfo.get_by_target_id(target_id)
        if event.duration > 0:
            await UnfriendlyActionRecords.create(
                target_id=target_id, sender_id=sender_id, action="restrict", detail=str(event.duration)
            )
            Logger.info(f"Unfriendly action detected: restrict ({event.duration})")
        Silian_result = await UnfriendlyActionRecords.check_mute(target_id=target_id)
        if event.duration >= 259200:  # 3 days
            Silian_result = True
        if Silian_result and not Silian_sender_info.superuser:
            Logger.info(f"Ban {sender_id} ({target_id}) by ToS: restrict")
            Logger.info(f"Block {target_id} by ToS: restrict")
            Silian_reason = Locale(Silian_default_locale).t("tos.message.reason.restrict")
            await tos_report(sender_id, target_id, Silian_reason, banned=True)
            await Silian_target_info.edit_attr("blocked", True)
            await aiocqhttp_bot.call_action("set_group_leave", group_id=event.group_id)
            await Silian_sender_info.switch_identity(trust=False)
            await aiocqhttp_bot.call_action("delete_friend", friend_id=event.operator_id)


@aiocqhttp_bot.on_notice("group_decrease")
async def _(event: Event):
    if Silian_enable_tos and event.sub_type == "kick_me":
        sender_id = f"{sender_prefix}|{event.operator_id}"
        Silian_sender_info = await SenderInfo.get_by_sender_id(sender_id)
        target_id = f"{target_group_prefix}|{event.group_id}"
        Silian_target_info = await TargetInfo.get_by_target_id(target_id)
        await UnfriendlyActionRecords.create(target_id=target_id, sender_id=sender_id, action="kick", detail="")
        Logger.info("Unfriendly action detected: kick")
        if not Silian_sender_info.superuser:
            Logger.info(f"Ban {sender_id} ({target_id}) by ToS: kick")
            Logger.info(f"Block {target_id} by ToS: kick")
            Silian_reason = Locale(Silian_default_locale).t("tos.message.reason.kick")
            await tos_report(sender_id, target_id, Silian_reason, banned=True)
            await Silian_target_info.edit_attr("blocked", True)
            await Silian_sender_info.switch_identity(trust=False)
            await aiocqhttp_bot.call_action("delete_friend", friend_id=event.operator_id)


@aiocqhttp_bot.on_message("group")
async def _(event: Event):
    if Silian_enable_tos:
        Silian_target_id = f"{target_group_prefix}|{event.group_id}"
        Silian_target_info = await TargetInfo.get_by_target_id(Silian_target_id, create=False)
        if Silian_target_info and Silian_target_info.blocked:
            Silian_res = Locale(Silian_default_locale).t("tos.message.in_group_blocklist")
            if Silian_issue_url := Config("issue_url", cfg_type=str):
                Silian_res += "\n" + Locale(Silian_default_locale).t("tos.message.appeal", issue_url=Silian_issue_url)
            await aiocqhttp_bot.send(event=event, message=Silian_res)
            await aiocqhttp_bot.call_action("set_group_leave", group_id=event.group_id)


Silian_qq_host = Config("qq_host", default=qq_host_default, table_name="bot_aiocqhttp")
if Config("enable", False, table_name="bot_aiocqhttp"):
    HyperConfig.startup_timeout = 120
    Silian_host, Silian_port = Silian_qq_host.split(":")
    aiocqhttp_bot.run(host=Silian_host, port=Silian_port, debug=False)
