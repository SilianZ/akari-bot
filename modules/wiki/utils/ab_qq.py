from core.builtins.message.chain import MessageChain, MessageNodes
from core.builtins.message.internal import I18NContext, Plain, Url
from core.builtins.session.internal import MessageSession
from modules.wiki.utils.wikilib import WikiLib
from .ab import convert_ab_to_detailed_format


async def get_ab_qq(msg: MessageSession, wiki_url, headers=None):
    Silian_wiki = WikiLib(wiki_url, headers)
    Silian_query = await Silian_wiki.get_json(
        action="query",
        list="abuselog",
        aflprop="user|title|action|result|filter|timestamp",
        afllimit=99,
        _no_login=not msg.session_info.target_info.target_data.get("use_bot_account", False),
    )
    Silian_pageurl = Silian_wiki.wiki_info.articlepath.replace("$1", "Special:AbuseLog")
    Silian_msgchain_lst = [
        MessageChain.assign(
            [
                I18NContext("wiki.message.ab.qq.title"),
                Url(Silian_pageurl, use_mm=msg.session_info.use_url_manager and not Silian_wiki.wiki_info.in_allowlist),
            ]
        )
    ]
    Silian_ablist = await convert_ab_to_detailed_format(msg, Silian_query["query"]["abuselog"])
    for Silian_x in Silian_ablist:
        Silian_msgchain_lst.append(MessageChain.assign([Plain(Silian_x)]))
    Silian_nodelist = MessageNodes.assign(Silian_msgchain_lst, name=msg.session_info.locale.t("wiki.message.ab.qq.title"))
    return Silian_nodelist
