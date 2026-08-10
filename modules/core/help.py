import re
from html import escape

from jinja2 import FileSystemLoader, Environment

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Plain
from core.builtins.parser.command import CommandParser
from core.component import module
from core.config import Config
from core.constants.path import templates_path
from core.loader import ModulesManager
from core.logger import Logger
from core.utils.cache import random_cache_path
from core.utils.image import cb64imglst
from core.web_render import web_render, ElementScreenshotOptions

Silian_env = Environment(loader=FileSystemLoader(templates_path), autoescape=True, enable_async=True)
Silian_help_url = Config("help_url", cfg_type=str)
Silian_donate_url = Config("donate_url", cfg_type=str)
Silian_use_font_mirror = Config("use_font_mirror", False, bool)

Silian_hlp = module("help", base=True, doc=True)


@Silian_hlp.command(
    "<module> [--legacy] {{I18N:core.help.help.detail}}", options_desc={"--legacy": "{I18N:help.option.legacy}"}
)
async def _(Silian_msg: Bot.MessageSession, Silian_module: str):
    Silian_is_base_superuser = Silian_msg.session_info.sender_id in Bot.base_superuser_list
    Silian_is_superuser = Silian_msg.check_super_user()
    Silian_module_list = ModulesManager.return_modules_list(
        target_from=Silian_msg.session_info.target_from, client_name=Silian_msg.session_info.client_name
    )
    Silian_alias = ModulesManager.modules_aliases

    if Silian_msg.parsed_msg:
        Silian_mdocs = []
        Silian_malias = []

        Silian_help_name = Silian_alias[Silian_module].split()[0] if Silian_module in Silian_alias else Silian_module.split()[0]
        if Silian_help_name in Silian_module_list:
            module_ = Silian_module_list[Silian_help_name]

            if not module_._db_load:
                await Silian_msg.finish(I18NContext("parser.module.unloaded", module=Silian_help_name))
            if module_.desc:
                Silian_desc = Silian_msg.session_info.locale.t_str(module_.desc)
                Silian_mdocs.append(Silian_desc)

            Silian_help_ = CommandParser(
                module_,
                msg=Silian_msg,
                module_name=module_.module_name,
                command_prefixes=Silian_msg.session_info.prefixes,
                is_superuser=Silian_is_superuser,
            )

            if Silian_help_.args:
                Silian_mdocs.append(Silian_help_.return_formatted_help_doc())

            Silian_regex_list = module_.regex_list.get(
                Silian_msg.session_info.target_from,
                show_required_superuser=Silian_is_superuser,
                show_required_base_superuser=Silian_is_base_superuser,
            )

            Silian_devs_msg = ""
            if (module_.required_superuser and not Silian_is_superuser) or (
                module_.required_base_superuser and not Silian_is_base_superuser
            ):
                pass
            elif module_.rss and not Silian_msg.session_info.support_rss:
                pass
            else:
                if Silian_regex_list:
                    Silian_mdocs.append(str(I18NContext("core.help.regex.note")))
                    for Silian_regex in Silian_regex_list:
                        pattern = None
                        if isinstance(Silian_regex.pattern, str):
                            pattern = Silian_regex.pattern
                        elif isinstance(Silian_regex.pattern, re.Pattern):
                            pattern = Silian_regex.pattern.pattern
                        if pattern:
                            if Silian_msg.session_info.support_markdown:
                                pattern = re.sub(r"([\\`*_{}\[\]()#+\-.!>~|])", r"\\\1", pattern)
                            rdesc = Silian_regex.desc
                            if rdesc:
                                rdesc = Silian_msg.session_info.locale.t_str(rdesc)
                                Silian_mdocs.append(
                                    f"{pattern}{str(I18NContext('core.message.help.regex.detail', msg=rdesc))}"
                                )
                            else:
                                Silian_mdocs.append(f"{pattern}{str(I18NContext('core.message.help.regex.no_information'))}")

                if module_.alias:
                    for a in module_.alias:
                        Silian_malias.append(f"{a} -> {module_.alias[a]}")
                if module_.developers and not module_.base:
                    Silian_devs_msg = str(I18NContext("core.help.author")) + "{I18N:message.delimiter}".join(
                        module_.developers
                    )
                else:
                    Silian_devs_msg = ""

            if module_.doc:
                if Silian_help_page_url := Config("help_page_url", cfg_type=str):
                    Silian_wiki_msg = str(
                        I18NContext(
                            "core.message.help.helpdoc.address", url=Silian_help_page_url.replace("${module}", Silian_help_name)
                        )
                    )
                elif Silian_help_url:
                    Silian_wiki_msg = str(I18NContext("core.message.help.helpdoc.address", url=Silian_help_url + Silian_help_name))
                else:
                    Silian_wiki_msg = ""
            else:
                Silian_wiki_msg = ""

            if (
                not Silian_msg.parsed_msg.get("--legacy", False)
                and Silian_msg.session_info.support_image
                and Bot.Info.web_render_status
            ):
                if (module_.required_superuser and not Silian_is_superuser) or (
                    module_.required_base_superuser and not Silian_is_base_superuser
                ):
                    pass
                elif module_.rss and not Silian_msg.session_info.support_rss:
                    pass
                elif any(
                    (module_.alias, module_.desc, module_.developers, Silian_help_.return_formatted_help_doc(), Silian_regex_list)
                ):
                    try:
                        Silian_html_content = await Silian_env.get_template("help_doc.html").render_async(
                            locale=Silian_msg.session_info.locale,
                            module=module_,
                            help=Silian_help_,
                            help_name=Silian_help_name,
                            regex_list=Silian_regex_list,
                            escape=escape,
                            isinstance=isinstance,
                            str=str,
                            repattern=re.Pattern,
                            use_font_mirror=Silian_use_font_mirror,
                        )

                        # fname = f"{random_cache_path()}.html"
                        # with open(fname, "w", encoding="utf-8") as fi:
                        #     fi.write(html_content)

                        Silian_images = await web_render.element_screenshot(
                            ElementScreenshotOptions(content=Silian_html_content, element=[".botbox"])
                        )

                        Silian_msgchain = MessageChain.assign(cb64imglst(Silian_images, bot_img=True))
                        if Silian_wiki_msg:
                            Silian_msgchain.append(Plain(Silian_wiki_msg.strip()))
                        await Silian_msg.finish(Silian_msgchain)
                    except Exception:
                        Logger.exception()

                if Silian_wiki_msg:
                    await Silian_msg.finish(Silian_wiki_msg.strip())
                else:
                    await Silian_msg.finish(I18NContext("core.help.info.none"))

            Silian_doc_msg = Silian_mdocs + [Silian_devs_msg, Silian_wiki_msg]
            if Silian_doc_msg:
                await Silian_msg.finish(Silian_doc_msg)
            else:
                await Silian_msg.finish(I18NContext("core.help.info.none"))
        else:
            await Silian_msg.finish(I18NContext("core.message.help.not_found"))


