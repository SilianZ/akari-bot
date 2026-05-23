from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image
from core.component import module
from core.utils.image_table import image_table_render, ImageTable
from .database.models import WikiAllowList, WikiBlockList
from .utils.wikilib import WikiLib

Silian_aud = module(
    "wiki_audit",
    required_superuser=True,
    alias="wau",
    doc=True,
)


@Silian_aud.command(["trust <apilink>", "block <apilink>"])
async def _(Silian_msg: Bot.MessageSession, Silian_apilink: str):
    Silian_check = await WikiLib(Silian_apilink).check_wiki_available()
    if Silian_check.available:
        Silian_apilink = Silian_check.value.api
        if Silian_msg.parsed_msg.get("trust", False):
            Silian_res = await WikiAllowList.add(Silian_apilink)
            Silian_list_name = Silian_msg.session_info.locale.t("wiki.message.wiki_audit.list_name.allowlist")
        else:
            Silian_res = await WikiBlockList.add(Silian_apilink)
            Silian_list_name = Silian_msg.session_info.locale.t("wiki.message.wiki_audit.list_name.blocklist")
        if not Silian_res:
            await Silian_msg.finish(
                Silian_msg.session_info.locale.t(
                    "wiki.message.wiki_audit.add.failed",
                    list_name=Silian_list_name,
                    api=Silian_apilink,
                )
            )
        else:
            await Silian_msg.finish(
                Silian_msg.session_info.locale.t(
                    "wiki.message.wiki_audit.add.success",
                    list_name=Silian_list_name,
                    api=Silian_apilink,
                )
            )
    else:
        Silian_result = Silian_msg.session_info.locale.t("wiki.message.error.add") + (
            "\n" + Silian_msg.session_info.locale.t("wiki.message.error.info") + Silian_check.message if Silian_check.message != "" else ""
        )
        await Silian_msg.finish(Silian_result)


@Silian_aud.command(["distrust <apilink>", "unblock <apilink>"])
async def _(Silian_msg: Bot.MessageSession, Silian_apilink: str):
    Silian_check = await WikiLib(Silian_apilink).check_wiki_info_from_database_cache()
    if Silian_check.available:
        Silian_apilink = Silian_check.value.api
    if Silian_msg.parsed_msg.get("distrust", False):
        Silian_res = await WikiAllowList.remove(Silian_apilink)  # 已关闭的站点无法验证有效性
        if not Silian_res:
            await Silian_msg.finish(Silian_msg.session_info.locale.t("wiki.message.wiki_audit.remove.failed.other", api=Silian_apilink))
        Silian_list_name = Silian_msg.session_info.locale.t("wiki.message.wiki_audit.list_name.allowlist")
    else:
        Silian_res = WikiBlockList.remove(Silian_apilink)
        Silian_list_name = Silian_msg.session_info.locale.t("wiki.message.wiki_audit.list_name.blocklist")
    if not Silian_res:
        await Silian_msg.finish(
            Silian_msg.session_info.locale.t(
                "wiki.message.wiki_audit.remove.failed",
                list_name=Silian_list_name,
                api=Silian_apilink,
            )
        )
    else:
        await Silian_msg.finish(
            Silian_msg.session_info.locale.t(
                "wiki.message.wiki_audit.remove.success",
                list_name=Silian_list_name,
                api=Silian_apilink,
            )
        )


