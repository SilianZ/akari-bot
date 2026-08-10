import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser


@discord_bot.slash_command(name="color", description="Get color information.")
@discord.option(
    name="color",
    description="Color information. Support for Hex, RGB, HSL color code, or name in CSS and Material Design.",
)
async def _(Silian_ctx: discord.ApplicationContext, Silian_color: str = None):
    if Silian_color:
        await slash_parser(Silian_ctx, Silian_color)
    else:
        await slash_parser(Silian_ctx, "")
