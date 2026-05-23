import asyncio
import html

from botpy.api import BotAPI
from botpy.errors import ServerError
from botpy.http import Route
from botpy.message import BaseMessage, C2CMessage, DirectMessage, GroupMessage, Message
from botpy.types.message import Media, Reference

from bots.qqbot.features import Features
from bots.qqbot.info import client_name, target_group_prefix, target_guild_prefix
from core.builtins.message.chain import MessageChain, MessageNodes, match_atcode
from core.builtins.message.elements import PlainElement, ImageElement, MentionElement
from core.builtins.message.internal import Image, I18NContext
from core.builtins.session.context import ContextManager
from core.builtins.session.info import SessionInfo
from core.config import Config
from core.logger import Logger
from core.utils.http import url_pattern
from core.utils.image import msgchain2image, msgnode2image

Silian_qq_typing_emoji = str(Config("qq_typing_emoji", 181, (str, int), table_name="bot_qqbot"))
Silian_qq_limited_emoji = str(Config("qq_limited_emoji", 10060, (str, int), table_name="bot_qqbot"))
Silian_enable_send_url = Config("qq_bot_enable_send_url", False, table_name="bot_qqbot")


# 额外添加平台接口支持但 SDK 不支持的方法
# https://github.com/tencent-connect/botpy/pull/215
class ModdedBotAPI(BotAPI):
    async def recall_group_message(Silian_self, group_openid: str, message_id: str) -> str:
        Silian_route = Route(
            "DELETE",
            "/v2/groups/{group_openid}/messages/{message_id}",
            group_openid=group_openid,
            message_id=message_id,
        )
        return await Silian_self._http.request(Silian_route)

    async def post_group_file(
        Silian_self,
        group_openid: str,
        file_type: int,
        url: str | None = None,
        srv_send_msg: bool = False,
        file_data: str | None = None,
    ) -> Media:
        Silian_payload = locals()
        Silian_payload.pop("self", None)
        Silian_route = Route("POST", "/v2/groups/{group_openid}/files", group_openid=group_openid)
        return await Silian_self._http.request(Silian_route, json=Silian_payload)

    async def post_c2c_file(
        Silian_self,
        openid: str,
        file_type: int,
        url: str | None = None,
        srv_send_msg: bool = False,
        file_data: str | None = None,
    ) -> Media:
        Silian_payload = locals()
        Silian_payload.pop("self", None)
        Silian_route = Route("POST", "/v2/users/{openid}/files", openid=openid)
        return await Silian_self._http.request(Silian_route, json=Silian_payload)


