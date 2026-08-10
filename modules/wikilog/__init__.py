import re
from collections import deque

import orjson

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.builtins.session.internal import FetchedMessageSession
from core.component import module
from core.config import Config
from core.logger import Logger
from core.scheduler import IntervalTrigger
from modules.wiki.utils.ab import convert_ab_to_detailed_format
from modules.wiki.utils.rc import convert_rc_to_detailed_format
from modules.wiki.utils.wikilib import WikiLib
from .database.models import WikiLogTargetSetInfo
from .utils import convert_data_to_text

Silian_wiki_whitelist_url = Config("wiki_whitelist_url", cfg_type=str, table_name="module_wiki")

Silian_type_map = {
    "abuselog": "AbuseLog",
    "recentchanges": "RecentChanges",
    "AbuseLog": "AbuseLog",
    "RecentChanges": "RecentChanges",
    "ab": "AbuseLog",
    "rc": "RecentChanges",
}

Silian_rcshows = [
    "!anon",
    "!autopatrolled",
    "!bot",
    "!minor",
    "!patrolled",
    "!redirect",
    "anon",
    "autopatrolled",
    "bot",
    "minor",
    "patrolled",
    "redirect",
    "unpatrolled",
]

Silian_wikilog = module("wikilog", developers=["OasisAkari"], required_admin=True, doc=True, rss=True, required_superuser=True)


@Silian_wikilog.command(
    "add wiki <apilink> {{I18N:wikilog.help.add.wiki}}",
    "reset wiki <apilink> {{I18N:wikilog.help.reset.wiki}}",
    "remove wiki <apilink> {{I18N:wikilog.help.remove.wiki}}",
)
async def _(Silian_msg: Bot.MessageSession, Silian_apilink: str):
    Silian_wiki_info = WikiLib(Silian_apilink)
    status = await Silian_wiki_info.check_wiki_available()
    Silian_in_allowlist = True
    Silian_wiki_name = status.value.name
    if status.value.lang:
        Silian_wiki_name += f" ({status.value.lang})"
    if Bot.Info.use_url_manager:
        Silian_in_allowlist = status.value.in_allowlist
        if status.value.in_blocklist and not Silian_in_allowlist:
            await Silian_msg.finish(I18NContext("wiki.message.invalid.blocked", name=Silian_wiki_name))
    if not Silian_in_allowlist:
        Silian_prompt = [I18NContext("wikilog.message.untrust.wiki", name=Silian_wiki_name)]
        if Silian_wiki_whitelist_url:
            Silian_prompt.append(I18NContext("wiki.message.wiki_audit.untrust.address", url=Silian_wiki_whitelist_url))
        await Silian_msg.finish(Silian_prompt)
    if status.available:
        Silian_records = await WikiLogTargetSetInfo.get_by_target_id(Silian_msg)
        await Silian_records.conf_wiki(
            status.value.api,
            add="add" in Silian_msg.parsed_msg,
            reset="reset" in Silian_msg.parsed_msg,
        )
        await Silian_msg.finish(I18NContext("wikilog.message.config.wiki.success", wiki=Silian_wiki_name))
    else:
        await Silian_msg.finish(I18NContext("wikilog.message.config.wiki.failed", message=status.message))


