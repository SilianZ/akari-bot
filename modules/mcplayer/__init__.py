from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image, Plain, Url
from core.component import module
from .mojang_api import *

Silian_mcplayer = module(
    "mcplayer",
    desc="{I18N:mcplayer.help.desc}",
    alias="namemc",
    doc=True,
    developers=["Dianliang233"],
)


@Silian_mcplayer.command("<username_or_uuid> {{I18N:mcplayer.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_username_or_uuid: str):
    Silian_arg = Silian_username_or_uuid
    try:
        if len(Silian_arg) == 32:
            name = await uuid_to_name(Silian_arg)
            uuid = Silian_arg
        elif len(Silian_arg) == 36 and Silian_arg.count("-") == 4:
            uuid = Silian_arg.replace("-", "")
            name = await uuid_to_name(Silian_arg)
        else:
            name = Silian_arg
            uuid = await name_to_uuid(Silian_arg)
        Silian_namemc = f"https://namemc.com/profile/{name}"
        Silian_sac = await uuid_to_skin_and_cape(uuid)
        if Silian_sac:
            Silian_render = Silian_sac["render"]
            Silian_skin = Silian_sac["skin"]
            Silian_cape = Silian_sac["cape"]
            Silian_chain = [Plain(f"{name} ({uuid})"), Url(Silian_namemc, use_mm=False), Image(Silian_render), Image(Silian_skin)]
            if Silian_cape:
                Silian_chain.append(Image(Silian_cape))
            await Silian_msg.finish(Silian_chain)
        else:
            await Silian_msg.finish([Plain(f"{name} ({uuid})"), Url(Silian_namemc, use_mm=False)])
    except ValueError:
        await Silian_msg.finish(I18NContext("mcplayer.message.not_found", player=Silian_arg))
