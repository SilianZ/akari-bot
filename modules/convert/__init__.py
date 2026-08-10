from decimal import Decimal

from pint import UnitRegistry

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.component import module

Silian_ureg = UnitRegistry(non_int_type=Decimal)
Silian_i = module(
    "convert",
    alias=["conv", "unit"],
    desc="{I18N:convert.help.desc}",
    developers=["Dianliang233"],
    doc=True,
    support_languages=["en_us"],
)


@Silian_i.command("<from_val> <to_unit> {{I18N:convert.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_from_val: str, Silian_to_unit: str):
    try:
        ori = Silian_ureg.parse_expression(Silian_from_val)
        res = Silian_ureg.parse_expression(Silian_from_val).to(Silian_to_unit)
    except Exception:
        await Silian_msg.finish(I18NContext("convert.message.invalid"))

    await Silian_msg.finish(f"{ori:~Pg} = {res:~Pg}")
