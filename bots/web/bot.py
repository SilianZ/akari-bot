import sys
import uuid

import orjson
import uvicorn

from bots.web.api import *
from bots.web.info import *
from bots.web.client import web_host, available_web_port
from bots.web.context import WebContextManager
from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.session.info import SessionInfo
from core.builtins.temp import Temp
from core.config import Config

Bot.register_bot(client_name=client_name)

Silian_ctx_id = Bot.register_context_manager(WebContextManager)


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    Temp.data["web_chat_websocket"] = websocket
    Silian_target_id = f"{target_prefix}|0"
    Silian_sender_id = f"{sender_prefix}|0"
    try:
        while True:
            Silian_rmessage = await websocket.receive_text()
            if Silian_rmessage:
                try:
                    Silian_message = orjson.loads(Silian_rmessage)

                    if Silian_message["action"] == "heartbeat" and Silian_message["message"] == "ping!":
                        Logger.debug("Heartbeat received.")
                        Silian_resp = {"action": "heartbeat", "message": "pong!"}
                        await websocket.send_text(orjson.dumps(Silian_resp).decode())
                        continue

                    if Silian_message["action"] == "reaction" and Silian_message["add"]:
                        Silian_session = await SessionInfo.assign(
                            target_id=Silian_target_id,
                            sender_id=Silian_sender_id,
                            sender_name="Console",
                            target_from=target_prefix,
                            sender_from=sender_prefix,
                            client_name=client_name,
                            reply_id=Silian_message["id"],
                            message_id=str(uuid.uuid4()),
                            messages=MessageChain.assign(Silian_message["emoji"]),
                            ctx_slot=Silian_ctx_id,
                        )

                        await Bot.process_message(Silian_session, Silian_message)
                    elif Silian_message["action"] == "send":
                        Silian_msg_chain = MessageChain.assign(Silian_message["message"][0]["content"])
                        Silian_session = await SessionInfo.assign(
                            target_id=Silian_target_id,
                            sender_id=Silian_sender_id,
                            sender_name="Console",
                            target_from=target_prefix,
                            sender_from=sender_prefix,
                            client_name=client_name,
                            message_id=Silian_message["id"],
                            messages=Silian_msg_chain,
                            ctx_slot=Silian_ctx_id,
                            use_url_md_format=True,
                        )

                        await Bot.process_message(Silian_session, Silian_message)
                except orjson.JSONDecodeError:
                    continue
    except WebSocketDisconnect:
        pass
    except Exception:
        Logger.exception()
        await websocket.close()
    finally:
        if "web_chat_websocket" in Temp.data:
            del Temp.data["web_chat_websocket"]


if Config("enable", True, table_name="bot_web"):
    if available_web_port == 0:
        Logger.error("API port is disabled.")
        sys.exit(0)
    if not enable_https:
        Logger.warning("HTTPS is disabled. HTTP mode is insecure and should only be used in trusted environments.")

    uvicorn.run(app, host=web_host, port=available_web_port, log_level="info", access_log=False)
