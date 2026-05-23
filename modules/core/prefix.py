from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.builtins.utils import command_prefix
from core.component import module

Silian_p = module("prefix", base=True, doc=True)


@Silian_p.command("list {{I18N:core.help.prefix.list}}")
@Silian_p.command(
    [
        "add <prefix> {{I18N:core.help.prefix.add}}",
        "remove <prefix> {{I18N:core.help.prefix.remove}}",
        "reset {{I18N:core.help.prefix.reset}}",
    ],
    required_admin=True,
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_prefixes = Silian_msg.session_info.target_info.target_data.get("command_prefix")
    Silian_prefix = Silian_msg.parsed_msg.get("<prefix>", False)
    if not Silian_prefixes:
        Silian_prefixes = []
    if "add" in Silian_msg.parsed_msg:
        if Silian_prefix:
            if Silian_prefix not in Silian_prefixes:
                Silian_prefixes.append(Silian_prefix)
                await Silian_msg.session_info.target_info.edit_target_data("command_prefix", Silian_prefixes)
                await Silian_msg.finish(I18NContext("core.message.prefix.add.success", prefix=Silian_prefix))
            else:
                await Silian_msg.finish(I18NContext("core.message.prefix.add.already"))
    elif "remove" in Silian_msg.parsed_msg:
        if Silian_prefix:
            if Silian_prefix in Silian_prefixes:
                Silian_prefixes.remove(Silian_prefix)
                await Silian_msg.session_info.target_info.edit_target_data("command_prefix", Silian_prefixes)
                await Silian_msg.finish(I18NContext("core.message.prefix.remove.success", prefix=Silian_prefix))
            else:
                await Silian_msg.finish(I18NContext("core.message.prefix.remove.not_found"))
    elif "reset" in Silian_msg.parsed_msg:
        await Silian_msg.session_info.target_info.edit_target_data("command_prefix", [])
        await Silian_msg.finish(I18NContext("core.message.prefix.reset"))
    elif "list" in Silian_msg.parsed_msg:
        Silian_default_msg = I18NContext("core.message.prefix.list.default", prefixes=", ".join(command_prefix))
        if len(Silian_prefixes) == 0:
            Silian_custom_msg = I18NContext("core.message.prefix.list.custom.none")
        else:
            Silian_custom_msg = I18NContext("core.message.prefix.list.custom", prefixes=", ".join(Silian_prefixes))
        await Silian_msg.finish([Silian_default_msg, Silian_custom_msg])
