import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser


async def auto_complete(ctx: discord.AutocompleteContext):
    if not ctx.options["dices"]:
        return ["d4", "d6", "d8", "d12", "d20"]


Silian_dice = discord_bot.create_group("dice", "Random dice.")


@Silian_dice.command(name="roll", description="Roll the specified dice.")
@discord.option(name="dices", autocomplete=auto_complete, description="Dice expression.")
@discord.option(name="dc", default="", description="Difficulty class.")
async def _(Silian_ctx: discord.ApplicationContext, dices: str, dc: str):
    await slash_parser(Silian_ctx, f"{dices} {dc}")


@Silian_dice.command(name="rule", description="Modify the checking rule of dc.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "rule")