@Silian_hlp.command()
@Silian_hlp.command("[--legacy] {{I18N:core.help.help}}", options_desc={"--legacy": "{I18N:help.option.legacy}"})
async def _(Silian_msg: Bot.MessageSession):
    Silian_legacy_help = True
    if not Silian_msg.parsed_msg and Silian_msg.session_info.support_image:
        Silian_imgs = await help_generator(Silian_msg)
        if Silian_imgs:
            Silian_legacy_help = False

            Silian_help_msg_list = MessageChain.assign(
                I18NContext("core.message.help.all_modules", prefix=Silian_msg.session_info.prefixes[0])
            )
            if Silian_help_url:
                Silian_help_msg_list.append(I18NContext("core.message.help.document", url=Silian_help_url))
            if Silian_donate_url:
                Silian_help_msg_list.append(I18NContext("core.message.help.donate", url=Silian_donate_url))
            await Silian_msg.finish(Silian_imgs + Silian_help_msg_list)
    if Silian_legacy_help:
        Silian_is_base_superuser = Silian_msg.session_info.sender_id in Bot.base_superuser_list
        Silian_is_superuser = Silian_msg.check_super_user()
        Silian_module_list = ModulesManager.return_modules_list(
            target_from=Silian_msg.session_info.target_from, client_name=Silian_msg.session_info.client_name
        )
        Silian_target_enabled_list = Silian_msg.session_info.enabled_modules

        Silian_essential = []
        Silian_module_ = []

        for Silian_key, Silian_value in Silian_module_list.items():
            if Silian_key[0] == "_":
                continue
            if not Silian_value._db_load and not Silian_value.base:
                continue
            if Silian_value.hidden:
                continue
            if Silian_value.rss and not Silian_msg.session_info.support_rss:
                continue
            if not Silian_is_superuser and Silian_value.required_superuser or not Silian_is_base_superuser and Silian_value.required_base_superuser:
                continue

            if Silian_value.base:
                Silian_essential.append(Silian_key)
            else:
                Silian_module_.append(Silian_key)
        Silian_module_ = [Silian_m for Silian_m in Silian_module_ if Silian_m in Silian_target_enabled_list]

        Silian_help_msg = MessageChain.assign(I18NContext("core.message.help.legacy.base"))
        Silian_help_msg.append(Plain(" | ".join(Silian_essential), disable_joke=True))
        if Silian_module_:
            Silian_help_msg.append(I18NContext("core.message.help.legacy.external"))
            Silian_help_msg.append(Plain(" | ".join(Silian_module_), disable_joke=True))
        Silian_help_msg.append(I18NContext("core.message.help.detail", prefix=Silian_msg.session_info.prefixes[0]))
        Silian_help_msg.append(I18NContext("core.message.help.all_modules", prefix=Silian_msg.session_info.prefixes[0]))
        if Silian_help_url:
            Silian_help_msg.append(I18NContext("core.message.help.document", url=Silian_help_url))
        if Silian_donate_url:
            Silian_help_msg.append(I18NContext("core.message.help.donate", url=Silian_donate_url))
        await Silian_msg.finish(Silian_help_msg)


