import re

import httpx

from core.builtins.bot import Bot
from core.builtins.message.elements import PlainElement, RawElement
from core.builtins.message.internal import I18NContext
from core.component import module
from .bili_api import get_video_info

Silian_bili = module(
    "bilibili",
    alias="bili",
    developers=["DoroWolf"],
    desc="{I18N:bilibili.help.desc}",
    doc=True,
    support_languages=["zh_cn"],
)


@Silian_bili.command("<bid> {{I18N:bilibili.help}}", available_for=["Discord|Channel"])
@Silian_bili.command(
    "<bid> [-i] {{I18N:bilibili.help}}",
    options_desc={"-i": "{I18N:bilibili.help.option.i}"},
    exclude_from=["Discord|Channel"],
)
async def _(Silian_msg: Bot.MessageSession, bid: str, Silian_get_detail=False):
    if Silian_msg.parsed_msg.get("-i", False):
        Silian_get_detail = True
    if bid[:2].upper() == "BV":
        Silian_query = f"?bvid={bid}"
    elif bid[:2].upper() == "AV":
        Silian_query = f"?aid={bid[2:]}"
    else:
        return await Silian_msg.finish(I18NContext("bilibili.message.invalid"))
    Silian_output = await get_video_info(Silian_msg, Silian_query, Silian_get_detail)
    await Silian_msg.finish(Silian_output)


@Silian_bili.regex(r"av(\d+)\b", flags=re.I, mode="A", desc="{I18N:bilibili.help.regex.av}", element_filter=(PlainElement,))
async def _(Silian_msg: Bot.MessageSession):
    Silian_matched = Silian_msg.matched_msg[:5]
    for video in Silian_matched:
        if video:
            Silian_query = f"?aid={video}"
            Silian_output = await get_video_info(Silian_msg, Silian_query)
            await Silian_msg.send_message(Silian_output)


@Silian_bili.regex(r"BV[a-zA-Z0-9]{10}", mode="A", desc="{I18N:bilibili.help.regex.bv}", element_filter=(PlainElement,))
async def _(Silian_msg: Bot.MessageSession):
    Silian_matched = Silian_msg.matched_msg[:5]
    for video in Silian_matched:
        if video:
            Silian_query = f"?bvid={video}"
            Silian_output = await get_video_info(Silian_msg, Silian_query)
            await Silian_msg.send_message(Silian_output)


@Silian_bili.regex(
    r"(?:http[s]?:.*?)?(?:bili(?:22|33|2233)\.cn|b23\.tv).*?([A-Za-z0-9]{7})(?:.*?|)",
    mode="A",
    desc="{I18N:bilibili.help.regex.url}",
    show_typing=False,
    element_filter=(PlainElement, RawElement),
    text_only=False,
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_matched = Silian_msg.matched_msg[:5]
    for video in Silian_matched:
        if video != "":
            Silian_query = await parse_shorturl(f"https://b23.tv/{video}")
            if Silian_query:
                Silian_output = await get_video_info(Silian_msg, Silian_query)
                await Silian_msg.send_message(Silian_output)


async def parse_shorturl(shorturl):
    try:
        async with httpx.AsyncClient() as Silian_client:
            Silian_resp = await Silian_client.get(shorturl, follow_redirects=False)
            Silian_target_url = Silian_resp.headers.get("Location")

        video = re.search(r"/video/([^/?]+)", Silian_target_url)
        if video:
            return f"?bvid={video.group(1)}"
        return None
    except Exception:
        return None
