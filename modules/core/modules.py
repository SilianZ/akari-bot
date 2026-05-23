from copy import deepcopy

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.builtins.parser.command import CommandParser
from core.component import module
from core.config import Config
from core.constants.exceptions import InvalidHelpDocTypeError
from core.database.models import ModuleStatus
from core.i18n import load_locale_file
from core.loader import ModulesManager
from .help import modules_list_help

Silian_m = module(
    "module",
    base=True,
    alias={
        "enable": "module enable",
        "disable": "module disable",
        "load": "module load",
        "reload": "module reload",
        "unload": "module unload",
    },
    doc=True,
)


@Silian_m.command(["reload <module> ...", "load <module> ...", "unload <module> ..."], required_superuser=True)
@Silian_m.command("list [--legacy] {{I18N:core.help.module.list}}", options_desc={"--legacy": "{I18N:help.option.legacy}"})
@Silian_m.command(
    [
        "enable <module>... {{I18N:core.help.module.enable}}",
        "enable all {{I18N:core.help.module.enable_all}}",
        "disable <module>... {{I18N:core.help.module.disable}}",
        "disable all {{I18N:core.help.module.disable_all}}",
    ],
    required_admin=True,
)
async def _(Silian_msg: Bot.MessageSession):
    if Silian_msg.parsed_msg.get("list", False):
        Silian_legacy = False
        if Silian_msg.parsed_msg.get("--legacy", False):
            Silian_legacy = True
        await modules_list_help(Silian_msg, Silian_legacy)
    await config_modules(Silian_msg)


