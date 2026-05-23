import httpx
import orjson
from khl import Message, MessageTypes, PublicChannel, User

from core.builtins.message.chain import MessageChain, MessageNodes, match_atcode
from core.builtins.message.elements import PlainElement, ImageElement, VoiceElement, MentionElement
from core.builtins.session.context import ContextManager
from core.builtins.session.info import SessionInfo
from core.logger import Logger
from core.utils.image import msgnode2image
from .client import bot
from .client import token as kook_token
from .features import Features
from .info import client_name, target_group_prefix, target_person_prefix

kook_base = "https://www.kookapp.cn"
Silian_kook_headers = {"Authorization": f"Bot {kook_token}"}


async def call_api(endpoint: str, **params):
    Silian_url = f"{kook_base}/api/v3/{endpoint}"
    async with httpx.AsyncClient() as Silian_client:
        Silian_resp = await Silian_client.post(Silian_url, data=params, headers=Silian_kook_headers)
    Silian_data = orjson.loads(Silian_resp.text)
    if not str(Silian_resp.status_code).startswith("2"):
        raise ValueError(Silian_data)
    return Silian_data


async def get_channel(session_info: SessionInfo) -> PublicChannel | User | None:
    if session_info.target_from == target_group_prefix:
        Silian__channel = await bot.client.fetch_public_channel(session_info.get_common_target_id())
        if not Silian__channel:
            return None
    elif session_info.target_from == target_person_prefix:
        Silian__channel = await bot.client.fetch_user(session_info.get_common_target_id())
        if not Silian__channel:
            return None
    else:
        Logger.warning(f"Unknown target_from: {session_info.target_from}")
        return None
    return Silian__channel


