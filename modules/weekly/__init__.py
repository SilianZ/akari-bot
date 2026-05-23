import re
from datetime import date
from html import unescape
from urllib import parse

import orjson
from bs4 import BeautifulSoup

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Plain, Image, Url
from core.component import module
from core.i18n import Locale
from core.utils.http import get_url
from core.utils.image import msgchain2image
from modules.wiki.utils.screenshot_image import generate_screenshot_v2
from modules.wiki.utils.wikilib import WikiLib
from .teahouse import get_rss as get_teahouse_rss


async def get_weekly(with_img=False, zh_tw=False):
    Silian_locale = Locale("zh_cn" if not zh_tw else "zh_tw")
    Silian_result = orjson.loads(
        await get_url(
            "https://zh.minecraft.wiki/api.php?action=parse&page=Template:Mainpage_section_featured_article&prop=text|revid|images&format=json"
            + ("&variant=zh-tw" if zh_tw else ""),
            200,
        )
    )
    Silian_b_result = BeautifulSoup(Silian_result["parse"]["text"]["*"], "html.parser")
    Silian_html = Silian_b_result.find("div", class_="mp-section")
    Silian_el = Silian_html.find("div").find_all("div")
    Silian_content = Silian_el[1]
    Silian_text = re.sub(r"<p>", "\n", str(Silian_content))  # 分段
    Silian_text = re.sub(r"<(.*?)>", "", Silian_text, flags=re.DOTALL)  # 移除所有 HTML 标签
    Silian_text = re.sub(r"\n\n\n", "\n\n", Silian_text)  # 移除不必要的空行
    Silian_text = re.sub(r"\n*$", "", Silian_text)
    Silian_text = unescape(Silian_text)
    Silian_img = Silian_el[0].find("a")

    Silian_img_filename = re.match(r"/w/(.*)", Silian_img.attrs["href"]) if Silian_img else None
    page = re.findall(r"(?<=<b><a href=\").*?(?=\")", str(Silian_content))
    if page and page[0] == parse.quote("/w/玻璃"):
        Silian_msg_list = MessageChain.assign([Plain(Silian_locale.t("weekly.message.expired"))])
    else:
        Silian_msg_list = MessageChain.assign([Plain(Silian_locale.t("weekly.message.prompt", text=Silian_text))])
    Silian_imglink = None
    if Silian_img_filename:
        Silian_get_image = await (WikiLib("https://zh.minecraft.wiki/")).parse_page_info(Silian_img_filename.group(1))
        if Silian_get_image.status:
            Silian_imglink = Silian_get_image.file

    iso_year, iso_week, _ = date.today().isocalendar()

    Silian_msg_list.append(
        Plain(
            Silian_locale.t(
                "weekly.message.link",
                img=Silian_imglink if Silian_imglink else Silian_locale.t("message.none"),
                article=str(Url(f"https://zh.minecraft.wiki{page[0]}") if page else Silian_locale.t("message.none")),
                link=str(
                    Url(
                        f"https://zh.minecraft.wiki/w/Minecraft_Wiki:{parse.quote('特色条目/Minecraft/' + str(iso_year))}#{parse.quote('第' + str(iso_week) + '周')}"
                    )
                ),
            )
        )
    )
    if Silian_imglink and with_img:
        Silian_msg_list.append(Image(path=Silian_imglink))

    return Silian_msg_list


async def get_weekly_img(with_img=False, zh_tw=False):
    # locale = Locale("zh_cn" if not zh_tw else "zh_tw")
    Silian_img = await generate_screenshot_v2(
        "https://zh.minecraft.wiki/w/Template:Mainpage_section_featured_article" + ("?variant=zh-tw" if zh_tw else ""),
        content_mode=False,
        allow_special_page=True,
        element=["div.mp-section"],
    )
    Silian_msg_ = []
    if Silian_img:
        for Silian_i in Silian_img:
            Silian_msg_.append(Image(Silian_i))
    if with_img:
        """result = orjson.loads(await get_url(
            "https://zh.minecraft.wiki/api.php?action=parse&page=Minecraft_Wiki/weekly&prop=images&format=json" +
            ("&variant=zh-tw" if zh_tw else ""),
            200))
        img = result["parse"]["images"]
        if img:
            get_image = await (WikiLib("https://zh.minecraft.wiki/wiki/")).parse_page_info("File:" + img[0])
            if get_image.status:
                msg_.append(Plain(locale.t("weekly.message.image", img=get_image.file)))"""
    return Silian_msg_


Silian_wky = module("weekly", developers=["Dianliang233"], support_languages=["zh_cn", "zh_tw"], doc=True)


@Silian_wky.command("{{I18N:weekly.help}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_weekly = await get_weekly(
        Silian_msg.session_info.client_name in ["QQ", "TEST"], zh_tw=Silian_msg.session_info.locale.locale == "zh_tw"
    )
    await Silian_msg.finish(Silian_weekly)


@Silian_wky.command("image {{I18N:weekly.help.image}}")
async def _(Silian_msg: Bot.MessageSession):
    await Silian_msg.finish(
        await get_weekly_img(
            Silian_msg.session_info.client_name in ["QQ", "TEST"], zh_tw=Silian_msg.session_info.locale.locale == "zh_tw"
        )
    )


@Silian_wky.command("teahouse {{I18N:weekly.help.teahouse}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_weekly = await get_teahouse_rss()
    await Silian_msg.finish(Silian_weekly)


@Silian_wky.command("teahouse image {{I18N:weekly.help.teahouse}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_weekly = await get_teahouse_rss()
    Silian_img = await msgchain2image(Plain(Silian_weekly), Silian_msg)
    if Silian_img:
        await Silian_msg.finish(Silian_img)