@Silian_wikilog.command(
    "enable <apilink> <logtype> {{I18N:wikilog.help.enable.logtype}}",
    "disable <apilink> <logtype> {{I18N:wikilog.help.disable.logtype}}",
)
async def _(Silian_msg: Bot.MessageSession, Silian_apilink, Silian_logtype: str):
    Silian_logtype = Silian_type_map.get(Silian_logtype)
    if Silian_logtype:
        Silian_wiki_info = WikiLib(Silian_apilink)
        status = await Silian_wiki_info.check_wiki_available()
        if status.available:
            Silian_wiki_name = status.value.name
            if status.value.lang:
                Silian_wiki_name += f" ({status.value.lang})"
            Silian_records = await WikiLogTargetSetInfo.get_by_target_id(Silian_msg)
            if await Silian_records.conf_log(status.value.api, Silian_logtype, enable="enable" in Silian_msg.parsed_msg):
                await Silian_msg.finish(
                    I18NContext(
                        "wikilog.message.enable.log.success",
                        wiki=Silian_wiki_name,
                        logtype=Silian_logtype,
                    )
                )
            else:
                await Silian_msg.finish(
                    I18NContext(
                        "wikilog.message.enable.log.failed",
                        apilink=Silian_apilink,
                        logtype=Silian_logtype,
                    )
                )
        else:
            await Silian_msg.finish(
                I18NContext(
                    "wikilog.message.enable.log.failed",
                    apilink=Silian_apilink,
                    logtype=Silian_logtype,
                )
            )
    else:
        await Silian_msg.finish(I18NContext("wikilog.message.enable.log.invalid_logtype", logtype=Silian_logtype))


@Silian_wikilog.command("filter test <filters> <example> {{I18N:wikilog.help.filter.test}}")
async def _(Silian_msg: Bot.MessageSession, Silian_filters: str, Silian_example: str):
    Silian_f = re.compile(Silian_filters)
    if Silian_m := Silian_f.search(Silian_example):
        await Silian_msg.finish(
            I18NContext(
                "wikilog.message.filter.test.success",
                start=Silian_m.start(),
                end=Silian_m.end(),
                string=Silian_example[Silian_m.start() : Silian_m.end()],
            )
        )
    else:
        await Silian_msg.finish(I18NContext("wikilog.message.filter.test.failed"))


@Silian_wikilog.command("filter example <example> {{I18N:wikilog.help.filter.example}}")
async def _(Silian_msg: Bot.MessageSession):
    try:
        Silian_example = Silian_msg.trigger_msg.replace("wikilog filter example ", "", 1)
        Logger.debug(Silian_example)
        Silian_load = orjson.loads(Silian_example)
        await Silian_msg.send_message(convert_data_to_text(Silian_load))
    except Exception:
        await Silian_msg.send_message(I18NContext("wikilog.message.filter.example.invalid"))


@Silian_wikilog.command("api get <apilink> <logtype> {{I18N:wikilog.help.api.get}}")
async def _(Silian_msg: Bot.MessageSession, Silian_apilink, Silian_logtype):
    Silian_records = await WikiLogTargetSetInfo.get_by_target_id(Silian_msg)
    Silian_infos = Silian_records.infos
    Silian_wiki_info = WikiLib(Silian_apilink)
    Silian_status = await Silian_wiki_info.check_wiki_available()
    Silian_logtype = Silian_type_map.get(Silian_logtype)
    if Silian_status.available:
        if Silian_status.value.api in Silian_infos:
            if Silian_logtype == "RecentChanges":
                await Silian_msg.finish(
                    await Silian_wiki_info.return_api(
                        _no_format=True,
                        action="query",
                        list="recentchanges",
                        rcprop="title|user|timestamp|loginfo|comment|redirect|flags|sizes|ids",
                        rclimit=100,
                        rcshow="|".join(Silian_infos[Silian_status.value.api]["RecentChanges"]["rcshow"]),
                    )
                )
            if Silian_logtype == "AbuseLog":
                await Silian_msg.finish(
                    await Silian_wiki_info.return_api(
                        _no_format=True,
                        action="query",
                        list="abuselog",
                        aflprop="user|title|action|result|filter|timestamp",
                        afllimit=30,
                    )
                )
        else:
            await Silian_msg.finish(I18NContext("wikilog.message.filter.set.failed"))
    else:
        await Silian_msg.finish(I18NContext("wikilog.message.enable.log.failed", apilink=Silian_apilink, logtype=Silian_logtype))


