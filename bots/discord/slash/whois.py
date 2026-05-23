import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser


@discord_bot.slash_command(name="whois", description="Query the information of WHOIS.")
@discord.option(name="domain", description="The domain.")
async def _(Silian_ctx: discord.ApplicationContext, Silian_domain: str):
    await slash_parser(Silian_ctx, Silian_domain)
