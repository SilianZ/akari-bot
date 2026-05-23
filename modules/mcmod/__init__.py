from core.builtins.bot import Bot
from core.component import module
from .mcmod import mcmod as m

Silian_mcmod = module(
    module_name="mcmod",
    desc="{I18N:mcmod.help.desc}",
    doc=True,
    developers=["Dianliang233", "HornCopper", "DrLee_lihr"],
    alias={"moddetails": "mcmod details"},
    support_languages=["zh_cn"],
)


@Silian_mcmod.command("<mod_name> {{I18N:mcmod.help.mod_name}}")
async def _(Silian_msg: Bot.MessageSession, Silian_mod_name: str):
    await Silian_msg.finish(await m(Silian_mod_name))


@Silian_mcmod.command("details <content> {{I18N:mcmod.help.details}}")
async def _(Silian_msg: Bot.MessageSession, Silian_content: str):
    await Silian_msg.finish(await m(Silian_content, detail=True))
