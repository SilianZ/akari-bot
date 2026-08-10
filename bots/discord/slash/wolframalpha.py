import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser

Silian_wolframalpha = discord_bot.create_group("wolframalpha", "Use WolframAlpha.")


@Silian_wolframalpha.command(name="query", description="Input a question or formula to search for WolframAlpha.")
@discord.option(name="query", description="Enter what you want to calculate.")
async def _(Silian_ctx: discord.ApplicationContext, Silian_query: str):
    await slash_parser(Silian_ctx, Silian_query)


@Silian_wolframalpha.command(name="ask", description="Answer the question via WolframAlpha.")
@discord.option(name="question", description="Ask WolframAlpha.")
async def _(Silian_ctx: discord.ApplicationContext, question: str):
    await slash_parser(Silian_ctx, f"ask {question}")
