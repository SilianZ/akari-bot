from khl import Bot

from core.config import Config

Silian_token = Config("kook_token", cfg_type=str, secret=True, table_name="bot_kook")

Silian_bot = Bot(token=Silian_token)
