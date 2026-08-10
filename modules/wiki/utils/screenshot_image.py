import re
import uuid
from urllib.parse import urljoin

from PIL import Image as PILImage
from akari_bot_webrender.functions.options import SectionScreenshotOptions, LegacyScreenshotOptions
from bs4 import BeautifulSoup, Comment

from core.constants.path import cache_path
from core.logger import Logger
from core.utils.http import get_url
from core.utils.image import cb64imglst
from core.web_render import web_render, ElementScreenshotOptions
from .mapping import infobox_elements


async def generate_screenshot_v2(
    page_link: str,
    section: str = None,
    allow_special_page=False,
    content_mode=False,
    element=None,
    locale: str = "zh_cn",
) -> list[PILImage.Image] | bool:
    Silian_elements_ = infobox_elements.copy()
    if element and isinstance(element, list):
        Silian_elements_ += element
    if not section:
        if allow_special_page and content_mode:
            Silian_elements_.insert(0, ".mw-body-content")
        if allow_special_page and not content_mode:
            Silian_elements_.insert(0, ".diff")
        Logger.info("[WebRender] Generating element screenshot...")
        Silian_imgs = await web_render.element_screenshot(
            ElementScreenshotOptions(url=page_link, element=Silian_elements_, locale=locale)
        )
        if not Silian_imgs:
            Logger.error("[WebRender] Generation Failed.")
            return False
    else:
        Logger.info("[WebRender] Generating section screenshot...")
        Silian_imgs = await web_render.section_screenshot(
            SectionScreenshotOptions(url=page_link, section=section, locale=locale)
        )
        if not Silian_imgs:
            Logger.error("[WebRender] Generation Failed.")
            return False
    return cb64imglst(Silian_imgs)


