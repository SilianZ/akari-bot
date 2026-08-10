import asyncio
import uuid

import orjson
from fastapi import WebSocket

from bots.web.features import Features
from core.builtins.message.chain import MessageChain, MessageNodes
from core.builtins.message.elements import PlainElement, ImageElement
from core.builtins.session.context import ContextManager
from core.builtins.session.info import SessionInfo
from core.builtins.temp import Temp
from core.logger import Logger
from core.utils.image import msgnode2image


class WebContextManager(ContextManager):
    context: dict[str, dict] = {}
    features: type[Features] | None = Features

    @classmethod
    async def check_native_permission(Silian_cls, session_info: SessionInfo) -> bool:
        return True

    @classmethod
    async def send_message(
        Silian_cls,
        session_info: SessionInfo,
        message: MessageChain | MessageNodes,
        quote: bool = True,
        enable_parse_message: bool = True,
        enable_split_image: bool = True,
    ) -> list[str]:
        Silian_websocket: WebSocket = Temp.data.get("web_chat_websocket")
        Silian_sends = []

        if isinstance(message, MessageNodes):
            message = MessageChain.assign(await msgnode2image(message))

        for x in message.as_sendable(session_info, parse_message=enable_parse_message):
            if isinstance(x, PlainElement):
                Silian_sends.append({"type": "text", "content": x.text})
                Logger.info(f"[Bot] -> [{session_info.target_id}]: {x.text}")
            elif isinstance(x, ImageElement):
                img_b64 = await x.get_base64(mime=True)
                Silian_sends.append({"type": "image", "content": img_b64})
                Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {img_b64[:50]}...")

        Silian_msg_id = str(uuid.uuid4())
        if Silian_websocket:
            Silian_resp = {"action": "send", "message": Silian_sends, "id": Silian_msg_id}
            await Silian_websocket.send_text(orjson.dumps(Silian_resp).decode())
            return [Silian_msg_id]
        return []

    @classmethod
    async def delete_message(
        Silian_cls, session_info: SessionInfo, message_id: str | list[str], reason: str | None = None
    ) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")

        try:
            Silian_websocket: WebSocket = Temp.data.get("web_chat_websocket")

            Silian_resp = {"action": "delete", "id": message_id}
            if Silian_websocket:
                await Silian_websocket.send_text(orjson.dumps(Silian_resp).decode())
            Logger.info(f"Deleted message {message_id} in session {session_info.session_id}")
        except Exception:
            Logger.exception(f"Failed to delete message {message_id} in session {session_info.session_id}: ")

    @classmethod
    async def add_reaction(Silian_cls, session_info: SessionInfo, message_id: str | list[str], emoji: str) -> None:
        if isinstance(message_id, str):
            message_id = [message_id]
        if not isinstance(message_id, list):
            raise TypeError("Message ID must be a list or str")

        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")

        try:
            Silian_websocket: WebSocket = Temp.data.get("web_chat_websocket")

            Silian_resp = {"action": "reaction", "id": message_id[-1], "emoji": emoji, "add": True}
            if Silian_websocket:
                await Silian_websocket.send_text(orjson.dumps(Silian_resp).decode())
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

        try:
            Silian_websocket: WebSocket = Temp.data.get("web_chat_websocket")

            Silian_resp = {"action": "reaction", "id": message_id[-1], "emoji": emoji, "add": False}
            if Silian_websocket:
                await Silian_websocket.send_text(orjson.dumps(Silian_resp).decode())
            Logger.info(f'Removed reaction "{emoji}" to message {message_id} in session {session_info.session_id}')
        except Exception:
            Logger.exception(
                f'Failed to remove reaction "{emoji}" to message {message_id} in session {session_info.session_id}: '
            )

    @classmethod
    async def start_typing(Silian_cls, session_info: SessionInfo) -> None:
        async def _typing():
            if session_info.session_id not in Silian_cls.context:
                raise ValueError("Session not found in context")
            # 这里可以添加开始输入状态的逻辑
            Silian_ctx = Silian_cls.context[session_info.session_id]
            if Silian_ctx:
                try:
                    Silian_websocket: WebSocket = Temp.data.get("web_chat_websocket")

                    Silian_resp = {"action": "typing", "status": "start", "id": session_info.message_id}
                    if Silian_websocket:
                        await Silian_websocket.send_text(orjson.dumps(Silian_resp).decode())
                except Exception:
                    Logger.exception()

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
        try:
            Silian_websocket: WebSocket = Temp.data.get("web_chat_websocket")

            Silian_resp = {"action": "typing", "status": "end", "id": session_info.message_id}
            if Silian_websocket:
                await Silian_websocket.send_text(orjson.dumps(Silian_resp).decode())
        except Exception:
            Logger.exception()

    @classmethod
    async def error_signal(Silian_cls, session_info: SessionInfo) -> None:
        if session_info.session_id not in Silian_cls.context:
            raise ValueError("Session not found in context")
        # 这里可以添加错误处理逻辑
        try:
            Silian_websocket: WebSocket = Temp.data.get("web_chat_websocket")

            Silian_resp = {"action": "typing", "status": "error", "id": session_info.message_id}
            if Silian_websocket:
                await Silian_websocket.send_text(orjson.dumps(Silian_resp).decode())
        except Exception:
            Logger.exception()