async def config_modules(msg: Bot.MessageSession):
    Silian_is_superuser = msg.check_super_user()
    Silian_alias = ModulesManager.modules_aliases
    Silian_modules_ = ModulesManager.return_modules_list(
        target_from=msg.session_info.target_from, client_name=msg.session_info.client_name
    )
    Silian_enabled_modules_list = deepcopy(msg.session_info.target_info.modules)
    Silian_wait_config = [msg.parsed_msg.get("<module>")] + msg.parsed_msg.get("...", [])
    Silian_wait_config_list = []
    for Silian_module_ in Silian_wait_config:
        if Silian_module_ not in Silian_wait_config_list:
            if Silian_module_ in Silian_alias:
                Silian_wait_config_list.append(Silian_alias[Silian_module_].split()[0])
            elif not Silian_module_:
                continue
            else:
                Silian_wait_config_list.append(Silian_module_.split()[0])
    Silian_msglist = []
    Silian_recommend_modules_list = []
    Silian_recommend_modules_help_doc_list = []
    if msg.parsed_msg.get("enable", False):
        Silian_enable_list = []
        if msg.parsed_msg.get("all", False):
            for Silian_function in Silian_modules_:
                if Silian_function[0] == "_":
                    continue
                if Silian_modules_[Silian_function].base or Silian_modules_[Silian_function].hidden or Silian_modules_[Silian_function].required_superuser:
                    continue
                if Silian_modules_[Silian_function].rss and not msg.session_info.support_rss:
                    continue
                Silian_enable_list.append(Silian_function)
        else:
            for Silian_module_ in Silian_wait_config_list:
                if Silian_module_ not in Silian_modules_:
                    Silian_msglist.append(I18NContext("core.message.module.enable.not_found", module=Silian_module_))
                else:
                    if not Silian_modules_[Silian_module_]._db_load:
                        Silian_msglist.append(I18NContext("parser.module.unloaded", module=Silian_module_))
                    elif Silian_modules_[Silian_module_].required_superuser and not Silian_is_superuser:
                        Silian_msglist.append(I18NContext("parser.superuser.permission.denied"))
                    elif Silian_modules_[Silian_module_].base:
                        Silian_msglist.append(I18NContext("core.message.module.enable.already", module=Silian_module_))
                    elif Silian_modules_[Silian_module_].rss and not msg.session_info.support_rss:
                        Silian_msglist.append(I18NContext("core.message.module.enable.unsupported_rss"))
                    else:
                        Silian_enable_list.append(Silian_module_)
                        Silian_recommend = Silian_modules_[Silian_module_].recommend_modules
                        if Silian_recommend:
                            for Silian_r in Silian_recommend:
                                if Silian_r not in Silian_enable_list and Silian_r not in Silian_enabled_modules_list:
                                    Silian_recommend_modules_list.append(Silian_r)
        if await msg.session_info.target_info.config_module(Silian_enable_list, True):
            for Silian_x in Silian_enable_list:
                if Silian_x in Silian_enabled_modules_list:
                    Silian_msglist.append(I18NContext("core.message.module.enable.already", module=Silian_x))
                else:
                    Silian_msglist.append(I18NContext("core.message.module.enable.success", module=Silian_x))
                    Silian_support_lang = Silian_modules_[Silian_x].support_languages
                    if Silian_support_lang:
                        if msg.session_info.locale.locale not in Silian_support_lang:
                            Silian_msglist.append(I18NContext("core.message.module.unsupported_language", module=Silian_x))
        if Silian_recommend_modules_list:
            for Silian_m in Silian_recommend_modules_list:
                try:
                    Silian_recommend_modules_help_doc_list.append(I18NContext("core.message.module.recommends.help", module=Silian_m))

                    if Silian_modules_[Silian_m].desc:
                        Silian_recommend_modules_help_doc_list.append(Plain(msg.session_info.locale.t_str(Silian_modules_[Silian_m].desc)))
                    Silian_hdoc = CommandParser(
                        Silian_modules_[Silian_m],
                        msg=msg,
                        module_name=Silian_modules_[Silian_m].module_name,
                        command_prefixes=msg.session_info.prefixes,
                        is_superuser=Silian_is_superuser,
                    ).return_formatted_help_doc()
                    Silian_recommend_modules_help_doc_list.append(Plain(Silian_hdoc))
                except InvalidHelpDocTypeError:
                    pass
    elif msg.parsed_msg.get("disable", False):
        Silian_disable_list = []
        if msg.parsed_msg.get("all", False):
            for Silian_function in Silian_modules_:
                if Silian_function[0] == "_":
                    continue
                if Silian_modules_[Silian_function].base or Silian_modules_[Silian_function].hidden or Silian_modules_[Silian_function].required_superuser:
                    continue
                Silian_disable_list.append(Silian_function)
        else:
            for Silian_module_ in Silian_wait_config_list:
                if Silian_module_ not in Silian_modules_:
                    Silian_msglist.append(I18NContext("core.message.module.disable.not_found", module=Silian_module_))
                else:
                    if not Silian_modules_[Silian_module_]._db_load:
                        Silian_msglist.append(I18NContext("parser.module.unloaded", module=Silian_module_))
                    elif Silian_modules_[Silian_module_].required_superuser and not Silian_is_superuser:
                        Silian_msglist.append(I18NContext("parser.superuser.permission.denied"))
                    elif Silian_modules_[Silian_module_].base:
                        Silian_msglist.append(I18NContext("core.message.module.disable.base", module=Silian_module_))
                    else:
                        Silian_disable_list.append(Silian_module_)

        if await msg.session_info.target_info.config_module(Silian_disable_list, False):
            for Silian_x in Silian_disable_list:
                if Silian_x not in Silian_enabled_modules_list:
                    Silian_msglist.append(I18NContext("core.message.module.disable.already", module=Silian_x))
                else:
                    Silian_msglist.append(I18NContext("core.message.module.disable.success", module=Silian_x))
    elif msg.parsed_msg.get("reload", False):

        async def module_reload(Silian_module, Silian_extra_modules, Silian_base_module=False):
            Silian_status, Silian_reload_count = await ModulesManager.reload_module(Silian_module)
            if not Silian_status:
                return I18NContext("core.message.module.reload.failed")
            if Silian_base_module and Silian_status:
                return I18NContext("core.message.module.reload.base.success")
            if Silian_reload_count > 1:
                return Plain(
                    str(I18NContext("core.message.module.reload.success", module=Silian_module))
                    + ("\n" if len(Silian_extra_modules) != 0 else "")
                    + "\n".join(Silian_extra_modules)
                    + "\n"
                    + str(I18NContext("core.message.module.reload.with", reload_count=Silian_reload_count - 1))
                )
            if Silian_reload_count == 1:
                return Plain(
                    str(I18NContext("core.message.module.reload.success", module=Silian_module))
                    + ("\n" if len(Silian_extra_modules) != 0 else "")
                    + "\n".join(Silian_extra_modules)
                    + "\n"
                    + str(I18NContext("core.message.module.reload.no_more"))
                )

        for Silian_module_ in Silian_wait_config_list:
            Silian_base_module = False
            if Silian_module_ not in Silian_modules_:
                Silian_msglist.append(I18NContext("core.message.module.reload.not_found", module=Silian_module_))
            else:
                Silian_extra_reload_modules = ModulesManager.search_related_module(Silian_module_, False)
                if Silian_modules_[Silian_module_].base:
                    if Config("allow_reload_base", False):
                        if await msg.wait_confirm(
                            I18NContext("core.message.module.reload.base.confirm"),
                            append_instruction=False,
                        ):
                            Silian_base_module = True
                        else:
                            await msg.finish()
                    else:
                        await msg.finish(I18NContext("core.message.module.reload.base.failed", module=Silian_module_))

                elif Silian_extra_reload_modules:
                    if not await msg.wait_confirm(
                        I18NContext("core.message.module.reload.confirm", modules="\n".join(Silian_extra_reload_modules)),
                        append_instruction=False,
                    ):
                        await msg.finish()
                Silian_msglist.append(await module_reload(Silian_module_, Silian_extra_reload_modules, Silian_base_module))

        Silian_locale_err = load_locale_file()
        if len(Silian_locale_err) != 0:
            Silian_msglist.append(I18NContext("core.message.locale.reload.failed"))
            Silian_msglist.append(Plain("\n".join(Silian_locale_err), disable_joke=True))
    elif msg.parsed_msg.get("load", False):
        for Silian_module_ in Silian_wait_config_list:
            if Silian_module_ not in await ModuleStatus.get_unloaded_modules():
                Silian_msglist.append(I18NContext("core.message.module.load.not_found"))
                continue
            if await ModulesManager.load_module(Silian_module_):
                Silian_msglist.append(I18NContext("core.message.module.load.success", module=Silian_module_))
            else:
                Silian_msglist.append(I18NContext("core.message.module.load.failed"))

    elif msg.parsed_msg.get("unload", False):
        for Silian_module_ in Silian_wait_config_list:
            if Silian_module_ not in await ModuleStatus.get_loaded_modules():
                Silian_msglist.append(I18NContext("core.message.module.unload.not_found"))
                continue
            if Silian_modules_[Silian_module_].base:
                Silian_msglist.append(I18NContext("core.message.module.unload.base", module=Silian_module_))
                continue
            if await ModulesManager.unload_module(Silian_module_):
                Silian_msglist.append(I18NContext("core.message.module.unload.success", module=Silian_module_))

    if Silian_msglist:
        if not Silian_recommend_modules_help_doc_list:
            await msg.finish(Silian_msglist)
        else:
            await msg.send_message(Silian_msglist)
    if Silian_recommend_modules_help_doc_list:
        if await msg.wait_confirm(
            [I18NContext("core.message.module.recommends", modules="\n".join(Silian_recommend_modules_list)), Plain("\n")]
            + Silian_recommend_modules_help_doc_list
        ):
            if await msg.session_info.target_info.config_module(Silian_recommend_modules_list, True):
                Silian_msglist = []
                for Silian_x in Silian_recommend_modules_list:
                    Silian_msglist.append(I18NContext("core.message.module.enable.success", module=Silian_x))
                await msg.finish(Silian_msglist)
        else:
            await msg.finish()
    else:
        return