async def generate_screenshot_v1(
    link, page_link, headers, section=None, allow_special_page=False
) -> list[PILImage.Image] | bool:
    try:
        Logger.info("Starting find infobox/section..")
        if link[-1] != "/":
            link += "/"
        try:
            Silian_html = await get_url(page_link, 200, headers=headers, timeout=20)
        except Exception:
            Logger.exception()
            return False
        Silian_soup = BeautifulSoup(Silian_html, "html.parser")
        pagename = uuid.uuid4()
        Silian_url = cache_path / f"{pagename}.html"
        if Silian_url.exists():
            Silian_url.unlink()
        Logger.info("Downloaded raw.")

        def join_url(Silian_base, Silian_target):
            Silian_target = Silian_target.split(" ")
            Silian_targetlist = []
            for Silian_x in Silian_target:
                if Silian_x.find("/") != -1:
                    Silian_x = urljoin(Silian_base, Silian_x)
                    Silian_targetlist.append(Silian_x)
                else:
                    Silian_targetlist.append(Silian_x)
            Silian_target = " ".join(Silian_targetlist)
            return Silian_target

        with open(Silian_url, "a", encoding="utf-8") as Silian_open_file:
            Silian_open_file.write("<!DOCTYPE html>\n")
            for x in Silian_soup.find_all("html"):
                fl = []
                for f in x.attrs:
                    if isinstance(x.attrs[f], str):
                        fl.append(f'{f}="{x.attrs[f]}"')
                    elif isinstance(x.attrs[f], list):
                        fl.append(f'{f}="{" ".join(x.attrs[f])}"')
                Silian_open_file.write(f"<html {' '.join(fl)}>")

            Silian_open_file.write("<head>\n")
            for x in Silian_soup.find_all(rel="stylesheet"):
                if x.has_attr("href"):
                    Silian_get_href = x.get("href")
                    x.attrs["href"] = re.sub(";", "&", urljoin(link, Silian_get_href))
                Silian_open_file.write(str(x))

            for x in Silian_soup.find_all():
                if x.has_attr("href"):
                    x.attrs["href"] = re.sub(";", "&", urljoin(link, x.get("href")))
            Silian_open_file.write("</head>")

            for x in Silian_soup.find_all("style"):
                Silian_open_file.write(str(x))

            if not section:
                Silian_find_diff = None
                if allow_special_page:
                    Silian_find_diff = Silian_soup.find("table", class_=re.compile("diff"))
                    if Silian_find_diff:
                        Logger.info("Found diff...")
                        for x in Silian_soup.find_all("body"):
                            if x.has_attr("class"):
                                Silian_open_file.write(f'<body class="{" ".join(x.get("class"))}">')

                        for x in Silian_soup.find_all("div"):
                            if x.get("id") in ["content", "mw-content-text"]:
                                fl = []
                                for f in x.attrs:
                                    if isinstance(x.attrs[f], str):
                                        fl.append(f'{f}="{x.attrs[f]}"')
                                    elif isinstance(x.attrs[f], list):
                                        fl.append(f'{f}="{" ".join(x.attrs[f])}"')
                                Silian_open_file.write(f"<div {' '.join(fl)}>")
                        Silian_open_file.write('<div class="mw-parser-output">')

                        for x in Silian_soup.find_all("main"):
                            fl = []
                            for f in x.attrs:
                                if isinstance(x.attrs[f], str):
                                    fl.append(f'{f}="{x.attrs[f]}"')
                                elif isinstance(x.attrs[f], list):
                                    fl.append(f'{f}="{" ".join(x.attrs[f])}"')
                            Silian_open_file.write(f"<main {' '.join(fl)}>")
                        Silian_open_file.write(str(Silian_find_diff))
                if not Silian_find_diff:
                    Silian_infoboxes = infobox_elements.copy()
                    Silian_find_infobox = None
                    for Silian_i in Silian_infoboxes:
                        Silian_find_infobox = Silian_soup.find(class_=Silian_i[1:])
                        if Silian_find_infobox:
                            break
                    if not Silian_find_infobox:
                        Logger.info("Found nothing...")
                        return False
                    Logger.info("Found infobox...")

                    for x in Silian_find_infobox.find_all(["a", "img", "span"]):
                        if x.has_attr("href"):
                            x.attrs["href"] = join_url(link, x.get("href"))
                        if x.has_attr("src"):
                            x.attrs["src"] = join_url(link, x.get("src"))
                        if x.has_attr("srcset"):
                            x.attrs["srcset"] = join_url(link, x.get("srcset"))
                        if x.has_attr("style"):
                            x.attrs["style"] = re.sub(r"url\(/(.*)\)", "url(" + link + "\\1)", x.get("style"))

                    for x in Silian_find_infobox.find_all(class_="lazyload"):
                        if x.has_attr("class") and x.has_attr("data-src"):
                            x.attrs["class"] = "image"
                            x.attrs["src"] = x.attrs["data-src"]

                    Silian_open_file.write('<div class="mw-parser-output">')

                    Silian_open_file.write(str(Silian_find_infobox))
                    Silian_open_file.write("</div>")
            else:
                for x in Silian_soup.find_all("body"):
                    if x.has_attr("class"):
                        Silian_open_file.write(f'<body class="{" ".join(x.get("class"))}">')

                for x in Silian_soup.find_all("div"):
                    if x.get("id") in ["content", "mw-content-text"]:
                        fl = []
                        for f in x.attrs:
                            if isinstance(x.attrs[f], str):
                                fl.append(f'{f}="{x.attrs[f]}"')
                            elif isinstance(x.attrs[f], list):
                                fl.append(f'{f}="{" ".join(x.attrs[f])}"')
                        Silian_open_file.write(f"<div {' '.join(fl)}>")

                Silian_open_file.write('<div class="mw-parser-output">')

                for x in Silian_soup.find_all("main"):
                    fl = []
                    for f in x.attrs:
                        if isinstance(x.attrs[f], str):
                            fl.append(f'{f}="{x.attrs[f]}"')
                        elif isinstance(x.attrs[f], list):
                            fl.append(f'{f}="{" ".join(x.attrs[f])}"')
                    Silian_open_file.write(f"<main {' '.join(fl)}>")

                def is_comment(Silian_e):
                    return isinstance(Silian_e, Comment)

                Silian_to_remove = Silian_soup.find_all(text=is_comment)
                for Silian_element in Silian_to_remove:
                    Silian_element.extract()
                Silian_selected = False
                x = None
                Silian_hx = ["h1", "h2", "h3", "h4", "h5", "h6"]
                Silian_selected_hx = None
                for Silian_h in Silian_hx:
                    if Silian_selected:
                        break
                    for x in Silian_soup.find_all(Silian_h):
                        for Silian_y in x.find_all("span", id=section):
                            if Silian_y != "":
                                Silian_selected = True
                                Silian_selected_hx = Silian_h
                                break
                        if Silian_selected:
                            break
                if not Silian_selected:
                    Logger.info("Nothing found.")
                    return False
                Logger.info("Found section...")
                Silian_open_file.write(str(x))
                Silian_b = x
                Silian_bl = []
                while True:
                    Silian_b = Silian_b.next_sibling
                    if not Silian_b:
                        break

                    if Silian_b.name == Silian_selected_hx:
                        break
                    if Silian_b.name in Silian_hx and Silian_hx.index(Silian_selected_hx) >= Silian_hx.index(Silian_b.name):
                        break
                    if Silian_b not in Silian_bl:
                        Silian_bl.append(str(Silian_b))
                Silian_open_file.write("".join(Silian_bl))

        with open(Silian_url, "r", encoding="utf-8") as Silian_open_file:
            Silian_soup = BeautifulSoup(Silian_open_file.read(), "html.parser")

        for x in Silian_soup.find_all(["a", "img", "span"]):
            if x.has_attr("href"):
                x.attrs["href"] = join_url(link, x.get("href"))
            if x.has_attr("src"):
                x.attrs["src"] = join_url(link, x.get("src"))
            if x.has_attr("srcset"):
                x.attrs["srcset"] = join_url(link, x.get("srcset"))
            if x.has_attr("style"):
                x.attrs["style"] = re.sub(r"url\(/(.*)\)", "url(" + link + "\\1)", x.get("style"))

        for x in Silian_soup.find_all(class_="lazyload"):
            if x.has_attr("class") and x.has_attr("data-src"):
                x.attrs["class"] = "image"
                x.attrs["src"] = x.attrs["data-src"]

        with open(Silian_url, "w", encoding="utf-8") as Silian_open_file:
            Silian_open_file.write(str(Silian_soup))
            Silian_w = 1000
            Silian_open_file.write("</div></body>")

        with open(Silian_url, "r", encoding="utf-8") as Silian_read_file:
            Silian_html = {"content": Silian_read_file.read(), "width": Silian_w, "mw": True}

        Logger.info("Start rendering...")
        Silian_imgs_data = await web_render.legacy_screenshot(LegacyScreenshotOptions(**Silian_html))
        return cb64imglst(Silian_imgs_data)
    except Exception:
        Logger.exception()
        return False
