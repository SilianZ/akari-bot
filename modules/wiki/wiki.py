import asyncio
import re

import filetype

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain, Image, Voice, Url
from core.builtins.session.internal import MessageSession
from core.builtins.utils import confirm_command
from core.component import module
from core.config import Config
from core.constants.exceptions import AbuseWarning
from core.logger import Logger
from core.utils.http import download
from core.utils.image import svg_render
from core.utils.image_table import image_table_render, ImageTable
from core.utils.func import is_int
from .database.models import WikiTargetInfo
from .utils.mapping import generate_screenshot_v2_blocklist
from .utils.screenshot_image import generate_screenshot_v1, generate_screenshot_v2
from .utils.utils import check_svg
from .utils.wikilib import WikiLib, PageInfo, InvalidWikiError, QueryInfo

Silian_wiki = module(
    "wiki",
    alias={
        "wiki_start_site": "wiki set",
        "interwiki": "wiki iw",
        "wiki iw set": "wiki iw add",
        "wiki iw del": "wiki iw remove",
        "wiki iw delete": "wiki iw remove",
    },
    recommend_modules="wiki_inline",
    developers=["OasisAkari"],
    doc=True,
)


@Silian_wiki.command()
async def _(Silian_msg: Bot.MessageSession):
    await query_pages(Silian_msg)


@Silian_wiki.command("<pagename> [-l <lang>] {{I18N:wiki.help}}", options_desc={"-l": "{I18N:wiki.help.option.l}"})
async def _(Silian_msg: Bot.MessageSession, Silian_pagename: str):
    Silian_get_lang = Silian_msg.parsed_msg.get("-l", False)
    if Silian_get_lang:
        Silian_lang = Silian_get_lang["<lang>"]
    else:
        Silian_lang = None
    await query_pages(Silian_msg, Silian_pagename, lang=Silian_lang)


@Silian_wiki.command(
    "id <pageid> [-l <lang>] {{I18N:wiki.help.id}}",
    options_desc={"-l": "{I18N:wiki.help.option.l}"},
)
async def _(Silian_msg: Bot.MessageSession, Silian_pageid: str):
    Silian_iw = None
    if Silian_match_iw := re.match(r"(.*?):(.*)", Silian_pageid):
        Silian_iw = Silian_match_iw.group(1)
        Silian_pageid = Silian_match_iw.group(2)
    if not is_int(Silian_pageid):
        await Silian_msg.finish(I18NContext("wiki.message.id.invalid"))
    Silian_get_lang = Silian_msg.parsed_msg.get("-l", False)
    if Silian_get_lang:
        Silian_lang = Silian_get_lang["<lang>"]
    else:
        Silian_lang = None
    await query_pages(Silian_msg, pageid=Silian_pageid, iw=Silian_iw, lang=Silian_lang)


