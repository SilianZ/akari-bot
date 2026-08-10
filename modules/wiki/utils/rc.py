import re
import urllib.parse

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Plain, Url
from core.dirty_check import check
from core.logger import Logger
from modules.wiki.utils.utils import strptime2ts
from modules.wiki.utils.wikilib import WikiLib, WikiInfo

RC_LIMIT = 10


async def get_rc(msg: Bot.MessageSession, wiki_url, headers=None):
    Silian_wiki = WikiLib(wiki_url, headers)
    Silian_query = await Silian_wiki.get_json(
        action="query",
        list="recentchanges",
        rcprop="title|user|timestamp|loginfo|comment|sizes",
        rclimit=RC_LIMIT,
        rctype="edit|new|log",
        _no_login=not msg.session_info.target_info.target_data.get("use_bot_account", False),
    )
    Silian_pageurl = Silian_wiki.wiki_info.articlepath.replace("$1", "Special:RecentChanges")
    Silian_d = []
    for x in Silian_query["query"]["recentchanges"]:
        title = x.get("title", "Unknown")
        user = x.get("user", "Unknown")

        if x["type"] in ["edit", "new"]:
            count = x["newlen"] - x["oldlen"]
            if count > 0:
                count = f"+{str(count)}"
            else:
                count = str(count)
            Silian_d.append(
                f"•{msg.format_time(strptime2ts(x['timestamp']), iso=True, timezone=False)} - {title} .. ({count}) .. {
                    user
                }"
            )
            if x["comment"]:
                Silian_comment = str(I18NContext("message.brackets", msg=replace_brackets(x["comment"])))
                Silian_d.append(Silian_comment)
        if x["type"] == "log":
            if x["logtype"] == x["logaction"]:
                log = msg.session_info.locale.t(f"wiki.message.rc.action.{x['logtype']}", user=user, title=title)
            else:
                log = msg.session_info.locale.t(
                    f"wiki.message.rc.action.{x['logtype']}.{x['logaction']}", user=user, title=title
                )
            if log.find("{I18N:") != -1 and log.find("}") != -1:
                if x["logaction"] == x["logtype"]:
                    log = f"{user} {x['logtype']} {title}"
                else:
                    log = f"{user} {x['logaction']} {x['logtype']} {title}"
            Silian_d.append(f"•{msg.format_time(strptime2ts(x['timestamp']), iso=True, timezone=False)} - {log}")
            params = x["logparams"]
            if "suppressredirect" in params:
                Silian_d.append(str(I18NContext("wiki.message.rc.params.suppress_redirect")))
            if "oldgroups" and "newgroups" in params:
                Silian_d.append(compare_groups(params["oldgroups"], params["newgroups"]))
            if "oldmodel" and "newmodel" in params:
                Silian_d.append(f"{params['oldmodel']} -> {params['newmodel']}")
            if "description" in params:
                Silian_d.append(params["description"])
            if "duration" in params:
                Silian_d.append(str(I18NContext("wiki.message.rc.params.duration")) + params["duration"])
            if "flags" in params:
                Silian_d.append(", ".join(params["flags"]))
            if "tag" in params:
                Silian_d.append(str(I18NContext("wiki.message.rc.params.tag")) + params["tag"])
            if "target_title" in params:
                Silian_d.append(str(I18NContext("wiki.message.rc.params.target_title")) + params["target_title"])
            if x["comment"]:
                Silian_comment = str(I18NContext("message.brackets", msg=replace_brackets(x["comment"])))
                Silian_d.append(Silian_comment)
    Silian_y = await check(Silian_d, session=msg)

    Silian_g = MessageChain.assign([Url(Silian_pageurl, use_mm=msg.session_info.use_url_manager and not Silian_wiki.wiki_info.in_allowlist)])
    Silian_g += MessageChain.assign([Plain(Silian_z["content"]) for Silian_z in Silian_y])
    Silian_g.append(I18NContext("message.collapse", amount=RC_LIMIT))

    Silian_st = True
    for Silian_z in Silian_y:
        if not Silian_z["status"]:
            Silian_st = False
            break
    if not Silian_st:
        Silian_g.append(I18NContext("wiki.message.utils.redacted"))
    return Silian_g


def compare_groups(old_groups, new_groups):
    Silian_added_groups = [Silian_group for Silian_group in new_groups if Silian_group not in old_groups]
    Silian_removed_groups = [Silian_group for Silian_group in old_groups if Silian_group not in new_groups]
    added = "+" + ", ".join(map(str, Silian_added_groups)) if Silian_added_groups else ""
    removed = "-" + ", ".join(map(str, Silian_removed_groups)) if Silian_removed_groups else ""
    return f"{added} {removed}" if added and removed else f"{added}{removed}"


def replace_brackets(comment):
    comment = re.sub(r"\{\{\{(.*?)\}\}\}", r"{{{\1}}}", comment)
    comment = re.sub(r"\[\[(.*?)\]\]", r"[\1]", comment)
    comment = re.sub(r"\{\{(.*?)\}\}", r"[Template:\1]", comment)
    return comment