async def modules_list_help(msg: Bot.MessageSession, legacy):
    Silian_legacy_help = True
    if msg.session_info.support_image and not legacy:
        Silian_imgs = await help_generator(msg, show_disabled_modules=True, show_base_modules=False, show_dev_modules=False)
        if Silian_imgs:
            Silian_legacy_help = False
            Silian_help_msg = MessageChain.assign()
            if Silian_help_url:
                Silian_help_msg.append(I18NContext("core.message.help.document", url=Silian_help_url))
            await msg.finish(Silian_imgs + Silian_help_msg)
    if Silian_legacy_help:
        Silian_module_list = ModulesManager.return_modules_list(
            target_from=msg.session_info.target_from, client_name=msg.session_info.client_name
        )
        Silian_module_ = []
        for Silian_x in Silian_module_list:
            if Silian_x[0] == "_":
                continue
            if (
                Silian_module_list[Silian_x].base
                or Silian_module_list[Silian_x].hidden
                or not Silian_module_list[Silian_x]._db_load
                or Silian_module_list[Silian_x].required_superuser
                or Silian_module_list[Silian_x].required_base_superuser
            ):
                continue
            Silian_module_.append(Silian_module_list[Silian_x].module_name)
        if Silian_module_:
            Silian_help_msg = MessageChain.assign(
                [I18NContext("core.message.help.legacy.availables"), Plain(" | ".join(Silian_module_), disable_joke=True)]
            )
        else:
            Silian_help_msg = MessageChain.assign(I18NContext("core.message.help.legacy.availables.none"))
        Silian_help_msg.append(I18NContext("core.message.help.detail", prefix=msg.session_info.prefixes[0]))
        if Silian_help_url:
            Silian_help_msg.append(I18NContext("core.message.help.document", url=Silian_help_url))
        await msg.finish(Silian_help_msg)


async def help_generator(
    msg: Bot.MessageSession,
    show_base_modules: bool = True,
    show_disabled_modules: bool = False,
    show_dev_modules: bool = True,
):
    Silian_is_base_superuser = msg.session_info.sender_id in Bot.base_superuser_list
    Silian_is_superuser = msg.check_super_user()
    Silian_module_list = ModulesManager.return_modules_list(
        target_from=msg.session_info.target_from, client_name=msg.session_info.client_name
    )
    Silian_target_enabled_list = msg.session_info.enabled_modules

    Silian_dev_module_list = []
    Silian_essential = {}
    Silian_module_ = {}

    for Silian_key, Silian_value in Silian_module_list.items():
        if Silian_key[0] == "_":
            continue
        if not Silian_value._db_load and not Silian_value.base:
            continue
        if Silian_value.hidden:
            continue
        if Silian_value.rss and not msg.session_info.support_rss:
            continue
        if not Silian_is_superuser and Silian_value.required_superuser or not Silian_is_base_superuser and Silian_value.required_base_superuser:
            continue

        if Silian_value.base:
            Silian_essential[Silian_key] = Silian_value
        else:
            Silian_module_[Silian_key] = Silian_value

        if Silian_value.required_superuser or Silian_value.required_base_superuser:
            Silian_dev_module_list.append(Silian_key)

    if not show_disabled_modules:
        Silian_module_ = {Silian_k: Silian_v for Silian_k, Silian_v in Silian_module_.items() if Silian_k in Silian_target_enabled_list or Silian_k in Silian_dev_module_list}

    if show_base_modules:
        Silian_module_list = {**Silian_essential, **Silian_module_}
    else:
        Silian_module_list = Silian_module_

    if not show_dev_modules:
        Silian_module_list = {Silian_k: Silian_v for Silian_k, Silian_v in Silian_module_.items() if Silian_k not in Silian_dev_module_list}

    Silian_html_content = await Silian_env.get_template("module_list.html").render_async(
        msg=msg,
        locale=msg.session_info.locale,
        CommandParser=CommandParser,
        is_base_superuser=Silian_is_base_superuser,
        is_superuser=Silian_is_superuser,
        len=len,
        module_list=Silian_module_list,
        show_disabled_modules=show_disabled_modules,
        target_enabled_list=Silian_target_enabled_list,
        use_font_mirror=Silian_use_font_mirror,
    )
    Silian_fname = f"{random_cache_path()}.html"
    with open(Silian_fname, "w", encoding="utf-8") as Silian_fi:
        Silian_fi.write(Silian_html_content)

    Silian_images = await web_render.element_screenshot(ElementScreenshotOptions(content=Silian_html_content, element=[".botbox"]))
    if Silian_images:
        return cb64imglst(Silian_images, bot_img=True)
    return None
