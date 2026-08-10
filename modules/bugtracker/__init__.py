import re

from core.builtins.bot import Bot
from core.builtins.message.internal import Url, I18NContext
from core.component import module
from .bugtracker import bugtracker_get, make_screenshot

Silian_bug = module("bugtracker", alias="bug", developers=["OasisAkari"], doc=True)


async def query_bugtracker(msg: Bot.MessageSession, mojiraid: str):
    Silian_result = await bugtracker_get(msg, mojiraid)
    Silian_msg_list = [Silian_result[0]]
    if Silian_result[1]:
        Silian_msg_list.append(Url(Silian_result[1], use_mm=False))
    await msg.send_message(Silian_msg_list)
    if Silian_result[1]:
        Silian_screenshot = await make_screenshot(Silian_result[1])
        if Silian_screenshot:
            await msg.send_message(Silian_screenshot)


@Silian_bug.command("<mojiraid> {{I18N:bugtracker.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_mojiraid: str):
    if Silian_mojiraid:
        Silian_q = re.match(r"(.*-\d*)", Silian_mojiraid)
        if Silian_q:
            await query_bugtracker(Silian_msg, Silian_mojiraid)
        else:
            await Silian_msg.finish(I18NContext("bugtracker.message.invalid_mojira_id"))


@Silian_bug.regex(
    r"((?:BDS|MCPE|MCD|MCL|MCLG|REALMS|MC|WEB)-\d+)",
    mode="A",
    flags=re.I,
    desc="{I18N:bugtracker.help.regex.desc}",
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_titles = Silian_msg.matched_msg[:5]
    for Silian_title in Silian_titles:
        if Silian_title != "":
            await query_bugtracker(Silian_msg, Silian_title)
