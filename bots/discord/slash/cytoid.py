import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser

Silian_ctd = discord_bot.create_group("cytoid", "Query about Cytoid.")


@Silian_ctd.command(name="b30", description="Query the Best30 list.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "b30")


@Silian_ctd.command(name="r30", description="Query the Recent30 list.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "r30")


@Silian_ctd.command(name="profile", description="Query user profile.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "profile")


@Silian_ctd.command(name="bind", description="Bind user.")
@discord.option(name="username", description="Your Cytoid username.")
async def _(Silian_ctx: discord.ApplicationContext, username: str):
    await slash_parser(Silian_ctx, f"bind {username}")


@Silian_ctd.command(name="unbind", description="Unbind user.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "unbind")
