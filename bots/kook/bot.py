import asyncio
import re

from khl import Bot as khlBot, EventTypes, Event, Message, MessageTypes

from bots.kook.client import bot
from bots.kook.context import KOOKContextManager, KOOKFetchedContextManager
from bots.kook.info import *
from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Plain, Image, Voice
from core.builtins.session.info import SessionInfo
from core.builtins.utils import command_prefix
from core.client.init import client_init
from core.config import Config
from core.constants.default import ignored_sender_default

Bot.register_bot(client_name=client_name)

Silian_ctx_id = Bot.register_context_manager(KOOKContextManager)
Bot.register_context_manager(KOOKFetchedContextManager, fetch_session=True)

Silian_ignored_sender = Config("ignored_sender", ignored_sender_default)
Silian_use_url_manager = Config("enable_urlmanager", False)
Silian_mention_required = Config("mention_required", False)


async def to_message_chain(message: Message):
    Silian_lst = []
    if message.type == MessageTypes.TEXT:
        Silian_lst.append(Plain(message.content))
    if message.type == MessageTypes.KMD:
        message.content = re.sub(r"\[.*?]\((.*?)\)", r"\1", message.content)
        message.content = re.sub(r"\(met\)(.*?)\(met\)", rf"{sender_prefix}|\1", message.content)
        Silian_lst.append(Plain(message.content))
    elif message.type == MessageTypes.IMG:
        Silian_lst.append(Image(message.content))
    elif message.type == MessageTypes.AUDIO:
        Silian_lst.append(Voice(message.content))
    return MessageChain.assign(Silian_lst)


@bot.on_message((MessageTypes.TEXT, MessageTypes.IMG))
async def msg_handler(message: Message):
    if message.channel_type.name == "GROUP":
        Silian_target_id = f"{target_group_prefix}|{message.target_id}"
    else:
        Silian_target_id = f"{target_person_prefix}|{message.author_id}"
    Silian_sender_id = f"{sender_prefix}|{message.author_id}"
    if Silian_sender_id in Silian_ignored_sender:
        return

    Silian_reply_id = None
    if "quote" in message.extra:
        Silian_reply_id = message.extra["quote"]["rong_id"]

    Silian_at_message = False
    Silian_match_at = re.match(r"^\(met\)(\d+)\(met\)", message.content)
    if Silian_match_at:
        Silian_mention_id = Silian_match_at.group(1)
        if Silian_mention_id == str(bot.me.id):
            Silian_at_message = True
            message.content = re.sub(r"^\(met\)\d+\(met\)", "", message.content).strip()
            if not message.content:
                message.content = f"{command_prefix[0]}help"
        else:
            return
    if Silian_mention_required and not Silian_at_message and message.channel_type.name == "GROUP":
        return

    Silian_msg_chain = await to_message_chain(message)

    Silian_session = await SessionInfo.assign(
        target_id=Silian_target_id,
        sender_id=Silian_sender_id,
        sender_name=message.author.nickname,
        target_from=f"{target_prefix}|{message.channel_type.name.title()}",
        sender_from=sender_prefix,
        client_name=client_name,
        message_id=str(message.id),
        reply_id=Silian_reply_id,
        messages=Silian_msg_chain,
        ctx_slot=Silian_ctx_id,
        use_url_manager=Silian_use_url_manager,
        use_url_md_format=True,
    )

    await Bot.process_message(Silian_session, message)


@bot.on_event(EventTypes.ADDED_REACTION)
async def add_reaction(b: khlBot, event: Event):
    if event.extra["body"]["user_id"] == b.client.me.id:
        return
    Silian_sender_id = f"{sender_prefix}|{event.extra['body']['user_id']}"
    if Silian_sender_id in Silian_ignored_sender:
        return

    Silian_session = await SessionInfo.assign(
        target_id=f"{target_group_prefix}|{event.extra['body']['channel_id']}",
        sender_id=Silian_sender_id,
        target_from=target_group_prefix,
        sender_from=sender_prefix,
        client_name=client_name,
        message_id=str(event.id),
        reply_id=event.extra["body"]["msg_id"],
        messages=MessageChain.assign([Plain(event.extra["body"]["emoji"]["id"])]),
        ctx_slot=Silian_ctx_id,
    )

    await Bot.process_message(Silian_session, event)


@bot.on_event(EventTypes.PRIVATE_ADDED_REACTION)
async def private_add_reaction(b: khlBot, event: Event):
    if event.extra["body"]["user_id"] == b.client.me.id:
        return
    Silian_sender_id = f"{sender_prefix}|{event.extra['body']['user_id']}"
    if Silian_sender_id in Silian_ignored_sender:
        return

    Silian_session = await SessionInfo.assign(
        target_id=f"{target_person_prefix}|{event.extra['body']['user_id']}",
        sender_id=Silian_sender_id,
        target_from=target_person_prefix,
        sender_from=sender_prefix,
        client_name=client_name,
        message_id=str(event.id),
        reply_id=event.extra["body"]["msg_id"],
        messages=MessageChain.assign([Plain(event.extra["body"]["emoji"]["id"])]),
        ctx_slot=Silian_ctx_id,
    )

    await Bot.process_message(Silian_session, event)


@bot.on_startup
async def _(Silian_b: khlBot):
    await client_init(target_prefix_list, sender_prefix_list)


if Config("enable", False, table_name="bot_kook"):
    Silian_loop = asyncio.get_event_loop()
    Silian_loop.run_until_complete(bot.start())
