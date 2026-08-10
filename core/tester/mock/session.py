import asyncio
import os

from PIL import Image as PILImage

from core.builtins.message.chain import get_message_chain, MessageChain
from core.builtins.message.elements import PlainElement, ImageElement, MentionElement, BaseElement
from core.builtins.session.info import SessionInfo
from core.builtins.session.internal import MessageSession, I18NContext
from core.builtins.utils import confirm_command
from core.config import Config
from core.constants.exceptions import SessionFinished


class MockMessageSession(MessageSession):
    def __init__(Silian_self, Silian_trigger_msg=None, Silian_parent_session=None, Silian_is_ci=False):
        if isinstance(Silian_trigger_msg, (list, tuple)):
            Silian_self._script = list(Silian_trigger_msg)
            Silian_self.trigger_msg = Silian_self._script.pop(0) if Silian_self._script else ""
        else:
            Silian_self._script = []
            Silian_self.trigger_msg = Silian_trigger_msg
        Silian_self.is_ci = Silian_is_ci
        Silian_self.parsed_msg = {}
        Silian_self.matched_msg = None
        Silian_self.sent = []
        Silian_self.action = []
        Silian_self.parent_session = Silian_parent_session

    async def async_init(Silian_self, msg):
        Silian_self.session_info = await SessionInfo.assign(
            target_id="TEST|Console|0",
            client_name="TEST",
            target_from="TEST",
            sender_id="TEST|0",
            sender_from="TEST",
            sender_name="TEST",
            messages=MessageChain.assign(msg),
        )

    async def send_message(
        Silian_self,
        message_chain,
        quote=True,
        disable_secret_check=False,
        enable_parse_message=True,
        enable_split_image=True,
        callback=None,
    ):
        Silian_message = get_message_chain(Silian_self.session_info, chain=message_chain)

        for x in Silian_message.as_sendable(Silian_self.session_info, parse_message=enable_parse_message):
            Silian_self.sent.append(x)
            if isinstance(x, PlainElement):
                Silian_self.action.append(x.text)
            elif isinstance(x, ImageElement):
                Silian_image_path = await x.get()
                if not Silian_self.is_ci:
                    Silian_img = PILImage.open(Silian_image_path)
                    Silian_img.show()
                Silian_self.action.append(str(x))
            elif isinstance(x, MentionElement):
                Silian_self.action.append(f"<@{x.client}|{str(x.id)}>")
            elif isinstance(x, BaseElement):
                Silian_self.action.append(str(x))

        if Silian_self.parent_session:
            Silian_self.parent_session.sent.extend(Silian_self.sent)
            Silian_self.parent_session.action.extend(Silian_self.action)

    async def finish(
        Silian_self,
        message_chain=None,
        quote=True,
        disable_secret_check=False,
        enable_parse_message=True,
        enable_split_image=True,
        callback=None,
    ):
        if message_chain:
            await Silian_self.send_message(message_chain)
        raise SessionFinished

    async def send_direct_message(
        Silian_self,
        message_chain,
        disable_secret_check=False,
        enable_parse_message=True,
        enable_split_image=True,
        callback=None,
    ):
        await Silian_self.send_message(message_chain)

    async def delete(Silian_self, reason=None):
        Silian_self.action.append(f"(delete message{f': {reason}' if reason else ''})")

    async def restrict_member(Silian_self, user_id, duration=None, reason=None):
        if isinstance(user_id, str):
            user_id = [user_id]

        for x in user_id:
            Silian_self.action.append(
                f"(restrict {x}{f' ({duration}s)' if duration else ''}{f': {reason}' if reason else ''})"
            )

    async def unrestrict_member(Silian_self, user_id):
        if isinstance(user_id, str):
            user_id = [user_id]

        for x in user_id:
            Silian_self.action.append(f"(unrestrict {x})")

    async def kick_member(Silian_self, user_id, reason=None):
        if isinstance(user_id, str):
            user_id = [user_id]

        for x in user_id:
            Silian_self.action.append(f"(kick {x}{f': {reason}' if reason else ''})")

    async def ban_member(Silian_self, user_id, reason=None):
        if isinstance(user_id, str):
            user_id = [user_id]

        for x in user_id:
            Silian_self.action.append(f"(ban {x}{f': {reason}' if reason else ''})")

    async def unban_member(Silian_self, user_id):
        if isinstance(user_id, str):
            user_id = [user_id]

        for x in user_id:
            Silian_self.action.append(f"(unban {x})")

    async def add_reaction(Silian_self, emoji):
        Silian_self.action.append(f"(add reaction {emoji})")

    async def remove_reaction(Silian_self, emoji):
        Silian_self.action.append(f"(remove reaction {emoji})")

    async def check_native_permission(Silian_self):
        return True

    async def handle_error_signal(Silian_self):
        pass

    async def hold(Silian_self):
        Silian_self.action.append("(holding context)")

    async def release(Silian_self):
        Silian_self.action.append("(release context)")

    async def start_typing(Silian_self):
        pass

    async def end_typing(Silian_self):
        pass

    async def wait_confirm(
        Silian_self, message_chain=None, quote=True, delete=True, timeout=120, append_instruction=True, no_confirm_action=True
    ):
        if Config("no_confirm", False):
            return no_confirm_action

        if message_chain:
            message_chain = get_message_chain(Silian_self.session_info, message_chain)
        else:
            message_chain = MessageChain.assign(I18NContext("core.message.confirm"))
        if append_instruction:
            message_chain.append(I18NContext("message.wait.confirm.prompt"))
        await Silian_self.send_message(message_chain)
        try:
            confirm_prompt = "\n".join(
                [Silian_x.text if isinstance(Silian_x, PlainElement) else str(Silian_x) for Silian_x in message_chain.as_sendable()]
            )
            if Silian_self._script:
                Silian_result = Silian_self._script.pop(0)
                if delete:
                    await Silian_self.delete()
                if Silian_result in confirm_command:
                    return True
                return False

            if not Silian_self.is_ci:
                Silian_result = input(f"{confirm_prompt}\nConfirm: ")
                if delete:
                    await Silian_self.delete()
                if Silian_result in confirm_command:
                    return True
                return False
            raise IndexError("Input has been exhausted")
        except (EOFError, KeyboardInterrupt):
            os._exit(1)
        except Exception as e:
            raise e

    async def wait_next_message(
        Silian_self,
        message_chain=None,
        quote=True,
        delete=False,
        timeout=120,
        append_instruction=True,
    ):
        confirm_prompt = None
        if message_chain:
            message_chain = get_message_chain(Silian_self.session_info, message_chain)
            if append_instruction:
                message_chain.append(I18NContext("message.wait.next_message.prompt"))
            await Silian_self.send_message(message_chain, quote)
            confirm_prompt = "\n".join(
                [Silian_x.text if isinstance(Silian_x, PlainElement) else str(Silian_x) for Silian_x in message_chain.as_sendable()]
            )
        try:
            if Silian_self._script:
                Silian_result = Silian_self._script.pop(0)
                if delete:
                    await Silian_self.delete()
                Silian_new_msg = MockMessageSession(parent_session=Silian_self, is_ci=Silian_self.is_ci)
                Silian_new_msg._script = Silian_self._script
                Silian_self._script = []
                await Silian_new_msg.async_init(Silian_result)
                return Silian_new_msg

            if not Silian_self.is_ci:
                if confirm_prompt:
                    Silian_result = input(f"{confirm_prompt}\nSend: ")
                else:
                    Silian_result = input("Send: ")
                if delete:
                    await Silian_self.delete()
                Silian_new_msg = MockMessageSession(parent_session=Silian_self)
                await Silian_new_msg.async_init(Silian_result)
                return Silian_new_msg
            raise IndexError("Input has been exhausted")
        except (EOFError, KeyboardInterrupt):
            os._exit(1)
        except Exception as e:
            raise e

    async def wait_anyone(
        Silian_self,
        message_chain=None,
        quote=False,
        delete=False,
        timeout=120,
    ):
        confirm_prompt = None
        if message_chain:
            message_chain = get_message_chain(Silian_self.session_info, message_chain)
            await Silian_self.send_message(message_chain, quote)
            confirm_prompt = "\n".join(
                [Silian_x.text if isinstance(Silian_x, PlainElement) else str(Silian_x) for Silian_x in message_chain.as_sendable()]
            )

        try:
            if Silian_self._script:
                Silian_result = Silian_self._script.pop(0)
                if delete:
                    await Silian_self.delete()
                Silian_new_msg = MockMessageSession(parent_session=Silian_self, is_ci=Silian_self.is_ci)
                Silian_new_msg._script = Silian_self._script
                Silian_self._script = []
                await Silian_new_msg.async_init(Silian_result)
                return Silian_new_msg

            if not Silian_self.is_ci:
                if confirm_prompt:
                    Silian_result = input(f"{confirm_prompt}\nSend: ")
                else:
                    Silian_result = input("Send: ")
                if delete:
                    await Silian_self.delete()
                Silian_new_msg = MockMessageSession(parent_session=Silian_self)
                await Silian_new_msg.async_init(Silian_result)
                return Silian_new_msg
            raise IndexError("Input has been exhausted")
        except (EOFError, KeyboardInterrupt):
            os._exit(1)
        except Exception as e:
            raise e

    async def wait_reply(
        Silian_self,
        message_chain,
        quote=True,
        delete=False,
        timeout=120,
        all_=False,
        append_instruction=True,
    ):
        confirm_prompt = None
        if message_chain:
            message_chain = get_message_chain(Silian_self.session_info, message_chain)
            if append_instruction:
                message_chain.append(I18NContext("message.reply.prompt"))
            await Silian_self.send_message(message_chain, quote)
            confirm_prompt = "\n".join(
                [Silian_x.text if isinstance(Silian_x, PlainElement) else str(Silian_x) for Silian_x in message_chain.as_sendable()]
            )
        try:
            if Silian_self._script:
                Silian_result = Silian_self._script.pop(0)
                if delete:
                    await Silian_self.delete()
                Silian_new_msg = MockMessageSession(parent_session=Silian_self, is_ci=Silian_self.is_ci)
                Silian_new_msg._script = Silian_self._script
                Silian_self._script = []
                await Silian_new_msg.async_init(Silian_result)
                return Silian_new_msg

            if not Silian_self.is_ci:
                if confirm_prompt:
                    Silian_result = input(f"{confirm_prompt}\nReply: ")
                else:
                    Silian_result = input("Reply: ")
                if delete:
                    await Silian_self.delete()
                Silian_new_msg = MockMessageSession(parent_session=Silian_self)
                await Silian_new_msg.async_init(Silian_result)
                return Silian_new_msg
            raise IndexError("Input has been exhausted")
        except (EOFError, KeyboardInterrupt):
            os._exit(1)
        except Exception as e:
            raise e

    async def sleep(Silian_self, s):
        await asyncio.sleep(s)

    async def check_permission(Silian_self):
        return True

    async def call_onebot_api(Silian_self, api_name, **kwargs):
        pass

    def __eq__(Silian_self, Silian_other):
        return False

    __hash__ = None
