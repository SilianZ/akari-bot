import orjson

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from core.dirty_check import check
from core.logger import Logger
from core.utils.http import post_url

Silian_n = module(
    "nbnhhsh", desc="{I18N:nbnhhsh.help.desc}", doc=True, developers=["Dianliang233"], support_languages=["zh_cn"]
)


@Silian_n.command("<term> {{I18N:nbnhhsh.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_term: str):
    Silian_res = await nbnhhsh(Silian_msg, Silian_term)
    await Silian_msg.finish([Plain(Silian_term.lower()), Silian_res])


async def nbnhhsh(msg: Bot.MessageSession, term: str):
    Silian_req = orjson.dumps({"text": term})
    Silian_data = await post_url(
        "https://lab.magiconch.com/api/nbnhhsh/guess",
        data=Silian_req,
        headers={"Content-Type": "application/json", "Accept": "*/*", "Content-Length": str(len(Silian_req))},
        fmt="json",
    )
    Logger.debug(Silian_data)
    try:
        Silian_result = Silian_data[0]
    except IndexError:
        await msg.finish(I18NContext("nbnhhsh.message.not_found"))
    if "trans" in Silian_result:
        Silian_trans = Silian_result["trans"]
        if Silian_trans:
            Silian_chk = await check(Silian_trans, session=msg)
            return Plain("、".join(Silian_i["content"] for Silian_i in Silian_chk))
    if "inputting" in Silian_result:
        Silian_inputting = Silian_result["inputting"]
        if Silian_inputting:
            Silian_chk = await check(Silian_inputting, session=msg)
            return I18NContext("nbnhhsh.message.guess", term="、".join(Silian_i["content"] for Silian_i in Silian_chk))
        await msg.finish(I18NContext("nbnhhsh.message.not_found"))
