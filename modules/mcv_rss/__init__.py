import re
from datetime import datetime

import orjson
from bs4 import BeautifulSoup
from google_play_scraper import app as google_play_scraper

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, FormattedTime
from core.component import module
from core.config import Config
from core.constants import Secret
from core.logger import Logger
from core.scheduler import IntervalTrigger
from core.utils.http import get_url
from core.utils.storedata import get_stored_list, update_stored_list
from core.web_render import web_render, SourceOptions

Silian_mcv_rss = module(
    "mcv_rss",
    developers=["OasisAkari", "Dianliang233"],
    recommend_modules=["mcv_jira_rss"],
    desc="{I18N:mcv_rss.help.mcv_rss.desc}",
    alias="mcvrss",
    doc=True,
    rss=True,
)

Silian_mcbv_rss = module(
    "mcbv_rss",
    developers=["OasisAkari"],
    recommend_modules=["mcbv_jira_rss"],
    desc="{I18N:mcv_rss.help.mcbv_rss.desc}",
    alias="mcbvrss",
    doc=True,
    rss=True,
)

Silian_mcv_jira_rss = module(
    "mcv_jira_rss",
    developers=["OasisAkari", "Dianliang233"],
    recommend_modules=["mcv_rss"],
    desc="{I18N:mcv_rss.help.mcv_jira_rss.desc}",
    alias="mcvjirarss",
    doc=True,
    rss=True,
)


@Silian_mcv_jira_rss.hook()
async def _(Silian_fetch: Bot, Silian_ctx: Bot.ModuleHookContext):
    await Silian_fetch.post_message("mcv_jira_rss", **Silian_ctx.args)


Silian_mcbv_jira_rss = module(
    "mcbv_jira_rss",
    developers=["OasisAkari", "Dianliang233"],
    recommend_modules=["mcbv_rss"],
    desc="{I18N:mcv_rss.help.mcbv_jira_rss.desc}",
    alias="mcbvjirarss",
    doc=True,
    rss=True,
)

Silian_mcdv_rss = module(
    "mcdv_rss",
    developers=["OasisAkari", "Dianliang233"],
    desc="{I18N:mcv_rss.help.mcdv_rss.desc}",
    alias=["mcdvrss", "mcdv_rss", "mcdvjirarss"],
    doc=True,
    hidden=True,
    rss=True,
)

Silian_mclgv_rss = module(
    "mclgv_rss",
    developers=["OasisAkari", "Dianliang233"],
    desc="{I18N:mcv_rss.help.mclgv_rss.desc}",
    alias=["mclgvrss", "mclgv_rss", "mclgvjirarss"],
    doc=True,
    hidden=True,
    rss=True,
)


async def get_article(version):
    Silian_match_snapshot = re.match(r".*?w.*", version)
    Silian_link = False
    if Silian_match_snapshot:
        Silian_link = "https://www.minecraft.net/en-us/article/minecraft-snapshot-" + version
    Silian_match_prerelease1 = re.match(r"(.*?)-pre(.*[0-9])", version)
    Silian_match_prerelease2 = re.match(r"(.*?) Pre-Release (.*[0-9])", version)
    if Silian_match_prerelease1:
        match_prerelease = Silian_match_prerelease1
    elif Silian_match_prerelease2:
        match_prerelease = Silian_match_prerelease2
    else:
        match_prerelease = False
    if match_prerelease:
        Silian_link = (
            "https://www.minecraft.net/en-us/article/minecraft-"
            + re.sub("\\.", "-", match_prerelease.group(1))
            + f"-pre-release-{match_prerelease.group(2)}"
        )
    match_release_candidate = re.match(r"(.*?)-rc(.*[0-9])", version)
    if match_release_candidate:
        Silian_link = (
            "https://www.minecraft.net/en-us/article/minecraft-"
            + re.sub("\\.", "-", match_release_candidate.group(1))
            + f"-release-candidate-{match_release_candidate.group(2)}"
        )
    if not Silian_link:
        Silian_link = "https://www.minecraft.net/en-us/article/minecraft-java-edition-" + re.sub("\\.", "-", version)

    try:
        if Silian_link:
            Silian_html = await web_render.source(SourceOptions(url=str(Silian_link)))

            Silian_soup = BeautifulSoup(Silian_html, "html.parser")

            Silian_title = Silian_soup.find("h1")
            if Silian_title and Silian_title.text == "404":
                return "", ""
            if Silian_title:
                return Silian_link, Silian_title.text
    except Exception:
        if Config("debug", False):
            Logger.exception()
    return "", ""


