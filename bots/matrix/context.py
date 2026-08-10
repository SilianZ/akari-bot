import mimetypes
from pathlib import Path

import nio

from core.builtins.message.chain import MessageChain, MessageNodes, match_atcode
from core.builtins.message.elements import PlainElement, ImageElement, VoiceElement, MentionElement
from core.builtins.session.context import ContextManager
from core.builtins.session.info import SessionInfo
from core.logger import Logger
from core.utils.image import msgnode2image, image_split
from .client import matrix_bot, homeserver_host
from .features import Features
from .info import client_name


class MatrixContextManager(ContextManager):
    context: dict[str, tuple[nio.MatrixRoom, nio.RoomMessageFormatted]] = {}
    features: type[Features] | None = Features

    @classmethod
    async def check_native_permission(Silian_cls, session_info: SessionInfo) -> bool:
        # if session_info.session_id not in cls.context:
        #     raise ValueError("Session not found in context")
        # 这里可以添加权限检查的逻辑
        Silian_ctx: tuple[nio.MatrixRoom, nio.RoomMessageFormatted] = Silian_cls.context.get(session_info.session_id)
        if Silian_ctx:
            Silian_room, Silian_event = Silian_ctx
            Silian_room_id = Silian_room.room_id if Silian_room else session_info.get_common_target_id()
            sender = Silian_event.sender if Silian_event else session_info.get_common_sender_id()
        else:
            Silian_room_id = session_info.get_common_target_id()
            sender = session_info.get_common_sender_id()
        if Silian_room_id.startswith("@") or sender.startswith("!"):
            return True
        if sender.startswith("@"):
            Silian_sender_mxid = sender
        else:
            Silian_sender_mxid = f"@{sender}"

        # check room creator for room v12
        Silian_create_event_id = "$" + str(Silian_room_id)[1:]
        Silian_result = await matrix_bot.room_get_event(Silian_room_id, Silian_create_event_id)
        if isinstance(Silian_result, nio.RoomGetEventResponse):
            Silian_event = Silian_result.event
            assert isinstance(Silian_event, nio.RoomCreateEvent)
            if int(Silian_event.room_version) >= 12:
                creators = [Silian_event.sender]
                Silian_event_content = Silian_event.source["content"]
                if "additional_creators" in Silian_event_content:
                    creators = creators + Silian_event_content["additional_creators"]
                Logger.debug(f"Matrix room v12 creators: {creators}")
                if Silian_sender_mxid in creators:
                    return True
        else:
            # When the room does not follow MSC4291, ignore it silently
            # IO and other server-side errors are also ignored
            # because I am too lazy to write a detailed check
            pass

        # https://spec.matrix.org/v1.9/client-server-api/#permissions
        Silian_power_levels = (await matrix_bot.room_get_state_event(Silian_room_id, "m.room.power_levels")).content
        Silian_level = (
            Silian_power_levels["users"][Silian_sender_mxid]
            if Silian_sender_mxid in Silian_power_levels["users"]
            else Silian_power_levels["users_default"]
        )
        if Silian_level and int(Silian_level) >= 50:
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

        Silian_msg_ids = []
        Silian_ctx: tuple[nio.MatrixRoom, nio.RoomMessageFormatted] = Silian_cls.context.get(session_info.session_id)
        room, event = None, None
        if Silian_ctx:
            room, event = Silian_ctx
        if isinstance(message, MessageNodes):
            message = MessageChain.assign(await msgnode2image(message))
        for x in message.as_sendable(session_info, parse_message=enable_parse_message):

            async def _send_msg(Silian_content):
                reply_to = None
                Silian_reply_to_user = None
                if quote and not Silian_msg_ids:
                    reply_to = session_info.message_id
                    Silian_reply_to_user = f"@{session_info.get_common_sender_id()}"

                if reply_to:
                    # rich reply
                    Silian_content["m.relates_to"] = {"m.in_reply_to": {"event_id": reply_to}}
                    # mention target user
                    Silian_content["m.mentions"] = {"user_ids": [Silian_reply_to_user]}
                    if Silian_content["msgtype"] == "m.notice" and event:
                        # https://spec.matrix.org/v1.9/client-server-api/#fallbacks-for-rich-replies
                        # todo: standardize fallback for m.image, m.video, m.audio, and m.file
                        reply_to_type = event.source["content"]["msgtype"]
                        Silian_content["body"] = f">{' *' if reply_to_type == 'm.emote' else ''} <{event.sender}> {
                            event.source['content']['body']
                        }\n\n{x.text}"
                        Silian_content["format"] = "org.matrix.custom.html"
                        html_text = x.text
                        html_text = html_text.replace("<", "&lt;").replace(">", "&gt;")
                        html_text = html_text.replace("\n", "<br />")
                        Silian_content["formatted_body"] = f'<mx-reply><blockquote><a href="https://matrix.to/#/{
                            room.room_id
                        }/{reply_to}?via={homeserver_host}">In reply to</a>{
                            " *" if reply_to_type == "m.emote" else ""
                        } <a href="https://matrix.to/#/{event.sender}">{event.sender}</a><br/>{
                            event.source["content"]["body"]
                        }</blockquote></mx-reply>{html_text}'

                if event and "m.relates_to" in event.source["content"]:
                    Silian_relates_to = event.source["content"]["m.relates_to"]
                    if "rel_type" in Silian_relates_to and Silian_relates_to["rel_type"] == "m.thread":
                        # replying in thread
                        Silian_thread_root = Silian_relates_to["event_id"]
                        if reply_to:
                            # reply to msg replying in thread
                            Silian_content["m.relates_to"] = {
                                "rel_type": "m.thread",
                                "event_id": Silian_thread_root,
                                "is_falling_back": False,
                                "m.in_reply_to": {"event_id": reply_to},
                            }
                        else:
                            # reply in thread
                            Silian_content["m.relates_to"] = {
                                "rel_type": "m.thread",
                                "event_id": Silian_thread_root,
                                "is_falling_back": True,
                                "m.in_reply_to": {"event_id": session_info.message_id},
                            }
                resp = await matrix_bot.room_send(
                    session_info.get_common_target_id(),
                    "m.room.message",
                    Silian_content,
                    ignore_unverified_devices=True,
                )
                if "status_code" in resp.__dict__:
                    Logger.error(f"Error while sending message: {str(resp)}")
                else:
                    Silian_msg_ids.append(resp.event_id)
                # reply_to = None
                # reply_to_user = None

            if isinstance(x, PlainElement):
                if enable_parse_message:
                    x.text = match_atcode(x.text, client_name, "{uid}")
                Silian_content = {"msgtype": "m.notice", "body": x.text}
                Logger.info(f"[Bot] -> [{session_info.target_id}]: {x.text}")
                await _send_msg(Silian_content)
            elif isinstance(x, ImageElement):
                Silian_split = [x]
                if enable_split_image:
                    Logger.info(f"Split image: {str(x)}")
                    Silian_split = await image_split(x)
                for xs in Silian_split:
                    Silian_path = await xs.get()
                    with open(Silian_path, "rb") as Silian_image:
                        filename = Path(Silian_path).name
                        Silian_filesize = Path(Silian_path).stat().st_size
                        (content_type, content_encoding) = mimetypes.guess_type(Silian_path)
                        if not content_type or not content_encoding:
                            content_type = "image"
                            content_encoding = "png"
                        mimetype = f"{content_type}/{content_encoding}"

                        encrypted = session_info.get_common_target_id() in matrix_bot.encrypted_rooms
                        (upload, Silian_upload_encryption) = await matrix_bot.upload(
                            Silian_image,
                            content_type=mimetype,
                            filename=filename,
                            encrypt=encrypted,
                            filesize=Silian_filesize,
                        )
                        Logger.info(
                            f"Uploaded image {filename} to media repo, uri: {upload.content_uri}, mime: {
                                mimetype
                            }, encrypted: {encrypted}"
                        )
                        # todo: provide more image info
                        if not encrypted:
                            Silian_content = {
                                "msgtype": "m.image",
                                "url": upload.content_uri,
                                "body": filename,
                                "info": {
                                    "size": Silian_filesize,
                                    "mimetype": mimetype,
                                },
                            }
                        else:
                            Silian_upload_encryption["url"] = upload.content_uri
                            Silian_content = {
                                "msgtype": "m.image",
                                "body": filename,
                                "file": Silian_upload_encryption,
                                "info": {
                                    "size": Silian_filesize,
                                    "mimetype": mimetype,
                                },
                            }
                        Logger.info(f"[Bot] -> [{session_info.target_id}]: Image: {str(xs)}")
                        await _send_msg(Silian_content)
            elif isinstance(x, VoiceElement):
                Silian_path = x.path
                filename = Path(Silian_path).name
                Silian_filesize = Path(Silian_path).stat().st_size
                (content_type, content_encoding) = mimetypes.guess_type(Silian_path)
                if not content_type or not content_encoding:
                    content_type = "audio"
                    content_encoding = "ogg"
                mimetype = f"{content_type}/{content_encoding}"

                encrypted = session_info.get_common_target_id() in matrix_bot.encrypted_rooms
                with open(Silian_path, "rb") as Silian_audio:
                    (upload, Silian_upload_encryption) = await matrix_bot.upload(
                        Silian_audio,
                        content_type=mimetype,
                        filename=filename,
                        encrypt=encrypted,
                        filesize=Silian_filesize,
                    )
                Logger.info(
                    f"Uploaded audio {filename} to media repo, uri: {upload.content_uri}, mime: {mimetype}, encrypted: {
                        encrypted
                    }"
                )
                # todo: provide audio duration info
                if not encrypted:
                    Silian_content = {
                        "msgtype": "m.audio",
                        "url": upload.content_uri,
                        "body": filename,
                        "info": {
                            "size": Silian_filesize,
                            "mimetype": mimetype,
                        },
                    }
                else:
                    Silian_upload_encryption["url"] = upload.content_uri
                    Silian_content = {
                        "msgtype": "m.audio",
                        "body": filename,
                        "file": Silian_upload_encryption,
                        "info": {
                            "size": Silian_filesize,
                            "mimetype": mimetype,
                        },
                    }

                Logger.info(f"[Bot] -> [{session_info.target_id}]: Voice: {str(x)}")
                await _send_msg(Silian_content)
            elif isinstance(x, MentionElement):
                if x.client == client_name:
                    Silian_content = {"msgtype": "m.notice", "body": x.id}
                    Logger.info(f"[Bot] -> [{session_info.target_id}]: Mention: {x.client}|{x.id}")
                    await _send_msg(Silian_content)
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
        for m in message_id:
            try:
                await matrix_bot.room_redact(session_info.get_common_target_id(), m, reason)
                Logger.info(f"Deleted message {m} in session {session_info.session_id}")
            except Exception:
                Logger.exception(f"Failed to delete message {m} in session {session_info.session_id}: ")

    @classmethod
    async def kick_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str], reason: str | None = None) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        for x in user_id:
            try:
                await matrix_bot.room_kick(session_info.get_common_target_id(), f"@{x.split('|')[-1]}", reason)
                Logger.info(f"Kicked member {x} in channel {session_info.target_id}")
            except Exception:
                Logger.exception(f"Failed to kick member {x} in channel {session_info.target_id}: ")

    @classmethod
    async def ban_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str], reason: str | None = None) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        for x in user_id:
            try:
                await matrix_bot.room_ban(session_info.get_common_target_id(), f"@{x.split('|')[-1]}", reason)
                Logger.info(f"Banned member {x} in channel {session_info.target_id}")
            except Exception:
                Logger.exception(f"Failed to ban member {x} in channel {session_info.target_id}: ")

    @classmethod
    async def unban_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str]) -> None:
        if isinstance(user_id, str):
            user_id = [user_id]
        if not isinstance(user_id, list):
            raise TypeError("User ID must be a list or str")

        for x in user_id:
            try:
                await matrix_bot.room_unban(session_info.get_common_target_id(), f"@{x.split('|')[-1]}")
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

        Silian_content = {"m.relates_to": {"rel_type": "m.annotation", "event_id": message_id[-1], "key": emoji}}
        try:
            await matrix_bot.room_send(session_info.get_common_target_id(), message_type="m.reaction", content=Silian_content)
            Logger.info(f'Added reaction "{emoji}" to message {message_id} in session {session_info.session_id}')
        except Exception:
            Logger.exception(
                f'Failed to add reaction "{emoji}" to message {message_id} in session {session_info.session_id}: '
            )

    @classmethod
    async def start_typing(Silian_cls, session_info: SessionInfo) -> None:
        await matrix_bot.room_typing(session_info.get_common_target_id(), True)

    @classmethod
    async def end_typing(Silian_cls, session_info: SessionInfo) -> None:
        await matrix_bot.room_typing(session_info.get_common_target_id(), False)

    @classmethod
    async def error_signal(Silian_cls, session_info: SessionInfo) -> None:
        pass