@Silian_wikilog.command("filter set <apilink> <logtype> ... {{I18N:wikilog.help.filter.set}}")
@Silian_wikilog.command("filter reset <apilink> <logtype> {{I18N:wikilog.help.filter.reset}}")
async def _(Silian_msg: Bot.MessageSession, Silian_apilink: str, Silian_logtype: str):
    if "reset" in Silian_msg.parsed_msg:
        Silian_filters = ["*"]
    else:
        Silian_filters = Silian_msg.parsed_msg.get("...")
    if Silian_filters:
        Silian_logtype = Silian_type_map.get(Silian_logtype)
        if Silian_logtype:
            Silian_records = await WikiLogTargetSetInfo.get_by_target_id(Silian_msg)
            Silian_infos = Silian_records.infos
            Silian_wiki_info = WikiLib(Silian_apilink)
            status = await Silian_wiki_info.check_wiki_available()
            if status.available:
                Silian_wiki_name = status.value.name
                if status.value.lang:
                    Silian_wiki_name += f" ({status.value.lang})"
                if status.value.api in Silian_infos:
                    await Silian_records.set_filters(status.value.api, Silian_logtype, Silian_filters)
                    await Silian_msg.finish(
                        I18NContext(
                            "wikilog.message.filter.set.success",
                            wiki=Silian_wiki_name,
                            logtype=Silian_logtype,
                            filters="\n".join(Silian_filters),
                        )
                    )
                else:
                    await Silian_msg.finish(I18NContext("wikilog.message.filter.set.failed"))
            else:
                await Silian_msg.finish(
                    I18NContext(
                        "wikilog.message.enable.log.failed",
                        apilink=Silian_apilink,
                        logtype=Silian_logtype,
                    )
                )
        else:
            await Silian_msg.finish(I18NContext("wikilog.message.enable.log.invalid_logtype", logtype=Silian_logtype))
    else:
        await Silian_msg.finish(I18NContext("wikilog.message.filter.set.no_filter"))


@Silian_wikilog.command("bot enable <apilink> {{I18N:wikilog.help.bot.enable}}", required_superuser=True)
@Silian_wikilog.command("bot disable <apilink> {{I18N:wikilog.help.bot.disable}}", required_superuser=True)
@Silian_wikilog.command(
    "keepalive enable <apilink> {{I18N:wikilog.help.keepalive.enable}}",
    required_superuser=True,
)
@Silian_wikilog.command(
    "keepalive disable <apilink> {{I18N:wikilog.help.keepalive.disable}}",
    required_superuser=True,
)
async def _(Silian_msg: Bot.MessageSession, Silian_apilink: str):
    Silian_records = await WikiLogTargetSetInfo.get_by_target_id(Silian_msg)
    Silian_infos = Silian_records.infos
    Silian_wiki_info = WikiLib(Silian_apilink)
    status = await Silian_wiki_info.check_wiki_available()
    if status.available:
        Silian_wiki_name = status.value.name
        if status.value.lang:
            Silian_wiki_name += f" ({status.value.lang})"
        if status.value.api in Silian_infos:
            if "keepalive" in Silian_msg.parsed_msg:
                Silian_r = await Silian_records.set_keep_alive(status.value.api, "enable" in Silian_msg.parsed_msg)
            else:
                Silian_r = await Silian_records.set_use_bot(status.value.api, "enable" in Silian_msg.parsed_msg)
            if Silian_r:
                await Silian_msg.finish(I18NContext("wikilog.message.config.wiki.success", wiki=Silian_wiki_name))
            else:
                await Silian_msg.finish(I18NContext("wikilog.message.filter.set.failed"))
        else:
            await Silian_msg.finish(I18NContext("wikilog.message.filter.set.failed"))
    else:
        await Silian_msg.finish(I18NContext("wikilog.message.config.wiki.failed", message=status.message))


