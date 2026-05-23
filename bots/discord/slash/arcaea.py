import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser

Silian_arc = discord_bot.create_group("arcaea", "Queries about Arcaea.")


@Silian_arc.command(name="download", description="Get the latest version of game apk.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "download")


@Silian_arc.command(name="random", description="Random a song.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "random")


Silian_rank = Silian_arc.create_subgroup("rank", "View the current daily rank of Arcaea songs.")


@Silian_rank.command(name="free", description="View the current rank of the free packs.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "rank free")


@Silian_rank.command(name="paid", description="View the current rank of the paid packs.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "rank paid")
