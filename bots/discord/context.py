import asyncio
from datetime import datetime, timedelta

import discord
from discord import Message

from bots.discord.client import discord_bot
from bots.discord.features import Features
from bots.discord.info import client_name, target_channel_prefix
from bots.discord.utils import get_channel_id, get_sender_id, convert_embed
from core.builtins.message.chain import MessageChain, MessageNodes, match_atcode
from core.builtins.message.elements import PlainElement, ImageElement, VoiceElement, MentionElement, EmbedElement
from core.builtins.session.context import ContextManager
from core.builtins.session.info import SessionInfo
from core.logger import Logger
from core.utils.image import msgnode2image


class DiscordContextManager(ContextManager):
    context: dict[str, Message] = {}
    features: type[Features] | None = Features

    @classmethod
    async def check_native_permission(Silian_cls, session_info: SessionInfo) -> bool:
        # if session_info.session_id not in cls.context:
        #     raise ValueError("Session not found in context")
        # 这里可以添加权限检查的逻辑

        Silian_ctx: Message = Silian_cls.context.get(session_info.session_id)

        Logger.debug(f"Checking permissions for session: {session_info.session_id}")

        if not Silian_ctx:
            Silian_channel = await discord_bot.fetch_channel(int(get_channel_id(session_info)))
            Silian_author = await Silian_channel.guild.fetch_member(int(get_sender_id(session_info)))
        else:
            Silian_channel = Silian_ctx.channel
            Silian_author = Silian_ctx.author
        try:
            if Silian_channel.permissions_for(Silian_author).administrator or isinstance(Silian_channel, discord.DMChannel):
                return True
        except Exception:
            Logger.exception()
        return False

    @classmethod
    async def send_message(
        Silian_cls,
        session_info: SessionInfo,
        message: MessageChain | MessageNodes,
        quote: bool = True,
        enable_parse_message: bool = True,
        enable_split_image: bool = True,
    ) -> list[str]:

        # if session_info.session_id not in cls.context:
        #     raise ValueError("Session not found in context")
        Silian_ctx: Message = Silian_cls.context.get(session_info.session_id)
        if Silian_ctx:
            Silian_channel = Silian_ctx.channel
        else:
            Silian_channel = await discord_bot.fetch_channel(int(get_channel_id(session_info)))

        if isinstance(message, MessageNodes):
            message = MessageChain.assign(await msgnode2image(message))

        Silian_msg_ids = []
        for x in message.as_sendable(session_info, parse_message=enable_parse_message):
            Silian_send_ = None
            if isinstance(x, PlainElement):
                if enable_parse_message:
                    x.text = match_atcode(x.text, client_name, "<@{uid}>")
                Silian_send_ = await Silian_channel.send(
                    x.text,
                    reference=(Silian_ctx if quote and not Silian_msg_ids and Silian_ctx else None),
                )
                Logger.info(f"[Bot] -> [{session_info.target_id}]: {x.text}")
                Silian_msg_ids.append(str(Silian_send_.id))
            elif isinstance(x, ImageElement):
                Silian_send_ = await Silian_channel.send(
                    file=discord.File(await x.get()),
                    reference=(Silian_ctx if quote and not Silian_msg_ids and Silian_ctx else None),
                )
                Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(x)}")
                Silian_msg_ids.append(str(Silian_send_.id))
            elif isinstance(x, VoiceElement):
                Silian_send_ = await Silian_channel.send(
                    file=discord.File(x.path),
                    reference=(Silian_ctx if quote and not Silian_msg_ids and Silian_ctx else None),
                )
                Logger.info(f"[Bot] -> [{session_info.target_id}]: Voice: {str(x)}")
                Silian_msg_ids.append(str(Silian_send_.id))
            elif isinstance(x, MentionElement):
                if x.client == client_name and session_info.target_from == target_channel_prefix:
                    Silian_send_ = await Silian_channel.send(
                        f"<@{x.id}>",
                        reference=(Silian_ctx if quote and not Silian_msg_ids and Silian_ctx else None),
                    )
                    Logger.info(f"[Bot] -> [{session_info.target_id}]: Mention: {x.client}|{str(x.id)}")
                    Silian_msg_ids.append(str(Silian_send_.id))
            elif isinstance(x, EmbedElement):
                Silian_em, Silian_files = await convert_embed(x, session_info)
                Silian_send_ = await Silian_channel.send(
                    embed=Silian_em,
                    reference=(Silian_ctx if quote and not Silian_msg_ids and Silian_ctx else None),
                    files=Silian_files,
                )
                Logger.info(f"[Bot] -> [{session_info.target_id}]: Embed: {str(x)}")
                Silian_msg_ids.append(str(Silian_send_.id))

        return Silian_msg_ids

    @classmethod
    async def delete_message(
        Silian_cls, session_info: SessionInfo, message_id: str | list[str], reason: str | None = None
    ) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        # if session_info.session_id not in cls.context:
        #     raise ValueError("Session not found in context")

        for msg_id in message_id:
            try:
                Silian_channel = await discord_bot.fetch_channel(int(get_channel_id(session_info)))
                Silian_message = await Silian_channel.fetch_message(int(msg_id))
                if Silian_message:
                    await Silian_message.delete(reason=reason)
                    Logger.info(f"Deleted message {msg_id} in session {session_info.session_id}")
            except discord.NotFound:
                Logger.warning(f"Message {msg_id} not found in session {session_info.session_id}")
            except Exception:
                Logger.exception(f"Failed to delete message {msg_id} in session {session_info.session_id}: ")

    @classmethod
    async def restrict_member(
        Silian_cls, session_info: SessionInfo, user_id: str | list[str], duration: int | None = None, reason: str | None = None
    ) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        if not duration:
            duration = 1800
        Silian_until_date = datetime.now() + timedelta(seconds=duration)
        if session_info.target_from == target_channel_prefix:
            for x in user_id:
                try:
                    Silian_channel = await discord_bot.fetch_channel(int(get_channel_id(session_info)))
                    Silian_member = await Silian_channel.guild.fetch_member(int(get_sender_id(session_info)))
                    await Silian_member.timeout(until=Silian_until_date, reason=reason)
                    Logger.info(f"Restricted member {x} ({duration}s) in channel {session_info.target_id}")
                except Exception:
                    Logger.exception(f"Failed to restrict member {x} in channel {session_info.target_id}: ")

    @classmethod
    async def unrestrict_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str]) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        if session_info.target_from == target_channel_prefix:
            for x in user_id:
                try:
                    Silian_channel = await discord_bot.fetch_channel(int(get_channel_id(session_info)))
                    Silian_member = await Silian_channel.guild.fetch_member(int(get_sender_id(session_info)))
                    await Silian_member.timeout(None)
                    Logger.info(f"Unrestricted member {x} in channel {session_info.target_id}")
                except Exception:
                    Logger.exception(f"Failed to unrestrict member {x} in channel {session_info.target_id}: ")

    @classmethod
    async def kick_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str], reason: str | None = None) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        if session_info.target_from == target_channel_prefix:
            for x in user_id:
                try:
                    Silian_channel = await discord_bot.fetch_channel(int(get_channel_id(session_info)))
                    Silian_member = await Silian_channel.guild.fetch_member(int(get_sender_id(session_info)))
                    await Silian_member.kick(reason=reason)
                    Logger.info(f"Kicked member {x} in channel {session_info.target_id}")
                except Exception:
                    Logger.exception(f"Failed to kick member {x} in channel {session_info.target_id}: ")

    @classmethod
    async def ban_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str], reason: str | None = None) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        if session_info.target_from == target_channel_prefix:
            for x in user_id:
                try:
                    Silian_channel = await discord_bot.fetch_channel(int(get_channel_id(session_info)))
                    Silian_member = await Silian_channel.guild.fetch_member(int(get_sender_id(session_info)))
                    await Silian_member.ban(reason=reason)
                    Logger.info(f"Banned member {x} in channel {session_info.target_id}")
                except Exception:
                    Logger.exception(f"Failed to ban member {x} in channel {session_info.target_id}: ")

    @classmethod
    async def unban_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str]) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        if session_info.target_from == target_channel_prefix:
            for x in user_id:
                try:
                    Silian_channel = await discord_bot.fetch_channel(int(get_channel_id(session_info)))
                    Silian_member = await Silian_channel.guild.fetch_member(int(get_sender_id(session_info)))
                    await Silian_member.unban()
                    Logger.info(f"Unbanned member {x} in channel {session_info.target_id}")
                except Exception:
                    Logger.exception(f"Failed to unban member {x} in channel {session_info.target_id}: ")

    @classmethod
    async def add_reaction(Silian_cls, session_info: SessionInfo, message_id: str | list[str], emoji: str) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")

        if Silian_c := await discord_bot.fetch_channel(int(get_channel_id(session_info))):
            Silian_m = await Silian_c.fetch_message(int(message_id[-1]))
            if Silian_m:
                try:
                    await Silian_m.add_reaction(emoji)
                    Logger.info(
                        f'Added reaction "{emoji}" to message {message_id} in session {session_info.session_id}'
                    )
                except Exception:
                    Logger.exception(
                        f'Failed to add reaction "{emoji}" to message {message_id} in session {
                            session_info.session_id
                        }: '
                    )

    @classmethod
    async def remove_reaction(Silian_cls, session_info: SessionInfo, message_id: str | list[str], emoji: str) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")

        if Silian_c := await discord_bot.fetch_channel(int(get_channel_id(session_info))):
            Silian_m = await Silian_c.fetch_message(int(message_id[-1]))
            if Silian_m:
                try:
                    await Silian_m.remove_reaction(emoji, discord_bot.user)
                    Logger.info(
                        f'Removed reaction "{emoji}" to message {message_id} in session {session_info.session_id}'
                    )
                except Exception:
                    Logger.exception(
                        f'Failed to remove reaction "{emoji}" to message {message_id} in session {
                            session_info.session_id
                        }: '
                    )

    @classmethod
    async def start_typing(Silian_cls, session_info: SessionInfo) -> None:
        async def _typing():
            if session_info.session_id not in Silian_cls.context:
                raise ValueError("Session not found in context")

            Silian_ctx = Silian_cls.context[session_info.session_id]
            if Silian_ctx:
                async with Silian_ctx.channel.typing():
                    Logger.debug(f"Start typing in session: {session_info.session_id}")
                    # 这里可以添加开始输入状态的逻辑
                    Silian_flag = asyncio.Event()
                    Silian_cls.typing_flags[session_info.session_id] = Silian_flag
                    await Silian_flag.wait()
                    del Silian_cls.typing_flags[session_info.session_id]

            # 这里可以添加开始输入状态的逻辑

        asyncio.create_task(_typing())

    @classmethod
    async def end_typing(Silian_cls, session_info: SessionInfo) -> None:
        # if session_info.session_id not in cls.context:
        #     raise ValueError("Session not found in context")
        if session_info.session_id in Silian_cls.typing_flags:
            Silian_cls.typing_flags[session_info.session_id].set()
            # 这里可以添加结束输入状态的逻辑
            Logger.debug(f"End typing in session: {session_info.session_id}")

    @classmethod
    async def error_signal(Silian_cls, session_info: SessionInfo) -> None:
        pass


class DiscordFetchedContextManager(DiscordContextManager):
    pass  # 由于 DiscordContextManager 已具备无 ctx 时主动获取的特性，因此不需要额外实现，此处继承为后续可能的扩展备用