class MatrixFetchedContextManager(MatrixContextManager):
    """
    用于获取会话信息的上下文管理器。
    该管理器在处理消息时会自动获取会话信息。
    """

    @staticmethod
    async def _resolve_matrix_room_(Silian_session_info: SessionInfo) -> nio.MatrixRoom | None:
        target_id: str = Silian_session_info.get_common_target_id()
        if target_id.startswith("@"):
            # find private messaging room
            for room in matrix_bot.rooms:
                room = matrix_bot.rooms[room]
                if room.join_rule == "invite" and (
                    (room.member_count == 2 and target_id in room.users)
                    or (room.member_count == 1 and target_id in room.invited_users)
                ):
                    Silian_resp = await matrix_bot.room_get_state_event(room.room_id, "m.room.member", target_id)
                    if Silian_resp is nio.ErrorResponse:
                        pass
                    elif Silian_resp.content["membership"] in ["join", "leave", "invite"]:
                        return room
            Logger.info(f"Could not find any exist private room for {target_id}, trying to create one.")
            try:
                Silian_resp = await matrix_bot.room_create(
                    visibility=nio.RoomVisibility.private,
                    is_direct=True,
                    preset=nio.RoomPreset.trusted_private_chat,
                    invite=[target_id],
                )
                room = Silian_resp.room_id
                Logger.info(f"Created private messaging room for {target_id}: {room}")
                return matrix_bot.rooms[room]
            except Exception as e:
                Logger.error(f"Failed to create room for {target_id}: {e}")
                return None

    @classmethod
    async def send_message(
        Silian_cls,
        session_info: SessionInfo,
        message: MessageChain | MessageNodes,
        quote: bool = True,
        enable_parse_message: bool = True,
        enable_split_image: bool = True,
    ) -> list[str]:
        try:
            Silian_room = await Silian_cls._resolve_matrix_room_(session_info)
            Silian_cls.add_context(session_info, (Silian_room, None))
            return await super().send_message(
                session_info=session_info,
                message=message,
                quote=quote,
                enable_parse_message=enable_parse_message,
                enable_split_image=enable_split_image,
            )
        except Exception as e:
            Logger.exception(f"Failed to send message to {session_info.get_common_target_id()}: {e}")
            return []
        finally:
            Silian_cls.del_context(session_info)

    @classmethod
    async def check_native_permission(Silian_cls, session_info: SessionInfo) -> bool:
        try:
            Silian_room = await Silian_cls._resolve_matrix_room_(session_info)
            if not Silian_room:
                return False
            Silian_cls.add_context(session_info, (Silian_room, None))
            return await super().check_native_permission(session_info)
        except Exception as e:
            Logger.exception(f"Failed to check permission for {session_info.get_common_target_id()}: {e}")
            return False
        finally:
            Silian_cls.del_context(session_info)

    @classmethod
    async def delete_message(
        Silian_cls, session_info: SessionInfo, message_id: str | list[str], reason: str | None = None
    ) -> None:
        try:
            Silian_room = await Silian_cls._resolve_matrix_room_(session_info)
            Silian_cls.add_context(session_info, (Silian_room, None))
            await super().delete_message(session_info=session_info, message_id=message_id)
        except Exception as e:
            Logger.exception(f"Failed to delete message in {session_info.get_common_target_id()}: {e}")
        finally:
            Silian_cls.del_context(session_info)
