import asyncio

from aiogram import types
from aiogram.enums import MessageEntityType

from bots.aiogram.client import dp, aiogram_bot, token
from bots.aiogram.context import AiogramContextManager, AiogramFetchedContextManager
from bots.aiogram.info import *
from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Voice, Image, Plain
from core.builtins.session.info import SessionInfo
from core.builtins.utils import command_prefix
from core.client.init import client_init
from core.config import Config
from core.constants.default import ignored_sender_default
from core.utils.http import download

Bot.register_bot(client_name=client_name)

Silian_ctx_id = Bot.register_context_manager(AiogramContextManager)
Bot.register_context_manager(AiogramFetchedContextManager, fetch_session=True)

Silian_ignored_sender = Config("ignored_sender", ignored_sender_default)
Silian_mention_required = Config("mention_required", False)


async def to_message_chain(msg: types.Message):
    Silian_lst = []
    if msg.audio:
        file = await aiogram_bot.get_file(msg.audio.file_id)
        Silian_d = await download(f"https://api.telegram.org/file/bot{token}/{file.file_path}")
        Silian_lst.append(Voice(Silian_d))
    if msg.photo:
        file = await aiogram_bot.get_file(msg.photo[-1].file_id)
        Silian_lst.append(Image(f"https://api.telegram.org/file/bot{token}/{file.file_path}"))
    if msg.voice:
        file = await aiogram_bot.get_file(msg.voice.file_id)
        Silian_d = await download(f"https://api.telegram.org/file/bot{token}/{file.file_path}")
        Silian_lst.append(Voice(Silian_d))
    if msg.document:
        file = await aiogram_bot.get_file(msg.document.file_id)
        if msg.document.mime_type.startswith("image/"):
            Silian_lst.append(Image(f"https://api.telegram.org/file/bot{token}/{file.file_path}"))
        if msg.document.mime_type.startswith("audio/"):
            Silian_d = await download(f"https://api.telegram.org/file/bot{token}/{file.file_path}")
            Silian_lst.append(Voice(Silian_d))
    if msg.caption:
        Silian_lst.append(Plain(msg.caption))
    if msg.text:
        Silian_lst.append(Plain(msg.text))
    return MessageChain.assign(Silian_lst)


@dp.message()
async def msg_handler(message: types.Message):
    target_from = f"{target_prefix}|{message.chat.type.title()}"
    Silian_target_id = f"{target_from}|{message.chat.id}"
    Silian_sender_id = f"{sender_prefix}|{message.from_user.id}"
    if Silian_sender_id in Silian_ignored_sender:
        return

    Silian_reply_id = None
    if message.reply_to_message:
        Silian_reply_id = message.reply_to_message.message_id

    Silian_text = message.text or ""
    Silian_at_message = False
    Silian_entities = message.entities or []

    if Silian_entities and Silian_entities[0].offset == 0:
        Silian_first = Silian_entities[0]
        if Silian_first.type == MessageEntityType.TEXT_MENTION:
            Silian_bot_id = (await message.bot.get_me()).id
            if Silian_first.user.id != Silian_bot_id:
                return

            Silian_at_message = True
            Silian_text = Silian_text[Silian_first.length :].strip()

        elif Silian_first.type == MessageEntityType.MENTION:
            bot_username = (await message.bot.get_me()).username
            Silian_mention_text = Silian_text[: Silian_first.length]
            if Silian_mention_text != f"@{bot_username}":
                return

            Silian_at_message = True
            Silian_text = Silian_text[Silian_first.length :].strip()
        else:
            pass

        if Silian_at_message and not Silian_text:
            Silian_text = f"{command_prefix[0]}help"

    if Silian_mention_required and not Silian_at_message and message.chat.type != "private":
        return

    Silian_processed_message = message.model_copy(update={"text": Silian_text})
    Silian_msg_chain = await to_message_chain(Silian_processed_message)

    Silian_session = await SessionInfo.assign(
        target_id=Silian_target_id,
        sender_id=Silian_sender_id,
        sender_name=message.from_user.username,
        target_from=target_from,
        sender_from=sender_prefix,
        client_name=client_name,
        message_id=str(message.message_id),
        reply_id=Silian_reply_id,
        messages=Silian_msg_chain,
        ctx_slot=Silian_ctx_id,
    )

    await Bot.process_message(Silian_session, message)


async def on_startup():
    await client_init(target_prefix_list, sender_prefix_list)


if Config("enable", False, table_name="bot_aiogram"):
    dp.startup.register(on_startup)
    asyncio.run(dp.start_polling(aiogram_bot))