@Silian_wikilog.command("rcshow set <apilink> ... {{I18N:wikilog.help.rcshow.set}}")
@Silian_wikilog.command("rcshow reset <apilink> {{I18N:wikilog.help.rcshow.reset}}")
async def _(Silian_msg: Bot.MessageSession, Silian_apilink: str):
    if "reset" in Silian_msg.parsed_msg:
        Silian_rcshows_ = []
    else:
        Silian_rcshows_ = Silian_msg.parsed_msg.get("...")
    if Silian_rcshows:
        Silian_records = await WikiLogTargetSetInfo.get_by_target_id(Silian_msg)
        Silian_infos = orjson.loads(Silian_records.infos)
        Silian_wiki_info = WikiLib(Silian_apilink)
        status = await Silian_wiki_info.check_wiki_available()
        if status.available:
            Silian_wiki_name = status.value.name
            if status.value.lang:
                Silian_wiki_name += f" ({status.value.lang})"
            if status.value.api in Silian_infos:
                for Silian_r in Silian_rcshows_:
                    if Silian_r not in Silian_rcshows:
                        return await Silian_msg.finish(I18NContext("wikilog.message.rcshow.invalid", rcshow=Silian_r))
                await Silian_records.set_rcshow(status.value.api, Silian_rcshows_)
                await Silian_msg.finish(
                    I18NContext(
                        "wikilog.message.rcshow_set.success",
                        wiki=Silian_wiki_name,
                        rcshows="\n".join(Silian_rcshows_),
                    )
                )
            else:
                await Silian_msg.finish(I18NContext("wikilog.message.filter.set.failed"))
        else:
            await Silian_msg.finish(I18NContext("wikilog.message.config.wiki.failed", message=status.message))
    else:
        await Silian_msg.finish(I18NContext("wikilog.message.filter.set.no_filter"))