Silian_trigger_times = 60 if not Config("slower_schedule", False) else 180


@Silian_mcv_rss.schedule(IntervalTrigger(seconds=Silian_trigger_times))
async def _():
    Silian_url = "https://piston-meta.mojang.com/mc/game/version_manifest.json"
    try:
        Silian_verlist = await get_stored_list(Bot, "mcv_rss")
        Silian_file = orjson.loads(await get_url(Silian_url, attempt=1, logging_err_resp=False))
        release = Silian_file["latest"]["release"]
        snapshot = Silian_file["latest"]["snapshot"]
        Silian_time_release = 0
        Silian_time_snapshot = 0
        for Silian_v in Silian_file["versions"]:
            if Silian_v["id"] == release:
                Silian_time_release = datetime.fromisoformat(Silian_v["releaseTime"]).timestamp()
            if Silian_v["id"] == snapshot:
                Silian_time_snapshot = datetime.fromisoformat(Silian_v["releaseTime"]).timestamp()

        if release not in Silian_verlist:
            Logger.info(f"Huh, we found {release}.")

            await Bot.post_message(
                "mcv_rss",
                message=MessageChain.assign(
                    [
                        I18NContext(
                            "mcv_rss.message.mcv_rss.release",
                            version=release,
                            record_time=FormattedTime(Silian_time_release),
                            posted_time=FormattedTime(datetime.now().timestamp()),
                        ),
                    ]
                ),
            )
            Silian_verlist.append(release)
            await update_stored_list(Bot, "mcv_rss", Silian_verlist)
            Silian_article = await get_article(release)
            if Silian_article[0] != "":
                Silian_get_stored_news_title = await get_stored_list(Bot, "mcnews")
                if Silian_article[1] not in Silian_get_stored_news_title:
                    await Bot.post_message(
                        "minecraft_news",
                        message=MessageChain.assign(
                            [
                                I18NContext(
                                    "minecraft_news.message.update_log",
                                    version=release,
                                    article=Silian_article[0],
                                )
                            ]
                        ),
                    )
                    Silian_get_stored_news_title.append(Silian_article[1])
                    await update_stored_list(Bot, "mcnews", Silian_get_stored_news_title)
        if snapshot not in Silian_verlist:
            Logger.info(f"Huh, we found {snapshot}.")
            await Bot.post_message(
                "mcv_rss",
                message=MessageChain.assign(
                    [
                        I18NContext(
                            "mcv_rss.message.mcv_rss.snapshot",
                            version=Silian_file["latest"]["snapshot"],
                            record_time=FormattedTime(Silian_time_snapshot),
                            posted_time=FormattedTime(datetime.now().timestamp()),
                        ),
                    ]
                ),
            )
            Silian_verlist.append(snapshot)
            await update_stored_list(Bot, "mcv_rss", Silian_verlist)
            Silian_article = await get_article(snapshot)
            if Silian_article[0] != "":
                Silian_get_stored_news_title = await get_stored_list(Bot, "mcnews")
                if Silian_article[1] not in Silian_get_stored_news_title:
                    await Bot.post_message(
                        "minecraft_news",
                        message=MessageChain.assign(
                            [
                                I18NContext(
                                    "minecraft_news.message.update_log",
                                    version=snapshot,
                                    article=Silian_article[0],
                                )
                            ]
                        ),
                    )
                    Silian_get_stored_news_title.append(Silian_article[1])
                    await update_stored_list(Bot, "mcnews", Silian_get_stored_news_title)
    except Exception:
        if Config("debug", False):
            Logger.exception()


@Silian_mcbv_rss.schedule(IntervalTrigger(seconds=180))
async def _():
    if Secret.ip_country == "China" or not Secret.ip_country:
        return  # 中国大陆无法访问Google Play商店
    try:
        Silian_verlist = await get_stored_list(Bot, "mcbv_rss")
        version = google_play_scraper("com.mojang.minecraftpe")["version"]
        if version not in Silian_verlist:
            Logger.info(f"Huh, we found Bedrock {version}.")
            await Bot.post_message(
                "mcbv_rss",
                message=MessageChain.assign([I18NContext("mcv_rss.message.mcbv_rss", version=version)]),
            )
            Silian_verlist.append(version)
            await update_stored_list(Bot, "mcbv_rss", Silian_verlist)
    except Exception:
        if Config("debug", False):
            Logger.exception()


