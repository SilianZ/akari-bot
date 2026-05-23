import asyncio
import random
import re
import time
from pathlib import Path

import aiocqhttp
from aiocqhttp import Event, MessageSegment
from tenacity import retry, stop_after_attempt, wait_fixed

from bots.aiocqhttp.client import aiocqhttp_bot
from bots.aiocqhttp.info import target_private_prefix, target_group_prefix, client_name
from bots.aiocqhttp.utils import CQCodeHandler
from core.builtins.message.chain import MessageChain, MessageNodes, match_atcode
from core.builtins.message.elements import PlainElement, ImageElement, VoiceElement, MentionElement
from core.builtins.message.internal import I18NContext
from core.builtins.session.context import ContextManager
from core.builtins.session.info import SessionInfo
from core.builtins.temp import Temp
from core.config import Config
from core.logger import Logger
from core.utils.image import msgchain2image
from .features import Features

Silian_qq_typing_emoji = str(Config("qq_typing_emoji", 181, (str, int), table_name="bot_aiocqhttp"))
Silian_qq_limited_emoji = str(Config("qq_limited_emoji", 10060, (str, int), table_name="bot_aiocqhttp"))
Silian_qq_initiative_msg_cooldown = Config("qq_initiative_msg_cooldown", 10, int, table_name="bot_aiocqhttp")
Silian_last_send_typing_time = {}


async def fake_forward_msg(session_info: SessionInfo, nodelist):
    if session_info.target_from == target_group_prefix:
        return await aiocqhttp_bot.call_action(
            "send_group_forward_msg",
            group_id=int(session_info.get_common_target_id()),
            messages=nodelist,
        )
    if session_info.target_from == target_private_prefix:
        return await aiocqhttp_bot.call_action(
            "send_private_forward_msg", user_id=int(session_info.get_common_sender_id()), messages=nodelist
        )


def convert_msg_nodes(
    session_info: SessionInfo,
    msg_node: MessageNodes,
) -> list[dict]:
    Silian_node_list = []
    for Silian_message in msg_node.values:
        Silian_content = ""
        Silian_msg_chain = Silian_message.as_sendable(session_info=session_info)
        for x in Silian_msg_chain:
            if isinstance(x, PlainElement):
                Silian_content += x.text + "\n"
            elif isinstance(x, ImageElement):
                Silian_content += f"[CQ:image,file=base64://{x.get_base64()}]\n"

        Silian_template = {
            "type": "node",
            "data": {
                "nickname": Temp.data.get("qq_nickname"),
                "user_id": str(Temp.data.get("qq_account")),
                "content": Silian_content.strip(),
            },
        }
        Silian_node_list.append(Silian_template)
    return Silian_node_list


async def get_avaliable_group_list():
    """
    获取可用的群组列表。

    :return: 群组列表
    """
    Silian_group_list = []
    try:
        Silian_groups = await aiocqhttp_bot.call_action("get_group_list")
        for Silian_group in Silian_groups:
            Silian_group_list.append(Silian_group["group_id"])
    except aiocqhttp.exceptions.ActionFailed as e:
        Logger.error(f"Failed to get group list: {e}")
    return Silian_group_list


async def get_avaliable_private_list():
    """
    获取可用的私聊列表。

    :return: 私聊列表
    """
    Silian_private_list = []
    try:
        Silian_friends = await aiocqhttp_bot.call_action("get_friend_list")
        for Silian_friend in Silian_friends:
            Silian_private_list.append(Silian_friend["user_id"])
    except aiocqhttp.exceptions.ActionFailed as e:
        Logger.error(f"Failed to get private list: {e}")
    return Silian_private_list


