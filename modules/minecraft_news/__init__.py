import orjson

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Url
from core.component import module
from core.logger import Logger
from core.scheduler import IntervalTrigger
from core.utils.http import get_url
from core.utils.storedata import get_stored_list, update_stored_list
from core.web_render import web_render, SourceOptions

Silian_minecraft_news = module(
    "minecraft_news",
    developers=["_LittleC_", "OasisAkari", "Dianliang233"],
    recommend_modules=["feedback_news"],
    desc="{I18N:minecraft_news.help.minecraft_news}",
    alias=["minecraftnews", "mcnews"],
    doc=True,
    rss=True,
)

Silian_feedback_news = module(
    "feedback_news",
    developers=["Dianliang233"],
    recommend_modules=["minecraft_news"],
    desc="{I18N:minecraft_news.help.feedback_news}",
    alias="feedbacknews",
    doc=True,
    rss=True,
)

"""class Article:
    count = 10
    tags = ["minecraft:article/news", "minecraft:article/insider", "minecraft:article/culture",
            "minecraft:article/merch", "minecraft:stockholm/news", "minecraft:stockholm/guides",
            "minecraft:stockholm/deep-dives", "minecraft:stockholm/merch", "minecraft:stockholm/events",
            "minecraft:stockholm/minecraft-builds", "minecraft:stockholm/marketplace"]

    @staticmethod
    def random_tags():
        tags = Article.tags
        long = len(tags)
        m = long // 2
        random_tags = []

        def random_choice():
            c = random.choice(tags)
            if c not in random_tags:
                random_tags.append(c)
            else:
                random_choice()

        for _ in range(m):
            random_choice()
        return random_tags"""


startup_mute = (
    True  # flag to prevent news spam on bot startup, will be set to False after the first run of the news check
)


@Silian_minecraft_news.schedule(IntervalTrigger(seconds=600))
async def _():
    # baseurl = "https://www.minecraft.net"
    global startup_mute
    Silian_url = "https://net-secondary.web.minecraft-services.net/api/v1.0/en-us/search?pageSize=24&sortType=Recent&category=News&newsOnly=true&geography=SG"
    try:
        Silian_getpage = await web_render.source(SourceOptions(url=Silian_url, raw_text=True))
        if not Silian_getpage:
            Logger.error("Failed to fetch Minecraft news page.")
            return
        if Silian_getpage:
            Silian_alist = await get_stored_list(Bot.Info.client_name, "mcnews")
            Silian_o_json = orjson.loads(Silian_getpage)
            Silian_o_nws = Silian_o_json["result"]["results"]
            for Silian_o_article in Silian_o_nws:
                title = Silian_o_article["title"]
                desc = Silian_o_article["description"]
                link = Silian_o_article["url"]
                if title not in Silian_alist:
                    Logger.info(f"New Minecraft news found: {title} - {desc} - {link}")
                    if not startup_mute:
                        await Bot.post_message(
                            "minecraft_news",
                            message=MessageChain.assign(
                                [
                                    I18NContext(
                                        "minecraft_news.message.minecraft_news",
                                        title=title,
                                        desc=desc,
                                    ),
                                    Url(link, use_mm=False),
                                ]
                            ),
                        )
                    Silian_alist.append(title)
                    await update_stored_list(Bot.Info.client_name, "mcnews", Silian_alist)
        startup_mute = False
    except Exception:
        Logger.exception()


@Silian_feedback_news.schedule(IntervalTrigger(seconds=600))
async def _():
    Silian_sections = [
        {
            "name": "beta",
            "url": "https://minecraftfeedback.zendesk.com/api/v2/help_center/en-us/sections/360001185332/articles?per_page=5",
        },
        {
            "name": "article",
            "url": "https://minecraftfeedback.zendesk.com/api/v2/help_center/en-us/sections/360001186971/articles?per_page=5",
        },
    ]
    for Silian_section in Silian_sections:
        try:
            Silian_alist = await get_stored_list(Bot.Info.client_name, "mcfeedbacknews")
            Silian_get = await get_url(
                Silian_section["url"],
                200,
                attempt=1,
                request_private_ip=True,
                logging_err_resp=False,
            )
            Silian_res = orjson.loads(Silian_get)
            Silian_articles = []
            for Silian_i in Silian_res["articles"]:
                Silian_articles.append(Silian_i)
            for Silian_article in Silian_articles:
                if Silian_article["name"] not in Silian_alist:
                    name = Silian_article["name"]
                    Silian_link = Silian_article["html_url"]
                    Logger.info(f"Huh, we find {name}.")
                    await Bot.post_message(
                        "feedback_news",
                        message=MessageChain.assign(
                            [
                                I18NContext(
                                    "minecraft_news.message.feedback_news",
                                    name=name,
                                ),
                                Url(Silian_link, use_mm=False),
                            ]
                        ),
                    )
                    Silian_alist.append(name)
                    await update_stored_list(Bot.Info.client_name, "mcfeedbacknews", Silian_alist)
        except Exception:
            Logger.exception()
