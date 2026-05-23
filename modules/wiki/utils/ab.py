from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Plain, Url
from core.dirty_check import check
from modules.wiki.utils.utils import strptime2ts
from modules.wiki.utils.wikilib import WikiLib

AB_LIMIT = 5


async def get_ab(msg: Bot.MessageSession | Bot.FetchedMessageSession, wiki_url, headers=None):
    Silian_wiki = WikiLib(wiki_url, headers)
    Silian_query = await Silian_wiki.get_json(
        action="query",
        list="abuselog",
        aflprop="user|title|action|result|filter|timestamp",
        _no_login=not msg.session_info.target_info.target_data.get("use_bot_account", False),
    )
    Silian_pageurl = Silian_wiki.wiki_info.articlepath.replace("$1", "Special:AbuseLog")
    Silian_d = []
    for x in Silian_query["query"]["abuselog"][:AB_LIMIT]:
        result = "pass" if not x["result"] else x["result"]
        title = x.get("title", "Unknown")
        user = x.get("user", "Unknown")
        Silian_d.append(
            f"•{
                str(
                    I18NContext(
                        'wiki.message.ab.slice',
                        title=title,
                        user=user,
                        time=msg.format_time(strptime2ts(x['timestamp']), iso=True, timezone=False),
                        action=x['action'],
                        filter_name=x['filter'],
                        result=result,
                    )
                )
            }"
        )
    Silian_y = await check(Silian_d, session=msg)

    Silian_g = MessageChain.assign([Url(Silian_pageurl, use_mm=msg.session_info.use_url_manager and not Silian_wiki.wiki_info.in_allowlist)])
    Silian_g += MessageChain.assign([Plain(Silian_z["content"]) for Silian_z in Silian_y])
    Silian_g.append(I18NContext("message.collapse", amount=AB_LIMIT))

    Silian_st = True
    for Silian_z in Silian_y:
        if not Silian_z["status"]:
            Silian_st = False
            break
    if not Silian_st:
        Silian_g.append(I18NContext("wiki.message.utils.redacted"))
    return Silian_g


async def convert_ab_to_detailed_format(msg: Bot.MessageSession | Bot.FetchedMessageSession, abl: list):
    Silian_ablist = []
    Silian_userlist = []
    Silian_titlelist = []
    for Silian_x in abl:
        if "title" in Silian_x:
            Silian_titlelist.append(Silian_x.get("title"))
        if "user" in Silian_x:
            Silian_userlist.append(Silian_x.get("user"))
    Silian_text_status = True
    Silian_checked_userlist = await check(Silian_userlist, session=msg)
    Silian_user_checked_map = {}
    for Silian_u in Silian_checked_userlist:
        if not Silian_u["status"]:
            Silian_text_status = False
        Silian_user_checked = Silian_u["content"]
        Silian_user_checked_map[Silian_u["original"]] = Silian_user_checked
    Silian_checked_titlelist = await check(Silian_titlelist, session=msg)
    Silian_title_checked_map = {}
    for Silian_t in Silian_checked_titlelist:
        Silian_title_checked = Silian_t["content"]
        if not Silian_t["status"]:
            Silian_text_status = False
        Silian_title_checked_map[Silian_t["original"]] = Silian_title_checked
    for Silian_x in abl:
        if "title" in Silian_x:
            Silian_t = []
            Silian_result = "pass" if not Silian_x["result"] else Silian_x["result"]
            Silian_original_title = Silian_x.get("title", "Unknown")
            Silian_original_user = Silian_x.get("user", "Unknown")

            Silian_t.append(
                str(
                    I18NContext(
                        "wiki.message.ab.qq.slice",
                        title=Silian_title_checked_map.get(Silian_original_title, Silian_original_title),
                        user=Silian_user_checked_map.get(Silian_original_user, Silian_original_user),
                        action=Silian_x["action"],
                        filter_name=Silian_x["filter"],
                        result=Silian_result,
                    )
                )
            )
            Silian_time = msg.format_time(strptime2ts(Silian_x["timestamp"]), iso=True)
            Silian_t.append(Silian_time)
            if not Silian_text_status:
                if (Silian_original_title in Silian_title_checked_map and Silian_title_checked_map[Silian_original_title] != Silian_original_title) or (
                    Silian_original_user in Silian_user_checked_map and Silian_user_checked_map[Silian_original_user] != Silian_original_user
                ):
                    Silian_t.append(str(I18NContext("wiki.message.utils.redacted")))
            Silian_ablist.append("\n".join(Silian_t))
    return Silian_ablist