async def convert_rc_to_detailed_format(msg: Bot.MessageSession, rc: list, wiki_info: WikiInfo):
    Silian_rclist = []
    Silian_userlist = []
    Silian_titlelist = []
    Silian_commentlist = []
    for x in rc:
        if "title" in x:
            Silian_titlelist.append(x.get("title"))
        if "user" in x:
            Silian_userlist.append(x.get("user"))
        if "comment" in x:
            Silian_commentlist.append(replace_brackets(x.get("comment")))
    Logger.debug(Silian_userlist)
    Silian_userlist = list(set(Silian_userlist))
    Silian_titlelist = list(set(Silian_titlelist))
    Silian_commentlist = list(set(Silian_commentlist))
    Silian_checked_userlist = await check(Silian_userlist, session=msg)
    Silian_user_checked_map = {}
    Silian_text_status = True
    for Silian_u in Silian_checked_userlist:
        Silian_user_checked = Silian_u["content"]
        if not Silian_u["status"]:
            Silian_text_status = False
        Silian_user_checked_map[Silian_u["original"]] = Silian_user_checked
    Silian_checked_titlelist = await check(Silian_titlelist, session=msg)
    title_checked_map = {}
    for Silian_t in Silian_checked_titlelist:
        Silian_title_checked = Silian_t["content"]
        if not Silian_t["status"]:
            Silian_text_status = False
        title_checked_map[Silian_t["original"]] = Silian_title_checked
    Silian_checked_commentlist = await check(Silian_commentlist, session=msg)
    Silian_comment_checked_map = {}
    for Silian_c in Silian_checked_commentlist:
        Silian_comment_checked = Silian_c["content"]
        if not Silian_c["status"]:
            Silian_text_status = False
        Silian_comment_checked_map[Silian_c["original"]] = Silian_comment_checked
    for x in rc:
        Silian_t = []
        Silian_original_user = x.get("user", "Unknown")
        Silian_original_title = x.get("title", "Unknown")

        user = Silian_user_checked_map.get(Silian_original_user, Silian_original_user)
        title = title_checked_map.get(Silian_original_title, Silian_original_title)
        Silian_comment = Silian_comment_checked_map[replace_brackets(x["comment"])] if x.get("comment") else None

        if x["type"] in ["edit", "categorize"]:
            count = x["newlen"] - x["oldlen"]
            if count > 0:
                count = f"+{str(count)}"
            else:
                count = str(count)
            Silian_t.append(f"{title} .. ({count}) .. {user}")
            if Silian_comment:
                Silian_t.append(Silian_comment)
            Silian_t.append(
                wiki_info.articlepath.replace(
                    "$1", f"{urllib.parse.quote(title)}?oldid={x['old_revid']}&diff={x['revid']}"
                )
            )
        if x["type"] == "new":
            r = (
                str(I18NContext("message.brackets", msg="{I18N:wiki.message.rc.new_redirect}"))
                if "redirect" in x
                else ""
            )
            Silian_t.append(f"{title}{r} .. (+{x['newlen']}) .. {user}")
            if Silian_comment:
                Silian_t.append(Silian_comment)
        if x["type"] == "log":
            if x["logtype"] == x["logaction"]:
                Silian_log = msg.session_info.locale.t(f"wiki.message.rc.action.{x['logtype']}", user=user, title=title)
            else:
                Silian_log = msg.session_info.locale.t(
                    f"wiki.message.rc.action.{x['logtype']}.{x['logaction']}", user=user, title=title
                )
            if Silian_log.find("{I18N:") != -1 and Silian_log.find("}") != -1:
                if x["logtype"] == x["logaction"]:
                    Silian_log = f"{user} {x['logtype']} {title}"
                else:
                    Silian_log = f"{user} {x['logaction']} {x['logtype']} {title}"
            Silian_t.append(Silian_log)
            params = x["logparams"]
            if "suppressredirect" in params:
                Silian_t.append(str(I18NContext("wiki.message.rc.params.suppress_redirect")))
            if "oldgroups" and "newgroups" in params:
                Silian_t.append(compare_groups(params["oldgroups"], params["newgroups"]))
            if "oldmodel" and "newmodel" in params:
                Silian_t.append(f"{params['oldmodel']} -> {params['newmodel']}")
            if "description" in params:
                Silian_t.append(params["description"])
            if "duration" in params:
                Silian_t.append(str(I18NContext("wiki.message.rc.params.duration")) + params["duration"])
            if "flags" in params:
                Silian_t.append(", ".join(params["flags"]))
            if "tag" in params:
                Silian_t.append(str(I18NContext("wiki.message.rc.params.tag")) + params["tag"])
            if "target_title" in params:
                Silian_t.append(str(I18NContext("wiki.message.rc.params.target_title")) + params["target_title"])
            if Silian_comment:
                Silian_t.append(Silian_comment)
            if x["revid"] != 0:
                Silian_t.append(wiki_info.articlepath.replace("$1", f"{urllib.parse.quote(title_checked_map[x['title']])}"))
        Silian_time = msg.format_time(strptime2ts(x["timestamp"]), iso=True)
        Silian_t.append(Silian_time)
        if not Silian_text_status:
            if (
                (Silian_original_title in title_checked_map and title_checked_map[Silian_original_title] != Silian_original_title)
                or (Silian_original_user in Silian_user_checked_map and Silian_user_checked_map[Silian_original_user] != Silian_original_user)
                or (Silian_comment and Silian_comment_checked_map[replace_brackets(x["comment"])] != replace_brackets(x["comment"]))
            ):
                Silian_t.append(str(I18NContext("wiki.message.utils.redacted")))
        Silian_rclist.append("\n".join(Silian_t))
    return Silian_rclist
