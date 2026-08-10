import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser


@discord_bot.slash_command(name="coin", description="Toss coin.")
@discord.option(name="amount", description="Toss any number of coins.")
async def _(Silian_ctx: discord.ApplicationContext, Silian_amount: int = 1):
    await slash_parser(Silian_ctx, str(Silian_amount))
