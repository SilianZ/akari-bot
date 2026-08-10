from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.component import module
from .process import process_expression

Silian_dice = module(
    "dice",
    alias=["rd", "roll"],
    developers=["Light-Beacon", "DoroWolf"],
    desc="{I18N:dice.help.desc}",
    doc=True,
)


@Silian_dice.command()
async def _(Silian_msg: Bot.MessageSession):
    await Silian_msg.finish(await process_expression(Silian_msg, "D", None))


@Silian_dice.command("<dices> [<dc>] {{I18N:dice.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_dices: str, Silian_dc: int = None):
    await Silian_msg.finish(await process_expression(Silian_msg, Silian_dices, Silian_dc))


@Silian_dice.command("set <sides> {{I18N:dice.help.set}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_sides: int):
    if Silian_sides > 1:
        await Silian_msg.session_info.target_info.edit_target_data("dice_default_sides", Silian_sides)
        await Silian_msg.finish(I18NContext("dice.message.set.success", sides=Silian_sides))
    elif Silian_sides == 0:
        await Silian_msg.session_info.target_info.edit_target_data("dice_default_sides", None)
        await Silian_msg.finish(I18NContext("dice.message.set.clear"))
    else:
        await Silian_msg.finish(I18NContext("dice.message.error.value.sides.invalid"))


@Silian_dice.command("rule {{I18N:dice.help.rule}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession):
    Silian_dc_rule = Silian_msg.session_info.target_info.target_data.get("dice_dc_reversed")

    if Silian_dc_rule:
        await Silian_msg.session_info.target_info.edit_target_data("dice_dc_reversed", False)
        await Silian_msg.finish(I18NContext("dice.message.rule.disable"))
    else:
        await Silian_msg.session_info.target_info.edit_target_data("dice_dc_reversed", True)
        await Silian_msg.finish(I18NContext("dice.message.rule.enable"))
