import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser


@discord_bot.slash_command(name="ai", description="Answer your question via LLMs.")
@discord.option(name="question", description="Ask Akaribot.")
async def _(Silian_ctx: discord.ApplicationContext, Silian_question: str):
    await slash_parser(Silian_ctx, Silian_question)