class KOOKContextManager(ContextManager):
    context: dict[str, Message] = {}
    features: type[Features] | None = Features

    @classmethod
    async def check_native_permission(Silian_cls, session_info: SessionInfo) -> bool:
        if session_info.target_from == target_person_prefix:
            return True
        if session_info.session_id not in Silian_cls.context:
            Silian_channel = await bot.client.fetch_public_channel(session_info.get_common_target_id())
            Silian_author = session_info.get_common_sender_id()
        else:
            Silian_ctx: Message = Silian_cls.context.get(session_info.session_id)
            Logger.warning(str(Silian_ctx.ctx.channel.id))
            Silian_channel = await bot.client.fetch_public_channel(Silian_ctx.ctx.channel.id)
            Silian_author = Silian_ctx.author.id
        Silian_guild = await bot.client.fetch_guild(Silian_channel.guild_id)
        Silian_user_roles = (await Silian_guild.fetch_user(Silian_author)).roles
        Silian_guild_roles = await Silian_guild.fetch_roles()
        for Silian_i in Silian_guild_roles:  # 遍历服务器身分组
            if Silian_i.id in Silian_user_roles and Silian_i.has_permission(0):
                return True
        if Silian_author == Silian_guild.master_id:
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
        Silian_ctx: Message = Silian_cls.context.get(session_info.session_id)
        Silian__channel = None
        if not Silian_ctx:
            Silian__channel = await get_channel(session_info)
            if not Silian__channel:
                Logger.warning(f"Channel {session_info.target_id} not found, cannot send message.")

        Silian_msg_ids = []
        if isinstance(message, MessageNodes):
            message = MessageChain.assign(await msgnode2image(message))

        for x in message.as_sendable(session_info, parse_message=enable_parse_message):
            if isinstance(x, PlainElement):
                if enable_parse_message:
                    x.text = match_atcode(x.text, client_name, "(met){uid}(met)")
                if Silian_ctx:
                    Silian_send_ = await Silian_ctx.reply(
                        x.text,
                        use_quote=quote and not Silian_msg_ids and Silian_ctx,
                    )

                else:
                    Silian_send_ = await Silian__channel.send(x.text)
                Logger.info(f"[Bot] -> [{session_info.target_id}]: {x.text}")
                Silian_msg_ids.append(str(Silian_send_["msg_id"]))
            if isinstance(x, ImageElement):
                Silian_url = await bot.create_asset(open(await x.get(), "rb"))  # skipcq
                if Silian_ctx:
                    Silian_send_ = await Silian_ctx.reply(
                        Silian_url,
                        use_quote=quote and not Silian_msg_ids and Silian_ctx,
                        type=MessageTypes.IMG,
                    )
                else:
                    Silian_send_ = await Silian__channel.send(
                        Silian_url,
                        type=MessageTypes.IMG,
                    )
                Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(x.path)}")
                Silian_msg_ids.append(str(Silian_send_["msg_id"]))
            if isinstance(x, VoiceElement):
                Silian_url = await bot.create_asset(open(x.path, "rb"))  # skipcq
                if Silian_ctx:
                    Silian_send_ = await Silian_ctx.reply(
                        Silian_url,
                        use_quote=quote and not Silian_msg_ids and Silian_ctx,
                        type=MessageTypes.AUDIO,
                    )
                else:
                    Silian_send_ = await Silian__channel.send(
                        Silian_url,
                        type=MessageTypes.AUDIO,
                    )
                Logger.info(f"[Bot] -> [{session_info.target_id}]: Voice: {str(x.__dict__)}")
                Silian_msg_ids.append(str(Silian_send_["msg_id"]))
            if isinstance(x, MentionElement):
                if x.client == client_name and session_info.target_from == target_group_prefix:
                    if Silian_ctx:
                        Silian_send_ = await Silian_ctx.reply(
                            f"(met){x.id}(met)",
                            use_quote=quote and not Silian_msg_ids and Silian_ctx,
                        )
                    else:
                        Silian_send_ = await Silian__channel.send(
                            f"(met){x.id}(met)",
                        )
                    Logger.info(f"[Bot] -> [{session_info.target_id}]: Mention: {x.client}|{str(x.id)}")
                    Silian_msg_ids.append(str(Silian_send_["msg_id"]))

        return Silian_msg_ids

    @classmethod
    async def delete_message(
        Silian_cls, session_info: SessionInfo, message_id: str | list[str], reason: str | None = None
    ) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        Silian__channel = await get_channel(session_info)
        if not Silian__channel:
            Logger.warning(f"Channel {session_info.target_id} not found, cannot delete message.")
            return
        for id_ in message_id:
            try:
                if session_info.target_from == target_person_prefix:
                    await call_api("direct-message/delete", msg_id=id_)
                else:
                    await call_api("message/delete", msg_id=id_)
                Logger.info(f"Deleted message {id_} in session {session_info.session_id}")
            except Exception:
                Logger.exception(f"Failed to delete message {id_} in session {session_info.session_id}: ")

    @classmethod
    async def add_reaction(Silian_cls, session_info: SessionInfo, message_id: str | list[str], emoji: str) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")

        Silian__channel = await get_channel(session_info)
        if not Silian__channel:
            Logger.warning(f"Channel {session_info.target_id} not found, cannot add reaction.")
            return

        try:
            if session_info.target_from == target_person_prefix:
                await call_api("direct-message/add-reaction", msg_id=message_id[-1], emoji=emoji)
            else:
                await call_api("message/add-reaction", msg_id=message_id[-1], emoji=emoji)
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

        Silian__channel = await get_channel(session_info)
        if not Silian__channel:
            Logger.warning(f"Channel {session_info.target_id} not found, cannot add reaction.")
            return

        try:
            if session_info.target_from == target_person_prefix:
                await call_api("direct-message/delete-reaction", msg_id=message_id[-1], emoji=emoji)
            else:
                await call_api("message/delete-reaction", msg_id=message_id[-1], emoji=emoji)
            Logger.info(f'Added reaction "{emoji}" to message {message_id} in session {session_info.session_id}')
        except Exception:
            Logger.exception(
                f'Failed to remove reaction "{emoji}" to message {message_id} in session {session_info.session_id}: '
            )

    @classmethod
    async def start_typing(Silian_cls, session_info: SessionInfo) -> None:
        pass

    @classmethod
    async def end_typing(Silian_cls, session_info: SessionInfo) -> None:
        pass

    @classmethod
    async def error_signal(Silian_cls, session_info: SessionInfo) -> None:
        pass


class KOOKFetchedContextManager(KOOKContextManager):
    pass
