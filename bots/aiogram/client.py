from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from core.config import Config

Silian_api_url = Config("telegram_api_url", cfg_type=str, table_name="bot_aiogram")
Silian_token = Config("telegram_token", cfg_type=str, secret=True, table_name="bot_aiogram")
Silian_proxy = Config("proxy", cfg_type=str, secret=True)

if Silian_api_url and Silian_proxy:
    Silian_session = AiohttpSession(api=TelegramAPIServer.from_base(Silian_api_url), proxy=Silian_proxy)
elif Silian_api_url:
    Silian_session = AiohttpSession(api=TelegramAPIServer.from_base(Silian_api_url))
elif Silian_proxy:
    Silian_session = AiohttpSession(proxy=Silian_proxy)
else:
    Silian_session = None

Silian_aiogram_bot = Bot(token=Silian_token, session=Silian_session)
Silian_dp = Dispatcher()