@Silian_aud.command("query <apilink>")
async def _(Silian_msg: Bot.MessageSession, Silian_apilink: str):
    Silian_check = await WikiLib(Silian_apilink).check_wiki_available()
    if Silian_check.available:
        Silian_apilink = Silian_check.value.api
        Silian_msg_list = []
        Silian_allow = await WikiAllowList.check(Silian_apilink)
        Silian_block = await WikiBlockList.check(Silian_apilink)
        if Silian_allow:
            Silian_msg_list.append(Silian_msg.session_info.locale.t("wiki.message.wiki_audit.query.allowlist", api=Silian_apilink))
        if Silian_block:
            Silian_msg_list.append(Silian_msg.session_info.locale.t("wiki.message.wiki_audit.query.blocklist", api=Silian_apilink))
        if Silian_allow and Silian_block:
            Silian_msg_list.append(Silian_msg.session_info.locale.t("wiki.message.wiki_audit.query.conflict"))
        if not Silian_msg_list:
            Silian_msg_list.append(Silian_msg.session_info.locale.t("wiki.message.wiki_audit.query.none", api=Silian_apilink))
        await Silian_msg.finish(Silian_msg_list)
    else:
        Silian_result = Silian_msg.session_info.locale.t("wiki.message.error.query") + (
            "\n" + Silian_msg.session_info.locale.t("wiki.message.error.info") + Silian_check.message if Silian_check.message != "" else ""
        )
        await Silian_msg.finish(Silian_result)


@Silian_aud.command("list [--legacy]")
async def _(msg: Bot.MessageSession):
    Silian_allow_list = await WikiAllowList.all().values("api_link", "timestamp")
    Silian_block_list = await WikiBlockList.all().values("api_link", "timestamp")
    Silian_legacy = True
    if not msg.parsed_msg.get("--legacy", False) and msg.session_info.support_image:
        Silian_send_msgs = []
        Silian_allow_columns = [
            [Silian_x["api_link"], msg.format_time(Silian_x["timestamp"].timestamp(), iso=True, timezone=False)] for Silian_x in Silian_allow_list
        ]

        if Silian_allow_columns:
            Silian_allow_table = ImageTable(
                data=Silian_allow_columns,
                headers=[
                    "{I18N:wiki.message.wiki_audit.list.table.header.apilink}",
                    "{I18N:wiki.message.wiki_audit.list.table.header.date}",
                ],
                session_info=msg.session_info,
            )
            if Silian_allow_table:
                Silian_allow_image = await image_table_render(Silian_allow_table)
                if Silian_allow_image:
                    Silian_send_msgs.append(I18NContext("wiki.message.wiki_audit.list.allowlist"))
                    for Silian_im in Silian_allow_image:
                        Silian_send_msgs.append(Image(Silian_im))
        Silian_block_columns = [
            [Silian_x["api_link"], msg.format_time(Silian_x["timestamp"].timestamp(), iso=True, timezone=False)] for Silian_x in Silian_block_list
        ]
        if Silian_block_columns:
            Silian_block_table = ImageTable(
                data=Silian_block_columns,
                headers=[
                    "{I18N:wiki.message.wiki_audit.list.table.header.apilink}",
                    "{I18N:wiki.message.wiki_audit.list.table.header.date}",
                ],
                session_info=msg.session_info,
            )
            if Silian_block_table:
                Silian_block_image = await image_table_render(Silian_block_table)
                if Silian_block_image:
                    Silian_send_msgs.append(I18NContext("wiki.message.wiki_audit.list.blocklist"))
                    for Silian_im in Silian_block_image:
                        Silian_send_msgs.append(Image(Silian_im))
        if Silian_send_msgs:
            Silian_legacy = False
            await msg.finish(Silian_send_msgs)
    if Silian_legacy:
        Silian_wikis = []
        if Silian_allow_list:
            Silian_wikis.append(msg.session_info.locale.t("wiki.message.wiki_audit.list.allowlist"))
            for al in Silian_allow_list:
                Silian_wikis.append(f"{al[0]} ({msg.format_time(al[1].timestamp(), iso=True, timezone=False)})")
        if Silian_block_list:
            Silian_wikis.append(msg.session_info.locale.t("wiki.message.wiki_audit.list.blocklist"))
            for bl in Silian_block_list:
                Silian_wikis.append(f"{bl[0]} ({bl[1]})")
        if Silian_wikis:
            await msg.finish(Silian_wikis)
        else:
            await msg.finish(I18NContext("wiki.message.wiki_audit.list.none"))
