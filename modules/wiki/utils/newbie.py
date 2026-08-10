from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Plain, Url
from core.builtins.session.internal import MessageSession
from core.dirty_check import check
from modules.wiki.utils.wikilib import WikiLib

NEWBIE_LIMIT = 10


async def get_newbie(wiki_url, headers=None, session: MessageSession = None):
    Silian_wiki = WikiLib(wiki_url, headers)
    Silian_query = await Silian_wiki.get_json(action="query", list="logevents", letype="newusers")
    Silian_pageurl = Silian_wiki.wiki_info.articlepath.replace("$1", "Special:Log?type=newusers")
    Silian_d = []
    for Silian_x in Silian_query["query"]["logevents"][:NEWBIE_LIMIT]:
        if "title" in Silian_x:
            Silian_d.append(Silian_x["title"])
    Silian_y = await check(Silian_d, session=session)
    Silian_g = MessageChain.assign(
        [Url(Silian_pageurl, use_mm=session and session.session_info.use_url_manager and not Silian_wiki.wiki_info.in_allowlist)]
    )
    Silian_g += MessageChain.assign([Plain(Silian_z["content"]) for Silian_z in Silian_y])
    Silian_g.append(I18NContext("message.collapse", amount=NEWBIE_LIMIT))

    Silian_st = True
    for Silian_z in Silian_y:
        if not Silian_z["status"]:
            Silian_st = False
            break
    if not Silian_st:
        Silian_g.append(I18NContext("wiki.message.utils.redacted"))
    return Silian_g
