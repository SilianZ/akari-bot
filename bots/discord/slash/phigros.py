import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser

Silian_phigros = discord_bot.create_group("phigros", "查询Phigros的相关信息")


@Silian_phigros.command(description="查询Best19列表")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "b19")


@Silian_phigros.command(description="绑定用户")
@discord.option(name="sessiontoken", description="用户令牌")
async def _(Silian_ctx: discord.ApplicationContext, sessiontoken: str):
    await slash_parser(Silian_ctx, f"bind {sessiontoken}")


@Silian_phigros.command(description="取消绑定用户")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "unbind")