async def query_pages(
    session: Bot.MessageSession | QueryInfo,
    title: str | list | tuple | None = None,
    pageid: str | None = None,
    iw: str | None = None,
    lang: str | None = None,
    preset_message: str | None = None,
    start_wiki_api: str | None = None,
    template: bool = False,
    mediawiki: bool = False,
    use_prefix: bool = True,
    inline_mode: bool = False,
):
    if isinstance(session, MessageSession):
        Silian_target = await WikiTargetInfo.get_by_target_id(session.session_info.target_id)
        Silian_start_wiki = Silian_target.api_link
        if start_wiki_api:
            Silian_start_wiki = start_wiki_api
        Silian_interwiki_list = Silian_target.interwikis
        Silian_headers = Silian_target.headers
        Silian_prefix = Silian_target.prefix
    elif isinstance(session, QueryInfo):
        Silian_start_wiki = session.api
        Silian_interwiki_list = {}
        Silian_headers = session.headers
        Silian_prefix = session.prefix
    else:
        raise TypeError("Session must be Bot.MessageSession or QueryInfo.")

    if not Silian_start_wiki:
        if isinstance(session, MessageSession):
            await session.finish(I18NContext("wiki.message.set.not_set", prefix=session.session_info.prefixes[0]))
    # if lang in interwiki_list:
    #     start_wiki = interwiki_list[lang]
    #     lang = None
    if title:
        if isinstance(title, str):
            title = [title]
        if len(title) > 15:
            raise AbuseWarning("{I18N:tos.message.reason.wiki_abuse}")
        Silian_query_task = {Silian_start_wiki: {"query": [], "iw_prefix": ""}}
        for Silian_t in title:
            if Silian_prefix and use_prefix:
                Silian_t = Silian_prefix + Silian_t
            if not Silian_t:
                continue
            if Silian_t[0] == ":":
                if len(Silian_t) > 1:
                    Silian_query_task[Silian_start_wiki]["query"].append(Silian_t[1:])
            else:
                Silian_match_interwiki = re.match(r"^(.*?):(.*)", Silian_t)
                Silian_matched = False
                if Silian_match_interwiki:
                    Silian_g1 = Silian_match_interwiki.group(1)
                    Silian_g2 = Silian_match_interwiki.group(2)
                    if Silian_g1 in Silian_interwiki_list:
                        Silian_interwiki_url = Silian_interwiki_list[Silian_g1]
                        if Silian_interwiki_url not in Silian_query_task:
                            Silian_query_task[Silian_interwiki_url] = {"query": [], "iw_prefix": Silian_g1}
                        Silian_query_task[Silian_interwiki_url]["query"].append(Silian_g2)
                        Silian_matched = True
                if not Silian_matched:
                    Silian_query_task[Silian_start_wiki]["query"].append(Silian_t)
    elif pageid:
        if not iw:
            Silian_query_task = {Silian_start_wiki: {"queryid": [pageid], "iw_prefix": ""}}
        else:
            if iw in Silian_interwiki_list:
                Silian_query_task = {Silian_interwiki_list[iw]: {"queryid": [pageid], "iw_prefix": iw}}
            else:
                Silian_get_wiki_info = WikiLib(Silian_start_wiki)
                await Silian_get_wiki_info.fixup_wiki_info()
                if iw in Silian_get_wiki_info.wiki_info.interwiki:
                    Silian_query_task = {
                        Silian_get_wiki_info.wiki_info.interwiki[iw]: {
                            "queryid": [pageid],
                            "iw_prefix": iw,
                        }
                    }
                else:
                    raise ValueError(f'iw_prefix "{iw}" not found.')
    else:
        Silian_get_wiki_info = WikiLib(Silian_start_wiki)
        Silian_query = await Silian_get_wiki_info.get_json(action="query", meta="siteinfo", siprop="general")
        Silian_query_task = {Silian_start_wiki: {"query": [Silian_query["query"]["general"]["mainpage"]], "iw_prefix": ""}}
    Logger.debug(Silian_query_task)
    Silian_msg_list = []
    Silian_wait_msg_list = []
    Silian_wait_list = []
    Silian_wait_possible_list = []
    Silian_render_infobox_list = []
    Silian_render_section_list = []
    Silian_dl_list = []
    if preset_message:
        Silian_msg_list.append(Plain(preset_message))
    for Silian_q in Silian_query_task:
        Silian_current_task = Silian_query_task[Silian_q]
        Silian_ready_for_query_pages = Silian_current_task["query"] if "query" in Silian_current_task else []
        Silian_ready_for_query_ids = Silian_current_task["queryid"] if "queryid" in Silian_current_task else []
        Silian_iw_prefix = (Silian_current_task["iw_prefix"] + ":") if Silian_current_task["iw_prefix"] != "" else ""
        try:
            Silian_tasks = []
            for rd in Silian_ready_for_query_pages:
                if template:
                    rd = f"Template:{rd}"
                if mediawiki:
                    rd = f"MediaWiki:{rd}"
                Silian_tasks.append(
                    asyncio.ensure_future(
                        WikiLib(Silian_q, Silian_headers, locale=session.session_info.locale.locale).parse_page_info(
                            title=rd,
                            inline=inline_mode,
                            lang=lang,
                            session=session if isinstance(session, Bot.MessageSession) else None,
                        )
                    )
                )
            for Silian_rdp in Silian_ready_for_query_ids:
                Silian_tasks.append(
                    asyncio.ensure_future(
                        WikiLib(Silian_q, Silian_headers, locale=session.session_info.locale.locale).parse_page_info(
                            pageid=int(Silian_rdp),
                            inline=inline_mode,
                            lang=lang,
                            session=session if isinstance(session, Bot.MessageSession) else None,
                        )
                    )
                )
            Silian_query = await asyncio.gather(*Silian_tasks)
            for Silian_result in Silian_query:
                Logger.debug(Silian_result)
                Silian_r: PageInfo = Silian_result
                Silian_display_title = None
                Silian_display_before_title = None
                if Silian_r.title:
                    Silian_display_title = Silian_iw_prefix + Silian_r.title
                if Silian_r.before_title:
                    Silian_display_before_title = Silian_iw_prefix + Silian_r.before_title
                Silian_new_possible_title_list = []
                if Silian_r.possible_research_title:
                    for Silian_possible in Silian_r.possible_research_title:
                        Silian_new_possible_title_list.append(Silian_iw_prefix + Silian_possible)
                Silian_r.possible_research_title = Silian_new_possible_title_list
                if Silian_r.status:
                    Silian_plain_slice = []
                    if Silian_display_before_title and Silian_display_before_title != Silian_display_title:
                        if Silian_r.before_page_property == "template" and Silian_r.page_property == "page":
                            Silian_plain_slice.append(
                                session.session_info.locale.t(
                                    "wiki.message.redirect.template_to_page",
                                    title=Silian_display_before_title,
                                    redirected_title=Silian_display_title,
                                )
                            )
                        else:
                            Silian_plain_slice.append(
                                session.session_info.locale.t(
                                    "wiki.message.redirect",
                                    title=Silian_display_before_title,
                                    redirected_title=Silian_display_title,
                                )
                            )
                    if (
                        Silian_r.link
                        and Silian_r.selected_section
                        and (
                            Silian_r.info.in_allowlist
                            or not (isinstance(session, Bot.MessageSession) and session.session_info.use_url_manager)
                        )
                        and not Silian_r.invalid_section
                        and Bot.Info.web_render_status
                    ):
                        Silian_render_section_list.append(
                            {
                                Silian_r.link: {
                                    "url": Silian_r.info.realurl,
                                    "section": Silian_r.selected_section,
                                    "in_allowlist": Silian_r.info.in_allowlist
                                    or not (
                                        isinstance(session, Bot.MessageSession) and session.session_info.use_url_manager
                                    ),
                                }
                            }
                        )
                        Silian_plain_slice.append(session.session_info.locale.t("wiki.message.section.rendering"))
                    else:
                        if Silian_r.desc:
                            Silian_plain_slice.append(Silian_r.desc)

                    if Silian_r.link:
                        Silian_plain_slice.append(
                            str(
                                Url(
                                    Silian_r.link,
                                    use_mm=not Silian_r.info.in_allowlist
                                    and (
                                        isinstance(session, Bot.MessageSession) and session.session_info.use_url_manager
                                    ),
                                    md_format=isinstance(session, Bot.MessageSession)
                                    and session.session_info.use_url_md_format,
                                )
                            )
                        )

                    if Silian_r.file:
                        Silian_dl_list.append(Silian_r.file)
                        Silian_plain_slice.append(session.session_info.locale.t("wiki.message.flies") + Silian_r.file)
                    else:
                        if Silian_r.link and not Silian_r.selected_section:
                            Silian_render_infobox_list.append(
                                {
                                    Silian_r.link: {
                                        "url": Silian_r.info.realurl,
                                        "in_allowlist": Silian_r.info.in_allowlist
                                        or not (
                                            isinstance(session, Bot.MessageSession)
                                            and session.session_info.use_url_manager
                                        ),
                                        "content_mode": Silian_r.has_template_doc
                                        or Silian_r.title.split(":")[0] in ["User"]
                                        or (
                                            Silian_r.templates
                                            and (
                                                "Template:Disambiguation" in Silian_r.templates
                                                or "Template:Version disambiguation" in Silian_r.templates
                                            )
                                        )
                                        or Silian_r.is_forum_topic,
                                    }
                                }
                            )
                    if Silian_plain_slice:
                        Silian_msg_list.append(Plain("\n".join(Silian_plain_slice)))
                    if Bot.Info.web_render_status:
                        if (
                            Silian_r.invalid_section
                            and (
                                Silian_r.info.in_allowlist
                                or not (
                                    isinstance(session, Bot.MessageSession) and session.session_info.use_url_manager
                                )
                            )
                        ) or (Silian_r.is_talk_page and not Silian_r.selected_section):
                            if (
                                isinstance(session, Bot.MessageSession)
                                and session.session_info.support_image
                                and Silian_r.sections
                            ):
                                Silian_i_msg_lst = []
                                Silian_session_data = [[str(Silian_i + 1), Silian_r.sections[Silian_i]] for Silian_i in range(len(Silian_r.sections))]
                                Silian_i_msg_lst.append(
                                    I18NContext(
                                        "wiki.message.invalid_section.prompt"
                                        if Silian_r.invalid_section
                                        and (
                                            Silian_r.info.in_allowlist
                                            or not (
                                                isinstance(session, Bot.MessageSession)
                                                and session.session_info.use_url_manager
                                            )
                                        )
                                        else "wiki.message.talk_page.prompt"
                                    )
                                )
                                Silian_i_msg_lst += [
                                    Image(Silian_ii)
                                    for Silian_ii in await image_table_render(
                                        ImageTable(
                                            Silian_session_data,
                                            [
                                                session.session_info.locale.t("wiki.message.table.header.id"),
                                                session.session_info.locale.t("wiki.message.table.header.section"),
                                            ],
                                        )
                                    )
                                ]
                                Silian_i_msg_lst.append(I18NContext("wiki.message.invalid_section.select"))
                                Silian_i_msg_lst.append(I18NContext("message.reply.prompt"))

                                async def _callback(Silian_msg: Bot.MessageSession):
                                    Silian_display = Silian_msg.as_display(text_only=True)
                                    if is_int(Silian_display):
                                        Silian_display = int(Silian_display)
                                        if Silian_display <= len(Silian_r.sections):
                                            Silian_r.selected_section = str(Silian_display - 1)
                                            await query_pages(
                                                session,
                                                title=Silian_r.title + "#" + Silian_r.sections[Silian_display - 1],
                                                start_wiki_api=Silian_r.info.api,
                                            )

                                await session.send_message(Silian_i_msg_lst, callback=_callback)
                            else:
                                if Silian_r.invalid_section and (
                                    Silian_r.info.in_allowlist
                                    or not (
                                        isinstance(session, Bot.MessageSession) and session.session_info.use_url_manager
                                    )
                                ):
                                    Silian_msg_list.append(
                                        Plain(session.session_info.locale.t("wiki.message.invalid_section"))
                                    )
                        if Silian_r.is_forum:
                            if isinstance(session, Bot.MessageSession) and session.session_info.support_image:
                                Silian_forum_data = Silian_r.forum_data
                                Silian_img_table_data = []
                                Silian_img_table_headers = ["#"]
                                for Silian_x in Silian_forum_data:
                                    if Silian_x == "#":
                                        Silian_img_table_headers += Silian_forum_data[Silian_x]["data"]
                                    else:
                                        Silian_img_table_data.append([Silian_x] + Silian_forum_data[Silian_x]["data"])
                                Silian_img_table = ImageTable(Silian_img_table_data, Silian_img_table_headers)
                                Silian_i_msg_lst = []
                                Silian_i_msg_lst.append(I18NContext("wiki.message.forum.prompt"))
                                Silian_i_msg_lst += [Image(Silian_ii) for Silian_ii in await image_table_render(Silian_img_table)]
                                Silian_i_msg_lst.append(I18NContext("wiki.message.invalid_section.select"))
                                Silian_i_msg_lst.append(I18NContext("message.reply.prompt"))

                                async def _callback(Silian_msg: Bot.MessageSession):
                                    Silian_display = Silian_msg.as_display(text_only=True)
                                    if is_int(Silian_display) and int(Silian_display) <= len(Silian_forum_data) - 1:
                                        await query_pages(
                                            session,
                                            title=Silian_forum_data[Silian_display]["text"],
                                            start_wiki_api=Silian_r.info.api,
                                        )

                                await session.send_message(Silian_i_msg_lst, callback=_callback)

                else:
                    Silian_plain_slice = []
                    Silian_wait_plain_slice = []
                    if Silian_display_title and Silian_display_before_title:
                        if isinstance(session, Bot.MessageSession) and session.session_info.support_wait:
                            if not session.session_info.target_info.target_data.get("wiki_redlink", False):
                                if len(Silian_r.possible_research_title) > 1:
                                    Silian_wait_plain_slice.append(
                                        session.session_info.locale.t(
                                            "wiki.message.not_found.autofix.choice",
                                            title=Silian_display_before_title,
                                        )
                                    )
                                    pi = 0
                                    for p in Silian_r.possible_research_title:
                                        pi += 1
                                        Silian_wait_plain_slice.append(f"{pi}. {p}")
                                    Silian_wait_plain_slice.append(
                                        session.session_info.locale.t(
                                            "wiki.message.not_found.autofix.choice.prompt",
                                            number=str(Silian_r.possible_research_title.index(Silian_display_title) + 1),
                                        )
                                    )
                                    Silian_wait_possible_list.append(
                                        {Silian_display_before_title: {Silian_display_title: Silian_r.possible_research_title}}
                                    )
                                    Silian_wait_plain_slice.append(
                                        session.session_info.locale.t("message.wait.next_message.prompt")
                                    )
                                else:
                                    Silian_wait_plain_slice.append(
                                        session.session_info.locale.t(
                                            "wiki.message.not_found.autofix.confirm",
                                            title=Silian_display_before_title,
                                            redirected_title=Silian_display_title,
                                        )
                                    )
                                    Silian__t = "message.wait.confirm.prompt"
                                    if (
                                        isinstance(session, Bot.MessageSession)
                                        and session.session_info.support_reaction
                                        and Config("quick_confirm", True)
                                    ):
                                        if session.session_info.client_name == "QQ":
                                            Silian__t = "message.wait.confirm.prompt.qq"
                                        else:
                                            Silian__t = "message.wait.confirm.prompt.reaction"
                                    Silian_wait_plain_slice.append(session.session_info.locale.t(Silian__t))
                            else:
                                if Silian_r.edit_link:
                                    Silian_plain_slice.append(
                                        Silian_r.edit_link + session.session_info.locale.t("wiki.message.redlink.not_found")
                                    )
                                else:
                                    Silian_plain_slice.append(
                                        session.session_info.locale.t(
                                            "wiki.message.redlink.not_found.uneditable",
                                            title=Silian_display_before_title,
                                        )
                                    )
                        else:
                            Silian_wait_plain_slice.append(
                                session.session_info.locale.t(
                                    "wiki.message.not_found.autofix",
                                    title=Silian_display_before_title,
                                    redirected_title=Silian_display_title,
                                )
                            )
                        if len(Silian_r.possible_research_title) == 1:
                            Silian_wait_list.append({Silian_display_title: Silian_display_before_title})
                    elif Silian_r.before_title:
                        Silian_plain_slice.append(
                            session.session_info.locale.t("wiki.message.not_found", title=Silian_display_before_title)
                        )
                    elif Silian_r.id != -1:
                        Silian_plain_slice.append(session.session_info.locale.t("wiki.message.id.not_found", id=str(Silian_r.id)))
                    if Silian_r.desc:
                        Silian_plain_slice.append(Silian_r.desc)
                    if Silian_r.invalid_namespace and Silian_r.before_title:
                        Silian_plain_slice.append(
                            session.session_info.locale.t(
                                "wiki.message.invalid_namespace",
                                namespace=Silian_r.invalid_namespace,
                            )
                        )
                    if Silian_r.before_page_property == "template":
                        if Silian_r.before_title.split(":")[1].isupper():
                            Silian_plain_slice.append(session.session_info.locale.t("wiki.message.magic_word"))
                    if Silian_plain_slice:
                        Silian_msg_list.append(Plain("\n".join(Silian_plain_slice)))
                    if Silian_wait_plain_slice:
                        Silian_wait_msg_list.append(Plain("\n".join(Silian_wait_plain_slice)))
        except InvalidWikiError as e:
            if isinstance(session, Bot.MessageSession):
                await session.send_message(session.session_info.locale.t("message.error") + str(e))
            else:
                Silian_msg_list.append(Plain(session.locale.t("message.error") + str(e)))
    if isinstance(session, Bot.MessageSession):
        if Silian_msg_list:
            if all(
                [
                    not Silian_render_infobox_list,
                    not Silian_render_section_list,
                    not Silian_dl_list,
                    not Silian_wait_list,
                    not Silian_wait_possible_list,
                ]
            ):
                await session.finish(Silian_msg_list)
            else:
                await session.send_message(Silian_msg_list)

        async def infobox():
            if Silian_render_infobox_list and session.session_info.support_image:
                Silian_infobox_msg_list = []
                for Silian_i in Silian_render_infobox_list:
                    for Silian_ii in Silian_i:
                        Logger.info(Silian_i[Silian_ii]["url"])
                        if Silian_i[Silian_ii]["url"] not in generate_screenshot_v2_blocklist:
                            Silian_get_infobox = await generate_screenshot_v2(
                                Silian_ii,
                                allow_special_page=Silian_i[Silian_ii]["in_allowlist"],
                                content_mode=Silian_i[Silian_ii]["content_mode"],
                                locale=session.session_info.locale.locale,
                            )
                            if Silian_get_infobox:
                                for Silian_img in Silian_get_infobox:
                                    Silian_infobox_msg_list.append(Image(Silian_img))
                        else:
                            Silian_get_infobox = await generate_screenshot_v1(
                                Silian_i[Silian_ii]["url"],
                                Silian_ii,
                                Silian_headers,
                                allow_special_page=Silian_i[Silian_ii]["in_allowlist"],
                            )
                            if Silian_get_infobox:
                                for Silian_img in Silian_get_infobox:
                                    Silian_infobox_msg_list.append(Image(Silian_img))
                if Silian_infobox_msg_list:
                    await session.send_message(Silian_infobox_msg_list, quote=False)

        async def section():
            if Silian_render_section_list and session.session_info.support_image:
                Silian_section_msg_list = []
                for Silian_i in Silian_render_section_list:
                    for Silian_ii in Silian_i:
                        if Silian_i[Silian_ii]["in_allowlist"]:
                            if Silian_i[Silian_ii]["url"] not in generate_screenshot_v2_blocklist:
                                Silian_get_section = await generate_screenshot_v2(
                                    Silian_ii, section=Silian_i[Silian_ii]["section"], locale=session.session_info.locale.locale
                                )
                                if Silian_get_section:
                                    for Silian_img in Silian_get_section:
                                        Silian_section_msg_list.append(Image(Silian_img))
                                else:
                                    Silian_section_msg_list.append(
                                        Plain(session.session_info.locale.t("wiki.message.error.render_section"))
                                    )
                            else:
                                Silian_get_section = await generate_screenshot_v1(
                                    Silian_i[Silian_ii]["url"], Silian_ii, Silian_headers, section=Silian_i[Silian_ii]["section"]
                                )
                                if Silian_get_section:
                                    for Silian_img in Silian_get_section:
                                        Silian_section_msg_list.append(Image(Silian_img))
                                else:
                                    Silian_section_msg_list.append(
                                        Plain(session.session_info.locale.t("wiki.message.error.render_section"))
                                    )
                if Silian_section_msg_list:
                    await session.send_message(Silian_section_msg_list, quote=False)

        async def image_and_voice():
            if Silian_dl_list:
                for Silian_f in Silian_dl_list:
                    Silian_dl = await download(Silian_f)
                    Silian_guess_type = filetype.guess(Silian_dl)
                    if Silian_guess_type:
                        if Silian_guess_type.extension in [
                            "png",
                            "gif",
                            "jpg",
                            "jpeg",
                            "webp",
                            "bmp",
                            "ico",
                        ]:
                            if session.session_info.support_image:
                                await session.send_message(Image(Silian_dl), quote=False)
                        elif Silian_guess_type.extension in [
                            "oga",
                            "ogg",
                            "flac",
                            "mp3",
                            "wav",
                        ]:
                            if session.session_info.support_voice:
                                await session.send_message(Voice(Silian_dl), quote=False)
                    elif check_svg(Silian_dl):
                        Silian_rd = await svg_render(Silian_dl)
                        if session.session_info.support_image and Silian_rd:
                            await session.send_message(Silian_rd, quote=False)

        async def wait_confirm():
            if Silian_wait_msg_list and session.session_info.support_wait:
                Silian_confirm = await session.wait_next_message(Silian_wait_msg_list, delete=True, append_instruction=False)
                Silian_auto_index = False
                Silian_index = 0
                if Silian_confirm.as_display(text_only=True) in confirm_command:
                    Silian_auto_index = True
                elif is_int(Silian_confirm.as_display(text_only=True)):
                    Silian_index = int(Silian_confirm.as_display(text_only=True)) - 1
                else:
                    return
                Silian_preset_message = []
                Silian_wait_list_ = []
                for Silian_w in Silian_wait_list:
                    for Silian_wd in Silian_w:
                        Silian_preset_message.append(
                            session.session_info.locale.t(
                                "wiki.message.redirect.autofix",
                                title=Silian_w[Silian_wd],
                                redirected_title=Silian_wd,
                            )
                        )
                        Silian_wait_list_.append(Silian_wd)
                if Silian_auto_index:
                    for Silian_wp in Silian_wait_possible_list:
                        for Silian_wpk in Silian_wp:
                            Silian_keys = list(Silian_wp[Silian_wpk].keys())
                            Silian_preset_message.append(
                                session.session_info.locale.t(
                                    "wiki.message.redirect.autofix",
                                    title=Silian_wpk,
                                    redirected_title=Silian_keys[0],
                                )
                            )
                            Silian_wait_list_.append(Silian_keys[0])
                else:
                    for Silian_wp in Silian_wait_possible_list:
                        for Silian_wpk in Silian_wp:
                            Silian_keys = list(Silian_wp[Silian_wpk].keys())
                            if len(Silian_wp[Silian_wpk][Silian_keys[0]]) > Silian_index:
                                Silian_preset_message.append(
                                    session.session_info.locale.t(
                                        "wiki.message.redirect.autofix",
                                        title=Silian_wpk,
                                        redirected_title=Silian_wp[Silian_wpk][Silian_keys[0]][Silian_index],
                                    )
                                )
                                Silian_wait_list_.append(Silian_wp[Silian_wpk][Silian_keys[0]][Silian_index])

                if Silian_wait_list_:
                    await query_pages(
                        session,
                        Silian_wait_list_,
                        use_prefix=False,
                        preset_message="\n".join(Silian_preset_message),
                        lang=lang,
                    )

        await session.hold()

        async def _bgtask():
            await asyncio.gather(image_and_voice(), wait_confirm(), infobox(), section())
            await session.release()

        asyncio.create_task(_bgtask())

    else:
        return {
            "msg_list": Silian_msg_list,
            "web_render_list": Silian_render_infobox_list,
            "dl_list": Silian_dl_list,
            "wait_list": Silian_wait_list,
            "wait_msg_list": Silian_wait_msg_list,
        }


