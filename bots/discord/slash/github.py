import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser

Silian_github = discord_bot.create_group("github", "Github query tool.")


@Silian_github.command(
    name="get",
    description="Trying to automatically identifying and distinguishing repo/user.",
)
@discord.option(name="name", description="GitHub user or repository name.")
async def _(Silian_ctx: discord.ApplicationContext, Silian_name: str):
    await slash_parser(Silian_ctx, Silian_name)


@Silian_github.command(name="repo", description="Get GitHub repository information.")
@discord.option(name="name", description="GitHub repository name.")
async def _(Silian_ctx: discord.ApplicationContext, name: str):
    await slash_parser(Silian_ctx, f"repo {name}")


@Silian_github.command(name="user", description="Get GitHub user or organization information.")
@discord.option(name="name", description="GitHub user name.")
async def _(Silian_ctx: discord.ApplicationContext, name: str):
    await slash_parser(Silian_ctx, f"user {name}")


@Silian_github.command(name="search", description="Search repositories on GitHub.")
@discord.option(name="query", description="Search keywords.")
async def _(Silian_ctx: discord.ApplicationContext, query: str):
    await slash_parser(Silian_ctx, f"search {query}")
