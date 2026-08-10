import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser


@discord_bot.slash_command(name="bilibili", description="Send video ID for video info.")
@discord.option(name="bid", description="Bilibili video ID.")
async def _(Silian_ctx: discord.ApplicationContext, Silian_bid: str):
    await slash_parser(Silian_ctx, Silian_bid)
