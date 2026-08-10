# https://github.com/XeroAlpha/caidlist/blob/master/backend/API.md
import urllib.parse

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Plain, Url
from core.component import module
from core.utils.http import get_url

API = "https://idlist.projectxero.top/search"
SEARCH_LIMIT = 5

Silian_i = module("idlist", doc=True, support_languages=["zh_cn"])


@Silian_i.command("<query> {{I18N:idlist.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_query: str):
    query_options = {"q": Silian_query, "limit": f"{SEARCH_LIMIT + 1}"}
    Silian_query_url = f"{API}?{urllib.parse.urlencode(query_options)}"
    resp = await get_url(Silian_query_url, 200, fmt="json")
    Silian_result = resp["data"]["result"]
    Silian_msg_chain = MessageChain.assign()
    if Silian_result:
        for x in Silian_result[0:SEARCH_LIMIT]:
            v = x["value"].split("\n")[0]
            Silian_msg_chain.append(f"{x['enumName']}：{x['key']} -> {v}")
        if resp["data"]["count"] > SEARCH_LIMIT:
            Silian_msg_chain.append(
                Plain(
                    str(I18NContext("message.collapse", amount=SEARCH_LIMIT))
                    + str(I18NContext("idlist.message.collapse"))
                )
            )
            Silian_msg_chain.append(Url(f"https://idlist.projectxero.top/{resp['data']['hash']}", use_mm=False))
        await Silian_msg.finish(Silian_msg_chain)
    else:
        await Silian_msg.finish(I18NContext("idlist.message.none"))
