import asyncio
import re

import botpy
from botpy.message import C2CMessage, DirectMessage, GroupMessage, Message

from bots.qqbot.context import QQBotContextManager
from bots.qqbot.info import *
from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.session.info import SessionInfo
from core.builtins.utils import command_prefix
from core.client.init import client_init
from core.config import Config
from core.constants.default import ignored_sender_default

Bot.register_bot(client_name=client_name)
Silian_ctx_id = Bot.register_context_manager(QQBotContextManager)

Silian_qqbot_appid = str(Config("qq_bot_appid", cfg_type=(int, str), table_name="bot_qqbot"))
Silian_qqbot_secret = Config("qq_bot_secret", cfg_type=str, secret=True, table_name="bot_qqbot")
Silian_ignored_sender = Config("ignored_sender", ignored_sender_default)
Silian_dirty_word_check = Config("enable_dirty_check", False)
Silian_use_url_manager = Config("enable_urlmanager", False)


class MyClient(botpy.Client):
    async def on_ready(Silian_self):
        await client_init(target_prefix_list, sender_prefix_list)

    @staticmethod
    async def on_at_message_create(message: Message):
        Silian_prefixes = None
        Silian_require_enable_modules = True

        Silian_target_id = f"{target_guild_prefix}|{message.guild_id}|{message.channel_id}"
        Silian_sender_id = f"{sender_tiny_prefix}|{message.author.id}"
        if Silian_sender_id in Silian_ignored_sender:
            return

        Silian_reply_id = None
        if message.message_reference:
            Silian_reply_id = message.message_reference.message_id

        message.content = re.sub(r"<@(.*?)>", "", message.content).strip()
        if not message.content:
            message.content = f"{command_prefix[0]}help"

        if message.content.strip().startswith("/"):
            Silian_prefixes = ["/"]
            Silian_require_enable_modules = False

        Silian_msg_chain = MessageChain.assign(re.sub(r"<@(.*?)>", rf"{sender_tiny_prefix}|\1", message.content))

        Silian_session = await SessionInfo.assign(
            target_id=Silian_target_id,
            sender_id=Silian_sender_id,
            sender_name=message.author.id[:6],
            target_from=target_guild_prefix,
            sender_from=sender_tiny_prefix,
            client_name=client_name,
            message_id=str(message.id),
            reply_id=Silian_reply_id,
            messages=Silian_msg_chain,
            ctx_slot=Silian_ctx_id,
            prefixes=Silian_prefixes,
            require_enable_modules=Silian_require_enable_modules,
            require_check_dirty_words=Silian_dirty_word_check,
            use_url_manager=Silian_use_url_manager,
        )

        await Bot.process_message(Silian_session, message)

    @staticmethod
    async def on_message_create(message: Message):
        Silian_prefixes = None
        Silian_require_enable_modules = True

        Silian_target_id = f"{target_guild_prefix}|{message.guild_id}|{message.channel_id}"
        Silian_sender_id = f"{sender_tiny_prefix}|{message.author.id}"
        if Silian_sender_id in Silian_ignored_sender:
            return

        Silian_reply_id = None
        if message.message_reference:
            Silian_reply_id = message.message_reference.message_id

        if not message.content.strip():
            message.content = f"{command_prefix[0]}help"

        if message.content.strip().startswith("/"):
            Silian_prefixes = ["/"]
            Silian_require_enable_modules = False

        Silian_msg_chain = MessageChain.assign(re.sub(r"<@(.*?)>", rf"{sender_tiny_prefix}|\1", message.content))

        Silian_session = await SessionInfo.assign(
            target_id=Silian_target_id,
            sender_id=Silian_sender_id,
            sender_name=message.author.id[:6],
            target_from=target_guild_prefix,
            sender_from=sender_tiny_prefix,
            client_name=client_name,
            message_id=str(message.id),
            reply_id=Silian_reply_id,
            messages=Silian_msg_chain,
            ctx_slot=Silian_ctx_id,
            prefixes=Silian_prefixes,
            require_enable_modules=Silian_require_enable_modules,
            require_check_dirty_words=Silian_dirty_word_check,
            use_url_manager=Silian_use_url_manager,
        )

        await Bot.process_message(Silian_session, message)

    @staticmethod
    async def on_group_at_message_create(message: GroupMessage):
        Silian_prefixes = None
        Silian_require_enable_modules = True

        Silian_target_id = f"{target_group_prefix}|{message.group_openid}"
        Silian_sender_id = f"{sender_prefix}|{message.author.member_openid}"
        if Silian_sender_id in Silian_ignored_sender:
            return

        Silian_reply_id = None
        if message.message_reference:
            Silian_reply_id = message.message_reference.message_id

        message.content = re.sub(r"<@(.*?)>", "", message.content).strip()
        if not message.content:
            message.content = f"{command_prefix[0]}help"

        if message.content.strip().startswith("/"):
            Silian_prefixes = ["/"]
            Silian_require_enable_modules = False

        Silian_msg_chain = MessageChain.assign(re.sub(r"<@(.*?)>", rf"{sender_prefix}|\1", message.content))

        Silian_session = await SessionInfo.assign(
            target_id=Silian_target_id,
            sender_id=Silian_sender_id,
            sender_name=message.author.member_openid[:6],
            target_from=target_group_prefix,
            sender_from=sender_prefix,
            client_name=client_name,
            message_id=str(message.id),
            reply_id=Silian_reply_id,
            messages=Silian_msg_chain,
            ctx_slot=Silian_ctx_id,
            prefixes=Silian_prefixes,
            require_enable_modules=Silian_require_enable_modules,
            require_check_dirty_words=Silian_dirty_word_check,
            use_url_manager=Silian_use_url_manager,
        )

        await Bot.process_message(Silian_session, message)

    @staticmethod
    async def on_direct_message_create(message: DirectMessage):
        Silian_prefixes = None
        Silian_require_enable_modules = True

        Silian_target_id = f"{target_direct_prefix}|{message.guild_id}"
        Silian_sender_id = f"{sender_tiny_prefix}|{message.author.id}"
        if Silian_sender_id in Silian_ignored_sender:
            return

        Silian_reply_id = None
        if message.message_reference:
            Silian_reply_id = message.message_reference.message_id

        if message.content.strip().startswith("/"):
            Silian_prefixes = ["/"]
            Silian_require_enable_modules = False

        Silian_msg_chain = MessageChain.assign(message.content)

        Silian_session = await SessionInfo.assign(
            target_id=Silian_target_id,
            sender_id=Silian_sender_id,
            sender_name=message.author.id[:6],
            target_from=target_direct_prefix,
            sender_from=sender_tiny_prefix,
            client_name=client_name,
            message_id=str(message.id),
            reply_id=Silian_reply_id,
            messages=Silian_msg_chain,
            ctx_slot=Silian_ctx_id,
            prefixes=Silian_prefixes,
            require_enable_modules=Silian_require_enable_modules,
            require_check_dirty_words=Silian_dirty_word_check,
            use_url_manager=Silian_use_url_manager,
        )

        await Bot.process_message(Silian_session, message)

    @staticmethod
    async def on_c2c_message_create(message: C2CMessage):
        Silian_prefixes = None
        Silian_require_enable_modules = True

        Silian_target_id = f"{target_c2c_prefix}|{message.author.user_openid}"
        Silian_sender_id = f"{sender_prefix}|{message.author.user_openid}"
        if Silian_sender_id in Silian_ignored_sender:
            return

        Silian_reply_id = None
        if message.message_reference:
            Silian_reply_id = message.message_reference.message_id

        if message.content.strip().startswith("/"):
            Silian_prefixes = ["/"]
            Silian_require_enable_modules = False

        Silian_msg_chain = MessageChain.assign(message.content)

        Silian_session = await SessionInfo.assign(
            target_id=Silian_target_id,
            sender_id=Silian_sender_id,
            sender_name=message.author.user_openid[:6],
            target_from=target_c2c_prefix,
            sender_from=sender_prefix,
            client_name=client_name,
            message_id=str(message.id),
            reply_id=Silian_reply_id,
            messages=Silian_msg_chain,
            ctx_slot=Silian_ctx_id,
            prefixes=Silian_prefixes,
            require_enable_modules=Silian_require_enable_modules,
            require_check_dirty_words=Silian_dirty_word_check,
            use_url_manager=Silian_use_url_manager,
        )

        await Bot.process_message(Silian_session, message)


Silian_intents = botpy.Intents.none()
Silian_intents.public_guild_messages = True
Silian_intents.public_messages = True
Silian_intents.direct_message = True
if Config("qq_private_bot", False, table_name="bot_qqbot"):
    Silian_intents.guild_messages = True

Silian_client = MyClient(intents=Silian_intents, bot_log=None)

if Config("enable", False, table_name="bot_qqbot"):
    Silian_loop = asyncio.get_event_loop()
    Silian_loop.run_until_complete(Silian_client.start(appid=Silian_qqbot_appid, secret=Silian_qqbot_secret))
