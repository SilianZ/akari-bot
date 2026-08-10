import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser


@discord_bot.slash_command(name="ip", description="Query the information of IP.")
@discord.option(name="ip_address", description="The IP address.")
async def _(Silian_ctx: discord.ApplicationContext, Silian_ip_address: str):
    await slash_parser(Silian_ctx, Silian_ip_address)
