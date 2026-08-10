from core.builtins.bot import Bot
from core.component import module
from .mcv import mcjv, mcbv

Silian_m = module(
    "mcv",
    developers=["OasisAkari", "Dianliang233"],
    alias={
        "mcbv": "mcv mcbv",
        "mcev": "mcv mcev",
    },
    doc=True,
)


@Silian_m.command("{{I18N:mcv.help.mcv}}")
async def _(Silian_msg: Bot.MessageSession):
    await Silian_msg.finish(await mcjv(Silian_msg))


@Silian_m.command("mcbv {{I18N:mcv.help.mcbv}}")
async def _(Silian_msg: Bot.MessageSession):
    await Silian_msg.finish(await mcbv(Silian_msg))


# @m.command("mcev {{I18N:mcv.help.mcev}}")
# async def mcev_loader(msg: Bot.MessageSession):
#     await msg.finish(await mcev(msg))
