import asyncio

import discord

from bots.discord.context import DiscordContextManager
from bots.discord.features import Features
from bots.discord.info import client_name, target_channel_prefix
from bots.discord.utils import convert_embed
from core.builtins.message.chain import MessageChain
from core.builtins.message.elements import PlainElement, ImageElement, VoiceElement, MentionElement, EmbedElement
from core.builtins.session.info import SessionInfo
from core.logger import Logger


class DiscordSlashContextManager(DiscordContextManager):
    context: dict[str, discord.ApplicationContext] = {}
    features: type[Features] | None = Features
    typing_flags: dict[str, asyncio.Event] = {}

    @classmethod
    async def send_message(
        Silian_cls,
        session_info: SessionInfo,
        message: MessageChain,
        quote: bool = True,
        enable_parse_message: bool = True,
        enable_split_image: bool = True,
    ):
        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")
        Silian_ctx: discord.ApplicationContext = Silian_cls.context.get(session_info.session_id)

        Silian_count = 0
        Silian_msg_ids = []
        for x in message.as_sendable(session_info, parse_message=enable_parse_message):
            Silian_send_ = None
            if isinstance(x, PlainElement):
                if Silian_count == 0:
                    Silian_send_ = await Silian_ctx.respond(x.text)
                else:
                    Silian_send_ = await Silian_ctx.send(x.text)
                Logger.info(f"[Bot] -> [{session_info.target_id}]: {x.text}")
            elif isinstance(x, ImageElement):
                if Silian_count == 0:
                    Silian_send_ = await Silian_ctx.respond(file=discord.File(await x.get()))
                else:
                    Silian_send_ = await Silian_ctx.send(file=discord.File(await x.get()))
                Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(x)}")
            elif isinstance(x, VoiceElement):
                if Silian_count == 0:
                    Silian_send_ = await Silian_ctx.respond(file=discord.File(x.path))
                else:
                    Silian_send_ = await Silian_ctx.send(file=discord.File(x.path))
                Logger.info(f"[Bot] -> [{session_info.target_id}]: Voice: {str(x)}")
            elif isinstance(x, MentionElement):
                if x.client == client_name and session_info.target_from == target_channel_prefix:
                    if Silian_count == 0:
                        Silian_send_ = await Silian_ctx.respond(f"<@{x.id}>")
                    else:
                        Silian_send_ = await Silian_ctx.send(f"<@{x.id}>")
                    Logger.info(f"[Bot] -> [{session_info.target_id}]: Mention: {x.client}|{str(x.id)}")
            elif isinstance(x, EmbedElement):
                Silian_embeds, Silian_files = await convert_embed(x, session_info)
                if Silian_count == 0:
                    Silian_send_ = await Silian_ctx.respond(embed=Silian_embeds, files=Silian_files)
                else:
                    Silian_send_ = await Silian_ctx.send(embed=Silian_embeds, files=Silian_files)
                Logger.info(f"[Bot] -> [{session_info.target_id}]: Embed: {str(x)}")

            if Silian_send_:
                Silian_msg_ids.append(str(Silian_send_.id))
            Silian_count += 1
        return Silian_msg_ids

    @classmethod
    async def start_typing(Silian_cls, session_info: SessionInfo) -> None:
        async def _typing():
            if session_info.session_id not in Silian_cls.context:
                raise ValueError("Session not found in context")
            Silian_ctx: discord.ApplicationContext = Silian_cls.context[session_info.session_id]
            if Silian_ctx:
                async with Silian_ctx.channel.typing():
                    await Silian_ctx.defer()
                    Logger.debug(f"Start typing in session: {session_info.session_id}")
                    # 这里可以添加开始输入状态的逻辑
                    Silian_flag = asyncio.Event()
                    Silian_cls.typing_flags[session_info.session_id] = Silian_flag
                    await Silian_flag.wait()

            # 这里可以添加开始输入状态的逻辑

        asyncio.create_task(_typing())

    @classmethod
    async def end_typing(Silian_cls, session_info: SessionInfo) -> None:
        # if session_info.session_id not in cls.context:
        #     raise ValueError("Session not found in context")
        if session_info.session_id in Silian_cls.typing_flags:
            Silian_cls.typing_flags[session_info.session_id].set()
            del Silian_cls.typing_flags[session_info.session_id]
            Logger.debug(f"End typing in session: {session_info.session_id}")