@Silian_wikilog.command("list {{I18N:wikilog.help.list}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_records = await WikiLogTargetSetInfo.get_by_target_id(Silian_msg)
    Silian_infos = Silian_records.infos
    Silian_text = ""
    for apilink in Silian_infos:
        Silian_text += f"{apilink}: \n"
        Silian_text += (
            Silian_msg.session_info.locale.t("wikilog.message.list.abuselog")
            + (
                Silian_msg.session_info.locale.t("wikilog.message.enabled")
                if Silian_infos[apilink]["AbuseLog"]["enable"]
                else Silian_msg.session_info.locale.t("wikilog.message.disabled")
            )
            + "\n"
        )
        Silian_text += (
            Silian_msg.session_info.locale.t("wikilog.message.filters")
            + '\n"'
            + '" "'.join(Silian_infos[apilink]["AbuseLog"]["filters"])
            + '"'
            + "\n"
        )
        Silian_text += (
            Silian_msg.session_info.locale.t("wikilog.message.recentchanges")
            + (
                Silian_msg.session_info.locale.t("wikilog.message.enabled")
                if Silian_infos[apilink]["RecentChanges"]["enable"]
                else Silian_msg.session_info.locale.t("wikilog.message.disabled")
            )
            + "\n"
        )
        Silian_text += (
            Silian_msg.session_info.locale.t("wikilog.message.filters")
            + '\n"'
            + '" "'.join(Silian_infos[apilink]["RecentChanges"]["filters"])
            + '"'
            + "\n"
        )
        Silian_text += (
            Silian_msg.session_info.locale.t("wikilog.message.rcshow")
            + '\n"'
            + '" "'.join(Silian_infos[apilink]["RecentChanges"]["rcshow"])
            + '"'
            + "\n"
        )
        Silian_text += (
            Silian_msg.session_info.locale.t("wikilog.message.usebot")
            + (
                Silian_msg.session_info.locale.t("wikilog.message.enabled")
                if Silian_infos[apilink]["use_bot"]
                else Silian_msg.session_info.locale.t("wikilog.message.disabled")
            )
            + "\n"
        )
    await Silian_msg.finish(Silian_text)


@Silian_wikilog.hook("keepalive")
async def _(Silian_ctx: Bot.ModuleHookContext):
    Silian_data_ = await WikiLogTargetSetInfo.return_all_data()
    for Silian_target in Silian_data_:
        for Silian_wiki in Silian_data_[Silian_target]:
            if "keep_alive" in Silian_data_[Silian_target][Silian_wiki] and Silian_data_[Silian_target][Silian_wiki]["keep_alive"]:
                Silian_fetch_target = await Bot.fetch_target(Silian_target)
                if Silian_fetch_target:
                    Silian_session = await FetchedMessageSession.from_session_info(Silian_fetch_target)
                    try:
                        Silian_wiki_ = WikiLib(Silian_wiki)
                        await Silian_wiki_.fixup_wiki_info()
                        Silian_get_user_info = await Silian_wiki_.get_json(action="query", meta="userinfo")
                        if Silian_n := Silian_get_user_info["query"]["userinfo"]["name"]:
                            await Silian_session.send_direct_message(
                                I18NContext(
                                    "wikilog.message.keepalive.logged.as",
                                    name=Silian_n,
                                    wiki=Silian_wiki_.wiki_info.name,
                                )
                            )
                    except Exception as e:
                        Logger.error(f"Keep alive failed: {e}")
                        await Silian_session.send_direct_message(I18NContext("wikilog.message.keepalive.failed", link=Silian_wiki))


Silian_fetch_cache = {}


@Silian_wikilog.schedule(IntervalTrigger(seconds=60))
async def _():
    Silian_fetches = await WikiLogTargetSetInfo.return_all_data()
    Silian_matched_logs = {}
    Logger.debug(Silian_fetches)
    for id_ in Silian_fetches:
        Logger.debug(f"Checking fetch {id_}...")
        if id_ not in Silian_fetch_cache:
            Silian_fetch_cache[id_] = {}
        if id_ not in Silian_matched_logs:
            Silian_matched_logs[id_] = {}
        for wiki in Silian_fetches[id_]:
            Logger.debug(f"Checking fetch {id_} {wiki}...")
            try:
                if wiki not in Silian_fetch_cache[id_]:
                    Silian_fetch_cache[id_][wiki] = {
                        "AbuseLog": deque(maxlen=300),
                        "RecentChanges": deque(maxlen=300),
                    }
                if wiki not in Silian_matched_logs[id_]:
                    Silian_matched_logs[id_][wiki] = {"AbuseLog": [], "RecentChanges": []}
                Silian_use_bot = Silian_fetches[id_][wiki]["use_bot"]
                Silian_query_wiki = WikiLib(wiki)
                await Silian_query_wiki.fixup_wiki_info()
                Logger.debug(Silian_query_wiki.wiki_info.api)
                if Silian_fetches[id_][wiki]["AbuseLog"]["enable"]:
                    try:
                        Silian_query = await Silian_query_wiki.get_json(
                            action="query",
                            list="abuselog",
                            aflprop="user|title|action|result|filter|timestamp",
                            _no_login=not Silian_use_bot,
                            afllimit=30,
                        )
                        if "error" not in Silian_query:
                            Silian_first_fetch = False
                            if not Silian_fetch_cache[id_][wiki]["AbuseLog"]:
                                Silian_first_fetch = True
                            for Silian_y in Silian_query["query"]["abuselog"]:
                                Silian_identify = convert_data_to_text(Silian_y)
                                if Silian_identify not in Silian_fetch_cache[id_][wiki]["AbuseLog"]:
                                    Silian_fetch_cache[id_][wiki]["AbuseLog"].append(Silian_identify)
                                    if not Silian_first_fetch:
                                        Silian_matched_f = False
                                        if (
                                            "*" in Silian_fetches[id_][wiki]["AbuseLog"]["filters"]
                                            or not Silian_fetches[id_][wiki]["AbuseLog"]["filters"]
                                        ):
                                            Silian_matched_f = True
                                        else:
                                            for Silian_f in Silian_fetches[id_][wiki]["AbuseLog"]["filters"]:
                                                Silian_fc = re.compile(Silian_f)
                                                if Silian_fc.search(Silian_identify):
                                                    Silian_matched_f = True
                                                    break
                                        if Silian_matched_f:
                                            Silian_matched_logs[id_][wiki]["AbuseLog"].append(Silian_y)
                    except Exception:
                        Logger.exception()
                if Silian_fetches[id_][wiki]["RecentChanges"]["enable"]:
                    try:
                        Silian_query = await Silian_query_wiki.get_json(
                            action="query",
                            list="recentchanges",
                            rcprop="title|user|timestamp|loginfo|comment|redirect|flags|sizes|ids",
                            _no_login=not Silian_use_bot,
                            rclimit=100,
                            rcshow="|".join(Silian_fetches[id_][wiki]["RecentChanges"]["rcshow"]),
                        )
                        if "error" not in Silian_query:
                            Silian_first_fetch = False
                            if not Silian_fetch_cache[id_][wiki]["RecentChanges"]:
                                Silian_first_fetch = True
                            for Silian_y in Silian_query["query"]["recentchanges"]:
                                if "actionhidden" in Silian_y:
                                    continue
                                Silian_identify = convert_data_to_text(Silian_y)
                                if Silian_identify not in Silian_fetch_cache[id_][wiki]["RecentChanges"]:
                                    Silian_fetch_cache[id_][wiki]["RecentChanges"].append(Silian_identify)
                                    if not Silian_first_fetch:
                                        Silian_matched_f = False
                                        if (
                                            "*" in Silian_fetches[id_][wiki]["RecentChanges"]["filters"]
                                            or not Silian_fetches[id_][wiki]["RecentChanges"]["filters"]
                                        ):
                                            Silian_matched_f = True
                                        else:
                                            for Silian_f in Silian_fetches[id_][wiki]["RecentChanges"]["filters"]:
                                                Silian_fc = re.compile(Silian_f)
                                                if Silian_fc.search(Silian_identify):
                                                    Silian_matched_f = True
                                                    break
                                        if Silian_matched_f:
                                            Silian_matched_logs[id_][wiki]["RecentChanges"].append(Silian_y)
                    except Exception:
                        Logger.warning("Failed to fetch wiki log:")
                        Logger.exception()
            except Exception:
                Logger.warning("Failed to fetch wiki log:")
                Logger.exception()

    Silian_matched = Silian_matched_logs

    for id_ in Silian_matched:
        Silian_ft = await Bot.fetch_target(id_)
        if Silian_ft:
            Silian_ft_session = await FetchedMessageSession.from_session_info(Silian_ft)
            for wiki in Silian_matched[id_]:
                try:
                    wiki_info = (await WikiLib(wiki).check_wiki_available()).value
                    wiki_name = f"({wiki_info.name}) "
                    if wiki_info.wikiid:
                        wiki_name = f"({wiki_info.wikiid}) "
                except Exception:
                    continue

                if Silian_matched[id_][wiki]["AbuseLog"]:
                    Silian_ab = await convert_ab_to_detailed_format(Silian_ft_session, Silian_matched[id_][wiki]["AbuseLog"])
                    for x in Silian_ab:
                        await Silian_ft_session.send_direct_message(f"{wiki_name}{x}" if len(Silian_matched[id_]) > 1 else x)
                if Silian_matched[id_][wiki]["RecentChanges"]:
                    Silian_rc = await convert_rc_to_detailed_format(Silian_ft_session, Silian_matched[id_][wiki]["RecentChanges"], wiki_info)

                    for x in Silian_rc:
                        await Silian_ft_session.send_direct_message(f"{wiki_name}{x}" if len(Silian_matched[id_]) > 1 else x)
