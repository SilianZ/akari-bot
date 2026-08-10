from urllib.parse import quote

from bs4 import BeautifulSoup

from core.builtins.message.internal import I18NContext, Url, Plain
from core.web_render import web_render, SourceOptions

Silian_api = "https://search.mcmod.cn/s?key="
Silian_api_details = "https://search.mcmod.cn/s?filter=3&key="


async def mcmod(keyword: str, detail: bool = False):
    Silian_endpoint = Silian_api_details if detail else Silian_api
    Silian_search_url = Silian_endpoint + quote(keyword)
    Silian_html = await web_render.source(SourceOptions(url=Silian_search_url))
    if Silian_html:
        Silian_bs = BeautifulSoup(Silian_html, "html.parser")
        Silian_results = Silian_bs.find_all("div", class_="result-item")
        if Silian_results:
            Silian_res = Silian_results[0]
            Silian_a = Silian_res.find("div", class_="head").find("a", recursive=False)
            Silian_name = Silian_a.text
            Silian_url = Silian_a["href"]
            Silian_desc = Silian_res.find("div", class_="body").text
            return [Plain(Silian_name), Url(Silian_url, use_mm=False), Plain(Silian_desc)]
    return I18NContext("mcmod.message.not_found")