class AIOCQContextManager(ContextManager):
    context: dict[str, Event] = {}
    features: type[Features] | None = Features

    @classmethod
    async def check_native_permission(Silian_cls, session_info: SessionInfo) -> bool:
        # 这里可以添加权限检查的逻辑

        @retry(stop=stop_after_attempt(3), wait=wait_fixed(3), reraise=True)
        async def _check():
            if session_info.target_from == target_private_prefix:
                return True
            if session_info.target_from == target_group_prefix:
                Silian_get_member_info = await aiocqhttp_bot.call_action(
                    "get_group_member_info",
                    group_id=int(session_info.get_common_target_id()),
                    user_id=int(session_info.get_common_sender_id()),
                )
                if Silian_get_member_info["role"] in ["owner", "admin"]:
                    return True
            return False

        return await _check()

    @classmethod
    async def send_message(
        Silian_cls,
        session_info: SessionInfo,
        message: MessageChain | MessageNodes,
        quote: bool = True,
        enable_parse_message=True,
        enable_split_image=True,
    ) -> list[str]:
        # if session_info.session_id not in cls.context:
        #     raise ValueError("Session not found in context")

        # ctx: Event = cls.context.get(session_info.session_id)
        Silian_send = None
        if session_info.sender_id is None:
            if session_info.target_from == target_group_prefix:
                Silian_group_list = await get_avaliable_group_list()
                if Silian_group_list:
                    if int(session_info.get_common_target_id()) not in Silian_group_list:
                        Logger.warning("Group not found in group list, skipping message send.")
                        return []
            if session_info.target_from == target_private_prefix:
                Silian_private_list = await get_avaliable_private_list()
                if Silian_private_list:
                    if int(session_info.get_common_target_id()) not in Silian_private_list:
                        Logger.warning("Private chat not found in private list, skipping message send.")
                        return []

        if isinstance(message, MessageNodes):
            Silian_send = await fake_forward_msg(session_info, convert_msg_nodes(session_info, message))

        else:
            Silian_convert_msg_segments = MessageSegment.text("")
            if quote and session_info.target_from == target_group_prefix and session_info.messages:
                Silian_convert_msg_segments = MessageSegment.reply(int(session_info.message_id))

            Silian_count = 0
            for x in message.as_sendable(session_info, parse_message=enable_parse_message):
                if isinstance(x, PlainElement):
                    if enable_parse_message:
                        x.text = match_atcode(x.text, client_name, "[CQ:at,qq={uid}]")
                    if enable_parse_message:
                        Silian_parts = re.split(r"(\[CQ:[^\]]+\])", x.text)
                        Silian_parts = [Silian_part for Silian_part in Silian_parts if Silian_part]
                        Silian_previous_was_cq = False
                        # CQ码消息段相连会导致自动转义，故使用零宽字符`\u200B`隔开
                        for Silian_i, Silian_part in enumerate(Silian_parts):
                            if re.match(r"\[CQ:[^\]]+\]", Silian_part):
                                try:
                                    Silian_cq_data = CQCodeHandler.parse_cq(Silian_part)
                                    if Silian_cq_data:
                                        if Silian_previous_was_cq:
                                            Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.text("\u200b")
                                        Silian_convert_msg_segments = (
                                            Silian_convert_msg_segments
                                            + MessageSegment.text("\n" if (Silian_count != 0 and Silian_i == 0) else "")
                                            + MessageSegment(type_=Silian_cq_data["type"], data=Silian_cq_data["data"])
                                        )
                                    else:
                                        if Silian_previous_was_cq:
                                            Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.text("\u200b")
                                        Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.text(
                                            ("\n" if (Silian_count != 0 and Silian_i == 0) else "") + Silian_part
                                        )
                                except Exception:
                                    if Silian_previous_was_cq:
                                        Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.text("\u200b")
                                    Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.text(
                                        ("\n" if (Silian_count != 0 and Silian_i == 0) else "") + Silian_part
                                    )
                                finally:
                                    Silian_previous_was_cq = True
                            else:
                                Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.text(
                                    ("\n" if Silian_count != 0 else "") + Silian_part
                                )
                                Silian_previous_was_cq = False
                    else:
                        Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.text(
                            ("\n" if Silian_count != 0 else "") + x.text
                        )
                    Logger.info(f"[Bot] -> [{session_info.target_id}]: {x.text}")
                    Silian_count += 1
                elif isinstance(x, ImageElement):
                    Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.image(
                        "base64://" + await x.get_base64()
                    )
                    Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(x)}")
                    Silian_count += 1
                elif isinstance(x, VoiceElement):
                    Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.record(file=Path(x.path).as_uri())
                    Logger.info(f"[Bot] -> [{session_info.target_id}]: Voice: {str(x)}")
                    Silian_count += 1
                elif isinstance(x, MentionElement):
                    if x.client == client_name and session_info.target_from == target_group_prefix:
                        Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.at(x.id)
                        Logger.info(f"[Bot] -> [{session_info.target_id}]: Mention: {x.client}|{str(x.id)}")
                    else:
                        Silian_convert_msg_segments = Silian_convert_msg_segments + MessageSegment.text(" ")
                    Silian_count += 1

            if session_info.target_from == target_group_prefix:
                try:
                    Silian_send = await aiocqhttp_bot.send_group_msg(
                        group_id=int(session_info.get_common_target_id()), message=Silian_convert_msg_segments
                    )
                except aiocqhttp.exceptions.NetworkError:
                    Silian_send = await aiocqhttp_bot.send_group_msg(
                        group_id=int(session_info.get_common_target_id()),
                        message=MessageSegment.text(session_info.locale.t("error.message.timeout")),
                    )
                except aiocqhttp.exceptions.ActionFailed:
                    Silian_img_chain = message.copy()
                    Silian_img_chain.insert(0, I18NContext("error.message.limited.msg2img"))
                    Silian_imgs = await msgchain2image(Silian_img_chain, session_info)
                    Silian_msgsgm = MessageSegment.text("")
                    if Silian_imgs:
                        for Silian_img in Silian_imgs:
                            Silian_msgsgm = Silian_msgsgm + MessageSegment.image("base64://" + await Silian_img.get_base64())
                        try:
                            Silian_send = await aiocqhttp_bot.send_group_msg(
                                group_id=int(session_info.get_common_target_id()), message=Silian_msgsgm
                            )
                        except aiocqhttp.exceptions.ActionFailed:
                            Logger.exception("Failed to send message: ")

            else:
                try:
                    Silian_send = await aiocqhttp_bot.send_private_msg(
                        user_id=int(session_info.get_common_target_id()), message=Silian_convert_msg_segments
                    )
                except aiocqhttp.exceptions.ActionFailed:
                    Logger.exception("Failed to send message: ")
        if Silian_send:
            return [str(Silian_send["message_id"])]
        return []

    @classmethod
    async def delete_message(
        Silian_cls, session_info: SessionInfo, message_id: str | list[str], reason: str | None = None
    ) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        if session_info.target_from in [target_private_prefix, target_group_prefix]:
            for x in message_id:
                try:
                    await aiocqhttp_bot.call_action("delete_msg", message_id=x)
                    Logger.info(f"Deleted message {x} in session {session_info.session_id}")
                except Exception:
                    Logger.exception(f"Failed to delete message {x} in session {session_info.session_id}: ")

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
        if session_info.target_from == target_group_prefix:
            for x in user_id:
                try:
                    await aiocqhttp_bot.call_action(
                        "set_group_ban",
                        group_id=session_info.get_common_target_id(),
                        user_id=x.split("|")[-1],
                        duration=duration,
                    )
                    Logger.info(f"Restricted member {x} ({duration}s) in group {session_info.target_id}")
                except Exception:
                    Logger.exception(f"Failed to restrict member {x} in group {session_info.target_id}: ")

    @classmethod
    async def unrestrict_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str]) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        if session_info.target_from == target_group_prefix:
            for x in user_id:
                try:
                    await aiocqhttp_bot.call_action(
                        "set_group_ban",
                        group_id=session_info.get_common_target_id(),
                        user_id=x.split("|")[-1],
                        duration=0,
                    )
                    Logger.info(f"Unrestricted member {x} in group {session_info.target_id}")
                except Exception:
                    Logger.exception(f"Failed to unrestrict member {x} in group {session_info.target_id}: ")

    @classmethod
    async def kick_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str], reason: str | None = None) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        if session_info.target_from == target_group_prefix:
            for x in user_id:
                try:
                    await aiocqhttp_bot.call_action(
                        "set_group_kick",
                        group_id=session_info.get_common_target_id(),
                        user_id=x.split("|")[-1],
                        reject_add_request=False,
                    )
                    Logger.info(f"Kicked member {x} in group {session_info.target_id}")
                except Exception:
                    Logger.exception(f"Failed to kick member {x} in group {session_info.target_id}: ")

    @classmethod
    async def ban_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str], reason: str | None = None) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        if session_info.target_from == target_group_prefix:
            for x in user_id:
                try:
                    await aiocqhttp_bot.call_action(
                        "set_group_kick",
                        group_id=session_info.get_common_target_id(),
                        user_id=x.split("|")[-1],
                        reject_add_request=True,
                    )
                    Logger.info(f"Banned member {x} in group {session_info.target_id}")
                except Exception:
                    Logger.exception(f"Failed to ban member {x} in group {session_info.target_id}: ")

    @classmethod
    async def add_reaction(Silian_cls, session_info: SessionInfo, message_id: str | list[str], emoji: str) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")

        if session_info.target_from == target_group_prefix:
            try:
                Silian_obi = Temp.data.get("onebot_impl")
                if Silian_obi in ["llonebot", "napcat"]:
                    await aiocqhttp_bot.call_action(
                        "set_msg_emoji_like", message_id=message_id[-1], emoji_id=emoji, set=True
                    )
                elif Silian_obi == "lagrange":
                    await aiocqhttp_bot.call_action(
                        "set_group_reaction",
                        group_id=int(session_info.get_common_target_id()),
                        message_id=message_id[-1],
                        code=emoji,
                        is_add=True,
                    )
                else:
                    return
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

        if session_info.target_from == target_group_prefix:
            try:
                Silian_obi = Temp.data.get("onebot_impl")
                if Silian_obi in ["llonebot", "napcat"]:
                    await aiocqhttp_bot.call_action(
                        "set_msg_emoji_like", message_id=message_id[-1], emoji_id=emoji, set=False
                    )
                elif Silian_obi == "lagrange":
                    await aiocqhttp_bot.call_action(
                        "set_group_reaction",
                        group_id=int(session_info.get_common_target_id()),
                        message_id=message_id[-1],
                        code=emoji,
                        is_add=False,
                    )
                else:
                    return
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
            # 这里可以添加开始输入状态的逻辑
            Logger.debug(f"Start typing in session: {session_info.session_id}")

            if session_info.target_from == target_group_prefix:  # wtf onebot 11
                Silian_obi = Temp.data.get("onebot_impl")
                if Silian_obi in ["llonebot", "napcat"]:
                    await aiocqhttp_bot.call_action(
                        "set_msg_emoji_like", message_id=session_info.message_id, emoji_id=Silian_qq_typing_emoji, set=True
                    )
                elif Silian_obi == "lagrange":
                    await aiocqhttp_bot.call_action(
                        "set_group_reaction",
                        group_id=int(session_info.get_common_target_id()),
                        message_id=session_info.message_id,
                        code=Silian_qq_typing_emoji,
                        is_add=True,
                    )
                else:
                    if session_info.sender_id in Silian_last_send_typing_time:
                        if time.time() - Silian_last_send_typing_time[session_info.sender_id] <= 3600:
                            return
                    Silian_last_send_typing_time[session_info.sender_id] = time.time()
                    if Silian_obi == "shamrock":
                        await aiocqhttp_bot.send_group_msg(
                            group_id=int(session_info.get_common_target_id()),
                            message=f"[CQ:touch,id={session_info.get_common_sender_id()}]",
                        )
                    elif Silian_obi == "go-cqhttp":
                        await aiocqhttp_bot.send_group_msg(
                            group_id=int(session_info.get_common_target_id()),
                            message=f"[CQ:poke,qq={session_info.get_common_sender_id()}]",
                        )
                    else:
                        pass
            Silian_flag = asyncio.Event()
            Silian_cls.typing_flags[session_info.session_id] = Silian_flag
            await Silian_flag.wait()

        asyncio.create_task(_typing())

    @classmethod
    async def end_typing(Silian_cls, session_info: SessionInfo) -> None:
        # if session_info.session_id not in cls.context:
        #     raise ValueError("Session not found in context")
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

        if session_info.target_from == target_group_prefix:
            qq_account = Temp.data.get("qq_account")
            Silian_obi = Temp.data.get("onebot_impl")
            if Silian_obi in ["llonebot", "napcat"]:
                await aiocqhttp_bot.call_action(
                    "set_msg_emoji_like", message_id=session_info.message_id, emoji_id=Silian_qq_limited_emoji, set=True
                )
            elif Silian_obi == "lagrange":
                await aiocqhttp_bot.call_action(
                    "set_group_reaction",
                    group_id=int(session_info.get_common_target_id()),
                    message_id=session_info.message_id,
                    code=Silian_qq_limited_emoji,
                    is_add=True,
                )
            elif Silian_obi == "shamrock":
                await aiocqhttp_bot.call_action(
                    "send_group_msg",
                    group_id=int(session_info.get_common_target_id()),
                    message=f"[CQ:touch,id={qq_account}]",
                )
            elif Silian_obi == "go-cqhttp":
                await aiocqhttp_bot.call_action(
                    "send_group_msg",
                    group_id=int(session_info.get_common_target_id()),
                    message=f"[CQ:poke,qq={qq_account}]",
                )
            else:
                pass

    @classmethod
    async def call_onebot_api(Silian_cls, api_name: str, **kwargs) -> dict | None:
        return await aiocqhttp_bot.call_action(api_name, **kwargs)


