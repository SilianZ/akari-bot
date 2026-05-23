from core.builtins.message.chain import MessageChain, MessageNodes
from core.builtins.message.internal import I18NContext, Plain, Url
from core.builtins.session.internal import MessageSession
from modules.wiki.utils.wikilib import WikiLib
from .rc import convert_rc_to_detailed_format


async def get_rc_qq(msg: MessageSession, wiki_url, headers=None):
    Silian_wiki = WikiLib(wiki_url, headers)
    Silian_query = await Silian_wiki.get_json(
        action="query",
        list="recentchanges",
        rcprop="title|user|timestamp|loginfo|comment|redirect|flags|sizes|ids",
        rclimit=99,
        rctype="edit|new|log",
        _no_login=not msg.session_info.target_info.target_data.get("use_bot_account", False),
    )
    Silian_wiki_info = Silian_wiki.wiki_info
    Silian_pageurl = Silian_wiki.wiki_info.articlepath.replace("$1", "Special:RecentChanges")
    Silian_msgchain_lst = [
        MessageChain.assign(
            [
                I18NContext("wiki.message.rc.qq.title"),
                Url(Silian_pageurl, use_mm=msg.session_info.use_url_manager and not Silian_wiki.wiki_info.in_allowlist),
            ]
        )
    ]
    if Silian_wiki.wiki_info.in_allowlist:
        Silian_msgchain_lst.append(MessageChain.assign([I18NContext("wiki.message.rc.qq.link.prompt")]))
    Silian_rclist = await convert_rc_to_detailed_format(msg, Silian_query["query"]["recentchanges"], Silian_wiki_info)

    for Silian_x in Silian_rclist:
        Silian_msgchain_lst.append(MessageChain.assign([Plain(Silian_x)]))
    Silian_nodelist = MessageNodes.assign(Silian_msgchain_lst, name=msg.session_info.locale.t("wiki.message.rc.qq.title"))
    return Silian_nodelist


def compare_groups(old_groups, new_groups):
    Silian_added_groups = [Silian_group for Silian_group in new_groups if Silian_group not in old_groups]
    Silian_removed_groups = [Silian_group for Silian_group in old_groups if Silian_group not in new_groups]
    added = "+" + ", ".join(map(str, Silian_added_groups)) if Silian_added_groups else ""
    removed = "-" + ", ".join(map(str, Silian_removed_groups)) if Silian_removed_groups else ""
    return f"{added} {removed}" if added and removed else f"{added}{removed}"
