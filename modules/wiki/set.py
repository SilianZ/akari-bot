import orjson

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image, Plain, Url
from core.config import Config
from core.utils.image_table import image_table_render, ImageTable
from . import wiki
from .database.models import WikiTargetInfo
from .utils.wikilib import WikiLib

Silian_enable_urlmanager = Config("enable_urlmanager", False)
Silian_wiki_whitelist_url = Config("wiki_whitelist_url", cfg_type=str, table_name="module_wiki")


@wiki.command("set <wikiurl> {{I18N:wiki.help.set}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_wikiurl: str):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    check = await WikiLib(Silian_wikiurl, headers=Silian_target.headers).check_wiki_available()
    if check.available:
        Silian_wiki_name = check.value.name
        if check.value.lang:
            Silian_wiki_name += f" ({check.value.lang})"
        Silian_in_allowlist = True
        if Bot.Info.use_url_manager:
            Silian_in_allowlist = check.value.in_allowlist
            if check.value.in_blocklist and not Silian_in_allowlist:
                await Silian_msg.finish(I18NContext("wiki.message.invalid.blocked", name=Silian_wiki_name))
        Silian_result = await Silian_target.add_start_wiki(check.value.api)
        if Silian_result and Silian_enable_urlmanager and not Silian_in_allowlist:
            Silian_prompt = "\n" + Silian_msg.session_info.locale.t("wiki.message.wiki_audit.untrust")
            if Silian_wiki_whitelist_url:
                Silian_prompt += "\n" + Silian_msg.session_info.locale.t(
                    "wiki.message.wiki_audit.untrust.address", url=Silian_wiki_whitelist_url
                )
        else:
            Silian_prompt = ""
        await Silian_msg.finish(Silian_msg.session_info.locale.t("wiki.message.set.success", name=Silian_wiki_name) + Silian_prompt)
    else:
        Silian_result = Silian_msg.session_info.locale.t("wiki.message.error.add") + (
            "\n" + Silian_msg.session_info.locale.t("wiki.message.error.info") + check.message if check.message != "" else ""
        )
        await Silian_msg.finish(Silian_result)


@wiki.command("iw add <interwiki> <wikiurl> {{I18N:wiki.help.iw.add}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_interwiki: str, Silian_wikiurl: str):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    check = await WikiLib(Silian_wikiurl, headers=Silian_target.headers).check_wiki_available()
    if check.available:
        Silian_wiki_name = check.value.name
        if check.value.lang:
            Silian_wiki_name += f" ({check.value.lang})"
        if Bot.Info.use_url_manager and check.value.in_blocklist and not check.value.in_allowlist:
            await Silian_msg.finish(Silian_msg.session_info.locale.t("wiki.message.invalid.blocked", name=Silian_wiki_name))
        Silian_result = await Silian_target.config_interwikis(Silian_interwiki, check.value.api)
        if Silian_result and Silian_enable_urlmanager and not check.value.in_allowlist:
            Silian_prompt = "\n" + Silian_msg.session_info.locale.t("wiki.message.wiki_audit.untrust")
            if Silian_wiki_whitelist_url:
                Silian_prompt += "\n" + Silian_msg.session_info.locale.t(
                    "wiki.message.wiki_audit.untrust.address", url=Silian_wiki_whitelist_url
                )

        else:
            Silian_prompt = ""
        await Silian_msg.finish(
            Silian_msg.session_info.locale.t("wiki.message.iw.add.success", iw=Silian_interwiki, name=Silian_wiki_name) + Silian_prompt
        )
    else:
        Silian_result = Silian_msg.session_info.locale.t("wiki.message.error.add") + (
            "\n" + Silian_msg.session_info.locale.t("wiki.message.error.info") + check.message if check.message != "" else ""
        )
        await Silian_msg.finish(Silian_result)


@wiki.command("iw remove <interwiki> {{I18N:wiki.help.iw.remove}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_interwiki: str):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_result = await Silian_target.config_interwikis(Silian_interwiki)
    if Silian_result:
        await Silian_msg.finish(I18NContext("wiki.message.iw.remove.success", iw=Silian_interwiki))


@wiki.command(
    "iw list [--legacy] {{I18N:wiki.help.iw.list}}",
    options_desc={"--legacy": "{I18N:help.option.legacy}"},
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    query = Silian_target.interwikis
    Silian_start_wiki = Silian_target.api_link
    Silian_base_interwiki_link = None
    if Silian_start_wiki:
        Silian_base_interwiki_link_ = await WikiLib(Silian_start_wiki, Silian_target.headers).parse_page_info(
            "Special:Interwiki", session=Silian_msg
        )
        if Silian_base_interwiki_link_.status:
            Silian_base_interwiki_link = Silian_base_interwiki_link_.link
    Silian_result = []
    if query != {}:
        if not Silian_msg.parsed_msg.get("--legacy", False) and Silian_msg.session_info.support_image:
            Silian_columns = [[Silian_x, query[Silian_x]] for Silian_x in query]
            Silian_imgs = await image_table_render(ImageTable(Silian_columns, ["Interwiki", "Url"]))
        else:
            Silian_imgs = None
        if Silian_imgs:
            Silian_img_list = [Image(Silian_ii) for Silian_ii in Silian_imgs]
            Silian_mt = [I18NContext("wiki.message.iw.list", prefix=Silian_msg.session_info.prefixes[0])]
            if Silian_base_interwiki_link:
                Silian_mt.append(I18NContext("wiki.message.iw.list.prompt", url=str(Url(Silian_base_interwiki_link))))
            await Silian_msg.finish(Silian_img_list + Silian_mt)
        else:
            Silian_result.append(I18NContext("wiki.message.iw.list.legacy"))
            for x in query:
                Silian_result.append(Plain(f"{x}: {query[x]}"))
    else:
        Silian_result.append(I18NContext("wiki.message.iw.list.none", prefix=Silian_msg.session_info.prefixes[0]))
    if Silian_base_interwiki_link:
        Silian_result.append(I18NContext("wiki.message.iw.list.prompt", url=str(Url(Silian_base_interwiki_link))))
    await Silian_msg.finish(Silian_result)


@wiki.command("iw get <interwiki> {{I18N:wiki.help.iw.get}}")
async def _(Silian_msg: Bot.MessageSession, Silian_interwiki: str):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_query = Silian_target.interwikis
    if Silian_query != {}:
        if Silian_interwiki in Silian_query:
            await Silian_msg.finish(Url(Silian_query[Silian_interwiki], use_mm=False))
        else:
            await Silian_msg.finish(I18NContext("wiki.message.iw.get.not_found", iw=Silian_interwiki))
    else:
        await Silian_msg.finish(I18NContext("wiki.message.iw.list.none", prefix=Silian_msg.session_info.prefixes[0]))


@wiki.command("headers show {{I18N:wiki.help.headers.show}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    await Silian_msg.finish(
        I18NContext(
            "wiki.message.headers.show",
            headers=orjson.dumps(Silian_target.headers).decode(),
            prefix=Silian_msg.session_info.prefixes[0],
        )
    )


@wiki.command("headers add <headers> {{I18N:wiki.help.headers.add}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_headers: str):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_add = await Silian_target.config_headers(Silian_headers)
    if Silian_add:
        await Silian_msg.finish(I18NContext("wiki.message.headers.add.success", headers=orjson.dumps(Silian_target.headers).decode()))
    else:
        await Silian_msg.finish(I18NContext("wiki.message.headers.add.failed"))


@wiki.command("headers remove <headerkey> {{I18N:wiki.help.headers.remove}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_headerkey: str):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_delete = await Silian_target.config_headers(Silian_headerkey, add=False)
    if Silian_delete:
        await Silian_msg.finish(I18NContext("wiki.message.headers.add.success", headers=orjson.dumps(Silian_target.headers).decode()))


@wiki.command("headers reset {{I18N:wiki.help.headers.reset}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_reset = await Silian_target.config_headers()
    if Silian_reset:
        await Silian_msg.finish(I18NContext("wiki.message.headers.reset.success"))


@wiki.command("prefix set <prefix> {{I18N:wiki.help.prefix.set}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_prefix: str):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_set_prefix = await Silian_target.config_prefix(Silian_prefix)
    if Silian_set_prefix:
        await Silian_msg.finish(I18NContext("wiki.message.prefix.set.success", wiki_prefix=Silian_prefix))


@wiki.command("prefix reset {{I18N:wiki.help.prefix.reset}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession):
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_set_prefix = await Silian_target.config_prefix()
    if Silian_set_prefix:
        await Silian_msg.finish(I18NContext("wiki.message.prefix.reset.success"))


@wiki.command("redlink {{I18N:wiki.help.redlink}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession):
    Silian_redlink_state = Silian_msg.session_info.target_info.target_data.get("wiki_redlink")

    if Silian_redlink_state:
        await Silian_msg.session_info.target_info.edit_target_data("wiki_redlink", False)
        await Silian_msg.finish(I18NContext("wiki.message.redlink.disable"))
    else:
        await Silian_msg.session_info.target_info.edit_target_data("wiki_redlink", True)
        await Silian_msg.finish(I18NContext("wiki.message.redlink.enable"))
