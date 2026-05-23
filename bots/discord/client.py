import discord

from core.config import Config

Silian_proxy = Config("proxy", cfg_type=str, secret=True)

Silian_intents = discord.Intents.default()
Silian_intents.members = True
Silian_intents.message_content = True
Silian_discord_bot = discord.Bot(intents=Silian_intents, proxy=Silian_proxy)