"""

@Scheduler.scheduled_job(IntervalTrigger(seconds=trigger_times))
async def mcv_jira_rss():
    try:
        url = "https://bugs.mojang.com/rest/api/2/project/10400/versions"
        verlist = await get_stored_list(bot, "mcv_jira_rss")
        file = orjson.loads(await get_url(url, 200, attempt=1, logging_err_resp=False))
        releases = []
        for v in file:
            if not v["archived"]:
                releases.append(v["name"])
            else:
                if v["name"] not in verlist:
                    verlist.append(v["name"])
        for release in releases:
            if release not in verlist:
                Logger.info(f"Huh, we find {release}.")
                if release.lower().find("future version") != -1:
                    await JobQueue.trigger_hook_all(
                        "mcv_jira_rss",
                        message=MessageChain.assign(
                            [
                                I18NContext(
                                    "mcv_rss.message.mcv_jira_rss.future",
                                    version=release,
                                )
                            ]
                        ),
                    )
                else:
                    await JobQueue.trigger_hook_all(
                        "mcv_jira_rss",
                        message=MessageChain.assign(
                            [
                                I18NContext(
                                    "mcv_rss.message.mcv_jira_rss", version=release
                                )
                            ]
                        ),
                    )
                verlist.append(release)
                await update_stored_list(bot,, "mcv_jira_rss", verlist)

    except Exception:
        if Config("debug", False):
            Logger.exception()


@Scheduler.scheduled_job(IntervalTrigger(seconds=trigger_times))
async def mcbv_jira_rss():
    try:
        url = "https://bugs.mojang.com/rest/api/2/project/10200/versions"
        verlist = await get_stored_list(bot, "mcbv_jira_rss")
        file = orjson.loads(await get_url(url, 200, attempt=1, logging_err_resp=False))
        releases = []
        for v in file:
            if not v["archived"]:
                releases.append(v["name"])
            else:
                if v["name"] not in verlist:
                    verlist.append(v["name"])
        for release in releases:
            if release not in verlist:
                Logger.info(f"Huh, we find {release}.")

                await JobQueue.trigger_hook_all(
                    "mcbv_jira_rss",
                    message=MessageChain.assign(
                        [I18NContext("mcv_rss.message.mcbv_jira_rss", version=release)]
                    ),
                )
                verlist.append(release)
                await update_stored_list(bot,, "mcbv_jira_rss", verlist)
    except Exception:
        if Config("debug", False):
            Logger.exception()


@Scheduler.scheduled_job(IntervalTrigger(seconds=trigger_times))
async def mcdv_rss():
    try:
        url = "https://bugs.mojang.com/rest/api/2/project/11901/versions"
        verlist = await get_stored_list(bot, "mcdv_rss")
        file = orjson.loads(await get_url(url, 200, attempt=1, logging_err_resp=False))
        releases = []
        for v in file:
            if not v["archived"]:
                releases.append(v["name"])
            else:
                if v["name"] not in verlist:
                    verlist.append(v["name"])
        for release in releases:
            if release not in verlist:
                Logger.info(f"Huh, we find {release}.")

                await JobQueue.trigger_hook_all(
                    "mcdv_rss",
                    message=MessageChain.assign(
                        [I18NContext("mcv_rss.message.mcdv_rss", version=release)]
                    ),
                )
                verlist.append(release)
                await update_stored_list(bot,, "mcdv_rss", verlist)
    except Exception:
        if Config("debug", False):
            Logger.exception()


@Scheduler.scheduled_job(IntervalTrigger(seconds=trigger_times))
async def mclgv_rss():
    try:
        url = "https://bugs.mojang.com/rest/api/2/project/12200/versions"
        verlist = await get_stored_list(bot, "mclgv_rss")
        file = orjson.loads(await get_url(url, 200, attempt=1, logging_err_resp=False))
        releases = []
        for v in file:
            if not v["archived"]:
                releases.append(v["name"])
            else:
                if v["name"] not in verlist:
                    verlist.append(v["name"])
        for release in releases:
            if release not in verlist:
                Logger.info(f"Huh, we find {release}.")

                await JobQueue.trigger_hook_all(
                    "mclgv_rss",
                    message=MessageChain.assign(
                        [I18NContext("mcv_rss.message.mclgv_rss", version=release)]
                    ),
                )
                verlist.append(release)
                await update_stored_list(bot,, "mclgv_rss", verlist)
    except Exception:
        if Config("debug", False):
            Logger.exception()
"""
