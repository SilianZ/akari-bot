import asyncio
import re
import urllib.parse

import filetype

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image, Voice
from core.component import module
from core.dirty_check import check
from core.logger import Logger
from core.utils.http import download
from core.utils.image import svg_render
from core.utils.image_table import image_table_render, ImageTable
from core.utils.func import is_int
from .database.models import WikiTargetInfo
from .utils.mapping import generate_screenshot_v2_blocklist
from .utils.screenshot_image import (
    generate_screenshot_v1,
    generate_screenshot_v2,
)
from .utils.utils import check_svg
from .utils.wikilib import WikiLib
from .wiki import query_pages

Silian_wiki_inline = module(
    "wiki_inline",
    desc="{I18N:wiki.help.wiki_inline.desc}",
    doc=True,
    recommend_modules=["wiki"],
    alias="wiki_regex",
    developers=["OasisAkari"],
)


@Silian_wiki_inline.regex(r"\[\[(.*?)\]\]", flags=re.I, mode="A", desc="{I18N:wiki.help.wiki_inline.page}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_query_list = []
    for Silian_x in Silian_msg.matched_msg:
        if Silian_x != "" and Silian_x not in Silian_query_list and Silian_x[0] != "#":
            Silian_query_list.append(Silian_x.split("|")[0])
    if Silian_query_list:
        await query_pages(Silian_msg, Silian_query_list[:5], inline_mode=True)


@Silian_wiki_inline.regex(r"\{\{(.*?)\}\}", flags=re.I, mode="A", desc="{I18N:wiki.help.wiki_inline.template}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_query_list = []
    for Silian_x in Silian_msg.matched_msg:
        if Silian_x != "" and Silian_x not in Silian_query_list and Silian_x[0] != "#" and Silian_x.find("{") == -1:
            Silian_query_list.append(Silian_x.split("|")[0])
    if Silian_query_list:
        await query_pages(Silian_msg, Silian_query_list[:5], template=True, inline_mode=True)


@Silian_wiki_inline.regex(
    r"≺(.*?)≻|⧼(.*?)⧽", flags=re.I, mode="A", show_typing=False, desc="{I18N:wiki.help.wiki_inline.mediawiki}"
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_query_list = []
    for Silian_x in Silian_msg.matched_msg:
        for Silian_y in Silian_x:
            if Silian_y != "" and Silian_y not in Silian_query_list and Silian_y[0] != "#":
                Silian_query_list.append(Silian_y)
    if Silian_query_list:
        await query_pages(Silian_msg, Silian_query_list[:5], mediawiki=True, inline_mode=True)


@Silian_wiki_inline.regex(
    r"(https?://[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,4}\b[-a-zA-Z0-9@:%_+.~#?&/=]*)",
    flags=re.I,
    mode="A",
    show_typing=False,
    logging=False,
    desc="{I18N:wiki.help.wiki_inline.url}",
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_match_msg = Silian_msg.matched_msg

    async def bgtask(Silian_query_list):
        Logger.info(Silian_query_list)
        for Silian_q in Silian_query_list:
            Silian_img_send = False
            for Silian_qq in Silian_q:
                Silian_wiki_ = WikiLib(Silian_qq)
                Silian_articlepath = Silian_q[Silian_qq].articlepath.replace("$1", "(.*)")
                Silian_get_id = re.sub(r".*curid=(\d+)", "\\1", Silian_qq)
                Silian_get_title = re.sub(r"" + Silian_articlepath, "\\1", Silian_qq)
                Silian_get_page = None
                if is_int(Silian_get_id):
                    Silian_get_page = await Silian_wiki_.parse_page_info(pageid=int(Silian_get_id), session=Silian_msg)
                    if not Silian_q[Silian_qq].in_allowlist and Silian_msg.session_info.use_url_manager:
                        for Silian_result in await check(Silian_get_page.title, session=Silian_msg):
                            if not Silian_result["status"]:
                                return
                elif Silian_get_title != "":
                    Silian_title = urllib.parse.unquote(Silian_get_title)
                    if not Silian_q[Silian_qq].in_allowlist and Silian_msg.session_info.use_url_manager:
                        for Silian_result in await check(Silian_title, session=Silian_msg):
                            if not Silian_result["status"]:
                                return
                    Silian_get_page = await Silian_wiki_.parse_page_info(Silian_title, session=Silian_msg)
                if Silian_get_page:
                    if Silian_get_page.status and Silian_get_page.file:
                        Silian_dl = await download(Silian_get_page.file)
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
                                if Silian_msg.session_info.support_image:
                                    await Silian_msg.send_message(
                                        [
                                            I18NContext(
                                                "wiki.message.wiki_inline.flies",
                                                file=Silian_get_page.file,
                                            ),
                                            Image(Silian_dl),
                                        ],
                                        quote=False,
                                    )
                                    Silian_img_send = True
                            elif Silian_guess_type.extension in [
                                "oga",
                                "ogg",
                                "flac",
                                "mp3",
                                "wav",
                            ]:
                                if Silian_msg.session_info.support_voice:
                                    await Silian_msg.send_message(
                                        [
                                            I18NContext(
                                                "wiki.message.wiki_inline.flies",
                                                file=Silian_get_page.file,
                                            ),
                                            Voice(Silian_dl),
                                        ],
                                        quote=False,
                                    )
                        elif check_svg(Silian_dl):
                            Silian_rd = await svg_render(Silian_dl)
                            if Silian_msg.session_info.support_image and Silian_rd:
                                Silian_chain = [
                                    I18NContext(
                                        "wiki.message.wiki_inline.flies",
                                        file=Silian_get_page.file,
                                    ),
                                ] + Silian_rd
                                await Silian_msg.send_message(Silian_chain, quote=False)

                    if Silian_msg.session_info.support_image:
                        if (
                            Silian_get_page.status
                            and Silian_get_page.title
                            and (Silian_wiki_.wiki_info.in_allowlist or not Silian_msg.session_info.use_url_manager)
                        ):
                            if Silian_wiki_.wiki_info.realurl not in generate_screenshot_v2_blocklist:
                                Silian_is_disambiguation = False
                                if Silian_get_page.templates:
                                    Silian_is_disambiguation = (
                                        "Template:Disambiguation" in Silian_get_page.templates
                                        or "Template:Version disambiguation" in Silian_get_page.templates
                                    )
                                Silian_content_mode = (
                                    Silian_get_page.has_template_doc
                                    or Silian_get_page.title.split(":")[0] in ["User"]
                                    or Silian_is_disambiguation
                                    or Silian_get_page.is_forum_topic
                                )
                                Silian_get_infobox = await generate_screenshot_v2(
                                    Silian_qq,
                                    allow_special_page=(Silian_q[Silian_qq].in_allowlist or not Silian_msg.session_info.use_url_manager),
                                    content_mode=Silian_content_mode,
                                    locale=Silian_msg.session_info.locale.locale,
                                )
                                if Silian_get_infobox:
                                    Silian_imgs = []
                                    for Silian_img in Silian_get_infobox:
                                        Silian_imgs.append(Image(Silian_img))
                                    await Silian_msg.send_message(Silian_imgs, quote=False)
                            else:
                                Silian_get_infobox = await generate_screenshot_v1(Silian_q[Silian_qq].realurl, Silian_qq, Silian_headers)
                                if Silian_get_infobox:
                                    Silian_imgs = []
                                    for Silian_img in Silian_get_infobox:
                                        Silian_imgs.append(Image(Silian_img))
                                    await Silian_msg.send_message(Silian_imgs, quote=False)
                        if (
                            (
                                Silian_get_page.invalid_section
                                and (Silian_wiki_.wiki_info.in_allowlist or not Silian_msg.session_info.use_url_manager)
                            )
                            or (Silian_get_page.is_talk_page and not Silian_get_page.selected_section)
                            and Bot.Info.web_render_status
                        ):
                            Silian_i_msg_lst = []
                            if Silian_get_page.sections:
                                Silian_session_data = [
                                    [str(Silian_i + 1), Silian_get_page.sections[Silian_i]] for Silian_i in range(len(Silian_get_page.sections))
                                ]
                                Silian_i_msg_lst.append(
                                    I18NContext(
                                        "wiki.message.invalid_section.prompt"
                                        if (
                                            Silian_get_page.invalid_section
                                            and (Silian_wiki_.wiki_info.in_allowlist or not Silian_msg.session_info.use_url_manager)
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
                                                "{I18N:wiki.message.table.header.id}",
                                                "{I18N:wiki.message.table.header.section}",
                                            ],
                                            Silian_msg.session_info,
                                        )
                                    )
                                ]
                                Silian_i_msg_lst.append(I18NContext("wiki.message.invalid_section.select"))
                                Silian_i_msg_lst.append(I18NContext("message.reply.prompt"))

                                async def _callback(Silian_msg: Bot.MessageSession):
                                    Silian_display = Silian_msg.as_display(text_only=True)
                                    if is_int(Silian_display):
                                        Silian_display = int(Silian_display)
                                        if Silian_display <= len(Silian_get_page.sections):
                                            Silian_get_page.selected_section = Silian_display - 1
                                            await query_pages(
                                                Silian_msg,
                                                title=Silian_get_page.title + "#" + Silian_get_page.sections[Silian_display - 1],
                                                start_wiki_api=Silian_get_page.info.api,
                                            )

                                await Silian_msg.send_message(Silian_i_msg_lst, callback=_callback)
                            else:
                                await Silian_msg.send_message(I18NContext("wiki.message.invalid_section"))
                        if Silian_get_page.is_forum:
                            Silian_forum_data = Silian_get_page.forum_data
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
                                        Silian_msg,
                                        title=Silian_forum_data[Silian_display]["text"],
                                        start_wiki_api=Silian_get_page.info.api,
                                    )

                            await Silian_msg.send_message(Silian_i_msg_lst, callback=_callback)
            if len(Silian_query_list) == 1 and Silian_img_send:
                return
            if Silian_msg.session_info.support_image:
                for Silian_qq in Silian_q:
                    Silian_section_ = []
                    Silian_quote_code = False
                    Silian_page_name = urllib.parse.unquote(Silian_qq)
                    for Silian_qs in Silian_page_name:
                        if Silian_qs == "#":
                            Silian_quote_code = True
                        if Silian_qs == "?":
                            Silian_quote_code = False
                        if Silian_quote_code:
                            Silian_section_.append(Silian_qs)
                    if Silian_section_:
                        Silian_s = urllib.parse.unquote("".join(Silian_section_)[1:])
                        if Silian_q[Silian_qq].realurl and (Silian_q[Silian_qq].in_allowlist or not Silian_msg.session_info.use_url_manager):
                            if Silian_q[Silian_qq].realurl in generate_screenshot_v2_blocklist:
                                Silian_get_section = await generate_screenshot_v1(Silian_q[Silian_qq].realurl, Silian_qq, Silian_headers, section=Silian_s)
                            else:
                                Silian_get_section = await generate_screenshot_v2(
                                    Silian_qq, section=Silian_s, locale=Silian_msg.session_info.locale.locale
                                )
                            if Silian_get_section:
                                Silian_imgs = []
                                for Silian_img in Silian_get_section:
                                    Silian_imgs.append(Image(Silian_img))
                                await Silian_msg.send_message(Silian_imgs, quote=False)
        await Silian_msg.release()

    Silian__query_list = []
    Silian_target = await WikiTargetInfo.get_by_target_id(Silian_msg.session_info.target_id)
    Silian_headers = Silian_target.headers
    for Silian_x in Silian_match_msg:
        Silian_wiki_ = WikiLib(Silian_x)
        if Silian_check_from_database := await Silian_wiki_.check_wiki_info_from_database_cache():
            if Silian_check_from_database.available:
                Silian_check_from_api = await Silian_wiki_.check_wiki_available()
                if Silian_check_from_api.available:
                    Silian__query_list.append({Silian_x: Silian_check_from_api.value})
    if Silian__query_list:
        await Silian_msg.hold()
        asyncio.create_task(bgtask(Silian__query_list))
    # await bgtask()