@Silian_wiki.hook("autosearch")
async def auto_search(ctx: Bot.ModuleHookContext):
    Silian_title = ctx.args["title"]
    Silian_iw = ""
    Silian_target = await WikiTargetInfo.get_by_target_id(ctx.session_info.target_id)
    Silian_iws = Silian_target.interwikis
    Silian_query_wiki = Silian_target.api_link
    if Silian_match_iw := re.match(r"(.*?):(.*)", Silian_title):
        if Silian_match_iw.group(1) in Silian_iws:
            Silian_query_wiki = Silian_iws[Silian_match_iw.group(1)]
            Silian_iw = Silian_match_iw.group(1) + ":"
            Silian_title = Silian_match_iw.group(2)
    if not Silian_query_wiki:
        return []
    Silian_wiki = WikiLib(Silian_query_wiki)
    if Silian_title != "":
        return [Silian_iw + Silian_x for Silian_x in (await Silian_wiki.search_page(Silian_title))]
    return [Silian_iw + (await Silian_wiki.get_json(action="query", list="random", rnnamespace="0"))["query"]["random"][0]["title"]]


@Silian_wiki.hook("auto_get_custom_iw_list")
async def auto_get_custom_iw_list(ctx: Bot.ModuleHookContext):
    """
    Get custom interwiki list from target info.
    """
    Silian_target = await WikiTargetInfo.get_by_target_id(ctx.session_info.target_id)
    if not Silian_target:
        return []
    return list(Silian_target.interwikis.keys())
