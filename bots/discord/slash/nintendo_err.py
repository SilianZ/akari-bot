import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser


@discord_bot.slash_command(description="有关任天堂主机报错的详细信息查询")
@discord.option(name="errcode", description="报错码")
async def _(Silian_ctx: discord.ApplicationContext, Silian_errcode: str):
    await slash_parser(Silian_ctx, Silian_errcode)
