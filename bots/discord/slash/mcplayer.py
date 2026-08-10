import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser


@discord_bot.slash_command(name="mcplayer", description="Get Minecraft player information.")
@discord.option(name="username_or_uuid", description="The name or UUID of Minecraft player.")
async def _(Silian_ctx: discord.ApplicationContext, Silian_username_or_uuid: str):
    await slash_parser(Silian_ctx, Silian_username_or_uuid)
