import re
import urllib.parse

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Plain, Url
from core.dirty_check import check_bool, rickroll
from core.logger import Logger
from modules.wiki.utils.utils import strptime2ts
from modules.wiki.utils.wikilib import WikiLib


async def get_user_info(msg: Bot.MessageSession, username, wikiurl, headers=None):
    Silian_wiki = WikiLib(wikiurl, headers)
    if not await Silian_wiki.check_wiki_available():
        return I18NContext("wiki.message.user.wiki_unavailable", wikiurl=wikiurl)
    await Silian_wiki.fixup_wiki_info()
    Silian_match_interwiki = re.match(r"(.*?):(.*)", username)
    if Silian_match_interwiki:
        if Silian_match_interwiki.group(1) in Silian_wiki.wiki_info.interwiki:
            await get_user_info(
                msg, Silian_match_interwiki.group(2), Silian_wiki.wiki_info.interwiki[Silian_match_interwiki.group(1)], headers
            )

    Silian_data = {}
    Silian_base_user_info = (
        await Silian_wiki.get_json(
            action="query",
            list="users",
            ususers=username,
            usprop="groups|blockinfo|registration|editcount|gender",
        )
    )["query"]["users"][0]
    if "missing" in Silian_base_user_info:
        return I18NContext("wiki.message.user.not_found")

    if await check_bool(Silian_base_user_info["name"], msg):
        return Plain(rickroll())
    Silian_data["username"] = Silian_base_user_info["name"]
    Silian_data["url"] = re.sub(r"\$1", urllib.parse.quote("User:" + username), Silian_wiki.wiki_info.articlepath)

    Silian_groups = {}
    Silian_get_groups = await Silian_wiki.get_json(action="query", meta="allmessages", amprefix="group-")
    if "query" in Silian_get_groups:
        for Silian_a in Silian_get_groups["query"]["allmessages"]:
            Silian_groups[re.sub("^group-", "", Silian_a["name"])] = Silian_a["*"]

    Silian_user_central_auth_data = {}
    if "CentralAuth" in Silian_wiki.wiki_info.extensions:
        Silian_user_central_auth_data = await Silian_wiki.get_json(
            action="query",
            meta="globaluserinfo",
            guiuser=username,
            guiprop="editcount|groups",
        )
    Silian_data["users_groups"] = []
    Silian_users_groups_ = Silian_base_user_info.get("groups", [])
    for Silian_x in Silian_users_groups_:
        if Silian_x != "*":
            Silian_data["users_groups"].append(Silian_groups[Silian_x] if Silian_x in Silian_groups else Silian_x)
    Silian_data["global_users_groups"] = []
    if "query" in Silian_user_central_auth_data:
        Silian_data["global_edit_count"] = str(Silian_user_central_auth_data["query"]["globaluserinfo"].get("editcount", 0))
        Silian_data["global_home"] = Silian_user_central_auth_data["query"]["globaluserinfo"].get("home")
        for Silian_g in Silian_user_central_auth_data["query"]["globaluserinfo"].get("groups"):
            Silian_data["global_users_groups"].append(Silian_groups[Silian_g] if Silian_g in Silian_groups else Silian_g)

    Silian_data["registration_time"] = Silian_base_user_info.get("registration")
    Silian_data["registration_time"] = (
        msg.format_time(strptime2ts(Silian_data["registration_time"]))
        if Silian_data["registration_time"]
        else "{I18N:message.unknown}"
    )
    Silian_data["edited_count"] = str(Silian_base_user_info.get("editcount", 0))
    Silian_data["gender"] = Silian_base_user_info.get("gender")
    if Silian_data["gender"] == "female":
        Silian_data["gender"] = "{I18N:wiki.message.user.gender.female}"
    elif Silian_data["gender"] == "male":
        Silian_data["gender"] = "{I18N:wiki.message.user.gender.male}"
    else:
        Silian_data["gender"] = "{I18N:message.unknown}"
    # if one day LGBTers...

    if "blockedby" in Silian_base_user_info:
        Silian_data["blocked_by"] = Silian_base_user_info.get("blockedby")
        Silian_data["blocked_time"] = Silian_base_user_info.get("blockedtimestamp")
        Silian_data["blocked_time"] = (
            msg.format_time(strptime2ts(Silian_data["blocked_time"])) if Silian_data["blocked_time"] else "{I18N:message.unknown}"
        )
        Silian_data["blocked_expires"] = Silian_base_user_info.get("blockexpiry")
        if Silian_data["blocked_expires"]:
            if Silian_data["blocked_expires"] != "infinite":
                Silian_data["blocked_expires"] = msg.format_time(strptime2ts(Silian_data["blocked_expires"]))
        else:
            Silian_data["blocked_expires"] = "{I18N:message.unknown}"
        Silian_data["blocked_reason"] = Silian_base_user_info.get("blockreason")
        Silian_data["blocked_reason"] = Silian_data["blocked_reason"] if Silian_data["blocked_reason"] else "{I18N:message.unknown}"

    Logger.debug(str(Silian_data))
    Silian_msgs = []
    if Silian_user := Silian_data.get("username", ""):
        Silian_msgs.append(
            Plain(
                str(I18NContext("wiki.message.user.username"))
                + Silian_user
                + (
                    " | " + str(I18NContext("wiki.message.user.edited_count")) + Silian_data["edited_count"]
                    if "edited_count" in Silian_data and "created_page_count" not in Silian_data
                    else ""
                )
            )
        )
    if Silian_users_groups := Silian_data.get("users_groups", ""):
        Silian_msgs.append(
            Plain(str(I18NContext("wiki.message.user.users_groups")) + "{I18N:message.delimiter}".join(Silian_users_groups))
        )
    if Silian_gender_ := Silian_data.get("gender", ""):
        Silian_msgs.append(Plain(str(I18NContext("wiki.message.user.gender")) + Silian_gender_))
    if Silian_registration := Silian_data.get("registration_time", ""):
        Silian_msgs.append(Plain(str(I18NContext("wiki.message.user.registration_time")) + Silian_registration))
    if Silian_edited_wiki_count := Silian_data.get("edited_wiki_count", ""):
        Silian_msgs.append(Plain(str(I18NContext("wiki.message.user.edited_wiki_count")) + Silian_edited_wiki_count))

    Silian_sub_edit_counts1 = []
    if Silian_created_page_count := Silian_data.get("created_page_count", ""):
        Silian_sub_edit_counts1.append(str(I18NContext("wiki.message.user.created_page_count")) + Silian_created_page_count)
    if Silian_edited_count := Silian_data.get("edited_count", ""):
        if Silian_created_page_count:
            Silian_sub_edit_counts1.append(str(I18NContext("wiki.message.user.edited_count")) + Silian_edited_count)
    Silian_sub_edit_counts2 = []
    if Silian_deleted_count := Silian_data.get("deleted_count", ""):
        Silian_sub_edit_counts2.append(str(I18NContext("wiki.message.user.deleted_count")) + Silian_deleted_count)
    if Silian_patrolled_count := Silian_data.get("patrolled_count", ""):
        Silian_sub_edit_counts2.append(str(I18NContext("wiki.message.user.patrolled_count")) + Silian_patrolled_count)
    Silian_sub_edit_counts3 = []
    if Silian_site_rank := Silian_data.get("site_rank", ""):
        Silian_sub_edit_counts3.append(str(I18NContext("wiki.message.user.site_rank")) + Silian_site_rank)
    if Silian_global_rank := Silian_data.get("global_rank", ""):
        Silian_sub_edit_counts3.append(str(I18NContext("wiki.message.user.global_rank")) + Silian_global_rank)
    if Silian_sub_edit_counts1:
        Silian_msgs.append(Plain(" | ".join(Silian_sub_edit_counts1)))
    if Silian_sub_edit_counts2:
        Silian_msgs.append(Plain(" | ".join(Silian_sub_edit_counts2)))
    if Silian_sub_edit_counts3:
        Silian_msgs.append(Plain(" | ".join(Silian_sub_edit_counts3)))

    if Silian_global_users_groups := Silian_data.get("global_users_groups", ""):
        Silian_msgs.append(
            Plain(
                str(I18NContext("wiki.message.user.global_users_groups"))
                + "{I18N:message.delimiter}".join(Silian_global_users_groups)
            )
        )
    if Silian_global_edit_count := Silian_data.get("global_edit_count", ""):
        Silian_msgs.append(Plain(str(I18NContext("wiki.message.user.global_edited_count")) + Silian_global_edit_count))
    if Silian_global_home := Silian_data.get("global_home", ""):
        Silian_msgs.append(Plain(str(I18NContext("wiki.message.user.global_home")) + Silian_global_home))

    if Silian_blocked_by := Silian_data.get("blocked_by", False):
        Silian_msgs.append(Plain(str(I18NContext("wiki.message.user.blocked", user=Silian_user))))
        Silian_msgs.append(
            Plain(
                str(
                    I18NContext(
                        "wiki.message.user.blocked.detail",
                        blocked_by=Silian_blocked_by,
                        blocked_time=Silian_data["blocked_time"],
                        blocked_expires=Silian_data["blocked_expires"],
                    )
                )
            )
        )
        Silian_msgs.append(Plain(str(I18NContext("wiki.message.user.blocked.reason")) + Silian_data["blocked_reason"]))

    if Silian_url := Silian_data.get("url", ""):
        Silian_msgs.append(Url(Silian_url, use_mm=msg.session_info.use_url_manager and not Silian_wiki.wiki_info.in_allowlist))
    return MessageChain.assign(Silian_msgs)