Silian__tasks_high_priority = []
Silian__tasks = []


class AIOCQFetchedContextManager(AIOCQContextManager):
    @classmethod
    async def send_message(
        Silian_cls,
        session_info: SessionInfo,
        message: MessageChain | MessageNodes,
        quote: bool = True,
        enable_parse_message=True,
        enable_split_image=True,
    ) -> None:
        Silian_append_tsk = (
            Silian__tasks_high_priority if session_info.target_info.target_data.get("in_post_whitelist", False) else Silian__tasks
        )
        Silian_append_tsk.append(
            super().send_message(
                session_info,
                message,
                quote=quote,
                enable_parse_message=enable_parse_message,
            )
        )

    @staticmethod
    async def process_tasks():
        while True:
            if Silian__tasks_high_priority:
                Silian_task = Silian__tasks_high_priority.pop(0)
                await Silian_task
                cd = random.randint(1, 5)
                Logger.info(
                    f"Processed a high-priority task in AIOCQFetchedContextManager, waiting cooldown for {cd}s..."
                )
                await asyncio.sleep(cd)
            elif Silian__tasks:
                Silian_task = Silian__tasks.pop(0)
                await Silian_task
                cd = random.randint(5, Silian_qq_initiative_msg_cooldown)
                Logger.info(f"Processed a task in AIOCQFetchedContextManager, waiting cooldown for {cd}s...")
                await asyncio.sleep(cd)
            else:
                await asyncio.sleep(1)
