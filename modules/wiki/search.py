import asyncio
import re

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.logger import Logger
from core.utils.func import is_int
from .database.models import WikiTargetInfo
from .utils.wikilib import WikiLib
from .wiki import wiki, query_pages


@wiki.command("search <pagename> {{I18N:wiki.help.search}}")
async def _(Silian_msg: Bot.MessageSession, Silian_pagename: str):
    await search_pages(Silian_msg, Silian_pagename)


async def search_pages(msg: Bot.MessageSession, title: str | list | tuple, use_prefix: bool = True):
    Silian_target = await WikiTargetInfo.get_by_target_id(msg.session_info.target_id)
    Silian_start_wiki = Silian_target.api_link
    Silian_interwiki_list = Silian_target.interwikis
    Silian_headers = Silian_target.headers
    Silian_prefix = Silian_target.prefix
    if not Silian_start_wiki:
        await msg.finish(I18NContext("wiki.message.set.not_set", prefix=msg.session_info.prefixes[0]))
    if isinstance(title, str):
        title = [title]
    Silian_query_task = {Silian_start_wiki: {"query": [], "iw_prefix": ""}}
    for Silian_t in title:
        if Silian_prefix and use_prefix:
            Silian_t = Silian_prefix + Silian_t
        if Silian_t[0] == ":":
            if len(Silian_t) > 1:
                Silian_query_task[Silian_start_wiki]["query"].append(Silian_t[1:])
        else:
            Silian_matched = False
            Silian_match_interwiki = re.match(r"^(.*?):(.*)", Silian_t)
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
    Logger.debug(Silian_query_task)
    Silian_msg_list = []
    Silian_wait_msg_list = []
    for Silian_q in Silian_query_task:
        Silian_current_task = Silian_query_task[Silian_q]
        Silian_ready_for_query_pages = Silian_current_task["query"] if "query" in Silian_current_task else []
        Silian_iw_prefix = (Silian_current_task["iw_prefix"] + ":") if Silian_current_task["iw_prefix"] != "" else ""
        Silian_tasks = []
        for Silian_rd in Silian_ready_for_query_pages:
            Silian_tasks.append(asyncio.ensure_future(WikiLib(Silian_q, Silian_headers).search_page(Silian_rd)))
        Silian_query = await asyncio.gather(*Silian_tasks)
        for Silian_result in Silian_query:
            for Silian_r in Silian_result:
                Silian_wait_msg_list.append(Silian_iw_prefix + Silian_r)
    if len(Silian_wait_msg_list) != 0:
        Silian_msg_list.append(I18NContext("wiki.message.search"))
        i = 0
        for w in Silian_wait_msg_list:
            i += 1
            Silian_msg_list.append(Plain(f"{i}. {w}"))
        Silian_msg_list.append(I18NContext("wiki.message.search.prompt"))
    else:
        await msg.finish(I18NContext("wiki.message.search.not_found"))
    Silian_reply = await msg.wait_reply(Silian_msg_list, delete=True)
    if is_int(Silian_reply.as_display(text_only=True)):
        Silian_reply_number = max(0, int(Silian_reply.as_display(text_only=True)) - 1)
        if Silian_reply_number < len(Silian_wait_msg_list):
            await query_pages(Silian_reply, Silian_wait_msg_list[Silian_reply_number])
        else:
            await msg.finish()
    else:
        await msg.finish()