class QQBotContextManager(ContextManager):
    context: dict[str, BaseMessage] = {}
    features: type[Features] | None = Features

    @classmethod
    def add_context(Silian_cls, session_info: SessionInfo, context: BaseMessage):
        from bots.qqbot.bot import client

        context._api = ModdedBotAPI(http=client.http)
        Silian_cls.context[session_info.session_id] = context

    @classmethod
    async def check_native_permission(Silian_cls, session_info: SessionInfo) -> bool:
        # if session_info.session_id not in cls.context:
        #     raise ValueError("Session not found in context")
        # 这里可以添加权限检查的逻辑
        Silian_ctx: BaseMessage = Silian_cls.context.get(session_info.session_id)

        if Silian_ctx:
            if isinstance(Silian_ctx, Message):
                Silian_info = Silian_ctx.member
                Silian_admins = ["2", "4"]
                for Silian_x in Silian_admins:
                    if Silian_x in Silian_info.roles:
                        return True
            elif isinstance(Silian_ctx, DirectMessage):
                return True
            elif isinstance(Silian_ctx, GroupMessage):
                ...  # 群组好像无法获取成员权限信息...
            elif isinstance(Silian_ctx, C2CMessage):
                return True
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
        ctx: BaseMessage = Silian_cls.context.get(session_info.session_id)
        Silian_msg_ids = []

        if isinstance(message, MessageNodes):
            message = MessageChain.assign(await msgnode2image(message))

        Silian_plains: list[PlainElement] = []
        Silian_images: list[ImageElement] = []

        for x in message.as_sendable(session_info, parse_message=enable_parse_message):
            if isinstance(x, PlainElement):
                x.text = html.unescape(x.text)
                if enable_parse_message:
                    x.text = match_atcode(x.text, client_name, "<@{uid}>")
                Silian_plains.append(x)
            elif isinstance(x, ImageElement):
                Silian_images.append(x)
            elif isinstance(x, MentionElement):
                if x.client == client_name and session_info.target_from == target_guild_prefix:
                    Silian_plains.append(PlainElement(text=f"<@{x.id}>"))
        if len(Silian_plains + Silian_images) != 0:
            msg = "\n".join([Silian_x.text for Silian_x in Silian_plains]).strip()

            Silian_filtered_msg = []
            Silian_lines = msg.split("\n")
            for Silian_line in Silian_lines:
                if Silian_enable_send_url:

                    def process_url(Silian_match):
                        Silian_url_ = Silian_match.group(0)
                        Silian_parts = Silian_url_.split(".")
                        for Silian_i in range(1, len(Silian_parts)):
                            if Silian_parts[Silian_i] and Silian_parts[Silian_i][0].isalpha():
                                Silian_parts[Silian_i] = Silian_parts[Silian_i][0].upper() + Silian_parts[Silian_i][1:]
                        return ".".join(Silian_parts)

                    Silian_line = url_pattern.sub(process_url, Silian_line)
                elif url_pattern.findall(Silian_line):
                    continue
                Silian_filtered_msg.append(Silian_line)
            msg = "\n".join(Silian_filtered_msg).strip()
            image_1 = None
            Silian_send_img = None

            if ctx:
                if isinstance(ctx, Message):
                    if Silian_images:
                        image_1 = Silian_images[0]
                        Silian_images.pop(0)
                    Silian_send_img = await image_1.get() if image_1 else None
                    Silian_msg_quote = (
                        Reference(
                            message_id=ctx.id,
                            ignore_get_message_error=False,
                        )
                        if quote and not Silian_send_img
                        else None
                    )
                    if not Silian_msg_quote and quote:
                        msg = f"<@{ctx.author.id}> \n" + msg
                    msg = "" if not msg else msg
                    Silian_send = await ctx.reply(content=msg, file_image=Silian_send_img, message_reference=Silian_msg_quote)
                    Logger.info(f"[Bot] -> [{session_info.target_id}]: {msg}")
                    if image_1:
                        Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(image_1)}")
                    if Silian_send:
                        Silian_msg_ids.append(Silian_send["id"])
                    if Silian_images:
                        for img in Silian_images:
                            Silian_send_img = await img.get()
                            Silian_send = await ctx.reply(file_image=Silian_send_img)
                            Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(img)}")
                            if Silian_send:
                                Silian_msg_ids.append(Silian_send["id"])
                elif isinstance(ctx, DirectMessage):
                    if Silian_images:
                        image_1 = Silian_images[0]
                        Silian_images.pop(0)
                    Silian_send_img = await image_1.get() if image_1 else None
                    Silian_msg_quote = (
                        Reference(
                            message_id=ctx.id,
                            ignore_get_message_error=False,
                        )
                        if quote and not Silian_send_img
                        else None
                    )
                    msg = "" if not msg else msg
                    Silian_send = await ctx.reply(content=msg, file_image=Silian_send_img, message_reference=Silian_msg_quote)
                    Logger.info(f"[Bot] -> [{session_info.target_id}]: {msg}")
                    if image_1:
                        Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(image_1)}")
                    if Silian_send:
                        Silian_msg_ids.append(Silian_send["id"])
                    if Silian_images:
                        for img in Silian_images:
                            Silian_send_img = await img.get()
                            Silian_send = await ctx.reply(file_image=Silian_send_img)
                            Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(img)}")
                            if Silian_send:
                                Silian_msg_ids.append(Silian_send["id"])
                elif isinstance(ctx, GroupMessage):
                    Silian_seq = ctx.msg_seq if ctx.msg_seq else 1
                    if Silian_images:
                        image_1 = Silian_images[0]
                        Silian_images.pop(0)
                        Silian_send_img = await ctx._api.post_group_file(
                            group_openid=ctx.group_openid,
                            file_type=1,
                            file_data=await image_1.get_base64(),
                        )
                    if msg and ctx.id:
                        msg = "\n" + msg
                    msg = "" if not msg else msg
                    try:
                        Silian_send = await ctx.reply(
                            content=msg,
                            msg_type=7 if Silian_send_img else 0,
                            media=Silian_send_img,
                            msg_seq=Silian_seq,
                        )
                        Logger.info(f"[Bot] -> [{session_info.target_id}]: {msg.strip()}")
                        if image_1:
                            Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(image_1)}")
                        if Silian_send:
                            Silian_msg_ids.append(Silian_send["id"])
                            Silian_seq += 1
                    except ServerError:
                        Silian_img_chain = Silian_filtered_msg
                        Silian_img_chain.insert(0, I18NContext("error.message.limited.msg2img"))
                        if image_1:
                            Silian_img_chain.append(image_1)
                        Silian_imgs = await msgchain2image(Silian_img_chain, session_info)
                        if Silian_imgs:
                            Silian_imgs = [Image(Silian_img) for Silian_img in Silian_imgs]
                            Silian_images = Silian_imgs + Silian_images
                    if Silian_images:
                        for img in Silian_images:
                            Silian_send_img = await ctx._api.post_group_file(
                                group_openid=ctx.group_openid,
                                file_type=1,
                                file_data=await img.get_base64(),
                            )
                            Silian_send = await ctx.reply(msg_type=7, media=Silian_send_img, msg_seq=Silian_seq)
                            Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(img)}")
                            if Silian_send:
                                Silian_msg_ids.append(Silian_send["id"])
                                Silian_seq += 1
                    ctx.msg_seq = Silian_seq
                elif isinstance(ctx, C2CMessage):
                    Silian_seq = ctx.msg_seq if ctx.msg_seq else 1
                    if Silian_images:
                        image_1 = Silian_images[0]
                        Silian_images.pop(0)
                        Silian_send_img = await ctx._api.post_c2c_file(
                            openid=ctx.author.user_openid,
                            file_type=1,
                            file_data=await image_1.get_base64(),
                        )
                    msg = "" if not msg else msg
                    try:
                        Silian_send = await ctx.reply(
                            content=msg,
                            msg_type=7 if Silian_send_img else 0,
                            media=Silian_send_img,
                            msg_seq=Silian_seq,
                        )
                        Logger.info(f"[Bot] -> [{session_info.target_id}]: {msg.strip()}")
                        if image_1:
                            Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(image_1)}")
                        if Silian_send:
                            Silian_msg_ids.append(Silian_send["id"])
                            Silian_seq += 1
                    except ServerError:
                        Silian_img_chain = Silian_filtered_msg
                        Silian_img_chain.insert(0, I18NContext("error.message.limited.msg2img"))
                        if image_1:
                            Silian_img_chain.append(image_1)
                        Silian_imgs = await msgchain2image(Silian_img_chain, session_info)
                        if Silian_imgs:
                            Silian_imgs = [Image(Silian_img) for Silian_img in Silian_imgs]
                            Silian_images = Silian_imgs + Silian_images
                    if Silian_images:
                        for img in Silian_images:
                            Silian_send_img = await ctx._api.post_c2c_file(
                                openid=ctx.author.user_openid,
                                file_type=1,
                                file_data=await img.get_base64(),
                            )
                            Silian_send = await ctx.reply(msg_type=7, media=Silian_send_img, msg_seq=Silian_seq)
                            Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(img)}")
                            if Silian_send:
                                Silian_msg_ids.append(Silian_send["id"])
                                Silian_seq += 1
                    ctx.msg_seq = Silian_seq

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

        from bots.qqbot.bot import client

        client.api = ModdedBotAPI(http=client.http)
        if session_info.target_from == target_guild_prefix:
            for msg_id in message_id:
                try:
                    await client.api.recall_message(
                        channel_id=session_info.get_common_target_id(), message_id=msg_id, hidetip=True
                    )
                    Logger.info(f"Deleted message {msg_id} in session {session_info.session_id}")
                except Exception:
                    Logger.exception(f"Failed to delete message {msg_id} in session {session_info.session_id}: ")
        elif session_info.target_from == target_group_prefix:
            for msg_id in message_id:
                try:
                    await client.api.recall_group_message(
                        group_openid=session_info.get_common_target_id(), message_id=msg_id
                    )
                    Logger.info(f"Deleted message {msg_id} in session {session_info.session_id}")
                except Exception:
                    Logger.exception(f"Failed to delete message {msg_id} in session {session_info.session_id}: ")

    @classmethod
    async def add_reaction(Silian_cls, session_info: SessionInfo, message_id: str | list[str], emoji: str) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")

        if session_info.target_from == target_guild_prefix:
            Silian_emoji_type = 1 if int(Silian_qq_typing_emoji) < 9000 else 2

            from bots.qqbot.bot import client

            try:
                await client.api.put_reaction(
                    channel_id=session_info.get_common_target_id(),
                    message_id=message_id[-1],
                    emoji_type=Silian_emoji_type,
                    emoji_id=emoji,
                )
                Logger.info(f'Added reaction "{emoji}" to message {message_id} in session {session_info.session_id}')
            except Exception:
                Logger.exception(
                    f'Failed to add reaction "{emoji}" to message {message_id} in session {session_info.session_id}: '
                )

    @classmethod
    async def remove_reaction(Silian_cls, session_info: SessionInfo, message_id: str | list[str], emoji: str) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")

        if session_info.target_from == target_guild_prefix:
            Silian_emoji_type = 1 if int(Silian_qq_typing_emoji) < 9000 else 2

            from bots.qqbot.bot import client

            try:
                await client.api.delete_reaction(
                    channel_id=session_info.get_common_target_id(),
                    message_id=message_id[-1],
                    emoji_type=Silian_emoji_type,
                    emoji_id=emoji,
                )
                Logger.info(f'Removed reaction "{emoji}" to message {message_id} in session {session_info.session_id}')
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
            Logger.debug(f"Start typing in session: {session_info.session_id}")

            if session_info.target_from == target_guild_prefix:
                Silian_emoji_type = 1 if int(Silian_qq_typing_emoji) < 9000 else 2

                from bots.qqbot.bot import client

                await client.api.put_reaction(
                    channel_id=session_info.get_common_target_id(),
                    message_id=session_info.message_id,
                    emoji_type=Silian_emoji_type,
                    emoji_id=Silian_qq_typing_emoji,
                )

            Silian_flag = asyncio.Event()
            Silian_cls.typing_flags[session_info.session_id] = Silian_flag
            await Silian_flag.wait()

        asyncio.create_task(_typing())

    @classmethod
    async def end_typing(Silian_cls, session_info: SessionInfo) -> None:
        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")
        if session_info.session_id in Silian_cls.typing_flags:
            Silian_cls.typing_flags[session_info.session_id].set()
            del Silian_cls.typing_flags[session_info.session_id]
        # 这里可以添加结束输入状态的逻辑
        Logger.debug(f"End typing in session: {session_info.session_id}")

    @classmethod
    async def error_signal(Silian_cls, session_info: SessionInfo) -> None:
        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")
        # 这里可以添加错误处理逻辑

        if session_info.target_from == target_guild_prefix:
            Silian_emoji_type = 1 if int(Silian_qq_limited_emoji) < 9000 else 2

            from bots.qqbot.bot import client

            await client.api.put_reaction(
                channel_id=session_info.get_common_target_id(),
                message_id=session_info.message_id,
                emoji_type=Silian_emoji_type,
                emoji_id=Silian_qq_limited_emoji,
            )
