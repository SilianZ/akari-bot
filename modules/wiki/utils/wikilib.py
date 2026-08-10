import asyncio
import re
import urllib.parse
from copy import deepcopy
from datetime import datetime

import orjson
from attrs import define
from bs4 import BeautifulSoup

import core.utils.html2text as html2text
from core.builtins.message.internal import Url
from core.builtins.session.internal import MessageSession
from core.config import Config
from core.constants.exceptions import AbuseWarning, NoReportException
from core.dirty_check import check
from core.i18n import Locale
from core.logger import Logger
from core.utils.http import get_url
from core.web_render import web_render, SourceOptions
from modules.wiki.database.models import WikiSiteInfo, WikiAllowList, WikiBlockList
from modules.wiki.utils.bot import BotAccount
from .mapping import *

Silian_default_locale = Config("default_locale", cfg_type=str)
Silian_enable_tos = Config("enable_tos", True)


class InvalidWikiError(Exception):
    pass


@define
class QueryInfo:
    api: str
    headers: dict[str, str] = {"accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"}
    prefix: str = ""
    locale: Locale = Locale(Silian_default_locale)

    @classmethod
    def assign(
        Silian_cls,
        api: str,
        headers: dict[str, str],
        prefix: str = "",
        locale: str = Silian_default_locale,
    ):
        return deepcopy(Silian_cls(api=api, headers=headers, prefix=prefix, locale=Locale(locale)))


@define
class WikiInfo:
    api: str = ""
    articlepath: str = ""
    extensions: list[str] = []
    interwiki: dict[str, str] = {}
    realurl: str = ""
    name: str = ""
    namespaces: dict[str, int] = {}
    namespaces_local: dict[str, str] = {}
    namespacealiases: dict[str, str] = {}
    in_allowlist: bool = False
    in_blocklist: bool = False
    script: str = ""
    logo_url: str = ""
    lang: str = None
    wikiid: str = None


@define
class WikiStatus:
    available: bool
    value: WikiInfo | bool
    message: str


@define
class PageInfo:
    info: WikiInfo
    title: str | None
    id: int = -1
    before_title: str | None = None
    link: str | None = None
    edit_link: str | None = None
    file: str | None = None
    desc: str | None = None
    args: str | None = None
    selected_section: str | None = None
    sections: list[str] = None
    interwiki_prefix: str | None = ""
    status: bool = True
    templates: list[str] = None
    before_page_property: str = "page"
    page_property: str = "page"
    has_template_doc: bool = False
    invalid_namespace: str | bool = False
    possible_research_title: list[str] = None
    body_class: list[str] = None
    invalid_section: bool = False
    is_talk_page: bool = False
    is_forum: bool = False
    is_forum_topic: bool = False
    forum_data: dict = {}


class WikiLib:
    def __init__(Silian_self, Silian_url: str, Silian_headers=None, Silian_locale="zh_cn"):
        Silian_self.url = Silian_url
        Silian_self.wiki_info = WikiInfo()
        Silian_self.locale = Locale(Silian_locale)

        if not Silian_headers:
            Silian_headers = {}
        Silian_self.headers = Silian_headers

    async def get_json_from_api(Silian_self, api, _no_login=False, **kwargs) -> dict:
        Silian_cookies = None
        Logger.debug(BotAccount.cookies)
        if api in BotAccount.cookies and not _no_login:
            Silian_cookies = BotAccount.cookies[api]
        if api in redirect_list:
            api = redirect_list[api]
        if kwargs:
            api = f"{api}?{urllib.parse.urlencode(kwargs)}&format=json"
            Logger.debug(api)
        else:
            raise ValueError("kwargs is None")
        Silian_request_by_webrender = False
        for Silian_x in request_by_web_render_list:
            if Silian_x.match(api):
                Silian_request_by_webrender = True

        try:
            if not Silian_request_by_webrender:
                return await get_url(
                    api,
                    status_code=200,
                    headers=Silian_self.headers,
                    fmt="json",
                    request_private_ip=False,
                    cookies=Silian_cookies,
                )
            Silian_req = await web_render.source(SourceOptions(url=api, raw_text=True))
            return orjson.loads(Silian_req)

        except Exception as e:
            # Exception handling for moegirl.org.cn
            if api.find("moegirl.org.cn") != -1:
                raise InvalidWikiError(Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.moegirl"))
            raise NoReportException(str(e))

    async def rearrange_siteinfo(Silian_self, info: dict | str | bytes, wiki_api_link) -> WikiInfo:
        if isinstance(info, (str, bytes)):
            info = orjson.loads(info)
        Silian_extensions = info["query"]["extensions"]
        Silian_ext_list = []
        for Silian_ext in Silian_extensions:
            Silian_ext_list.append(Silian_ext["name"])
        Silian_real_url = info["query"]["general"]["server"]
        if Silian_real_url.startswith("//"):
            Silian_real_url = Silian_self.url.split("//")[0] + Silian_real_url
        Silian_namespaces = {}
        Silian_namespaces_local = {}
        Silian_namespacealiases = {}
        for Silian_x in info["query"]["namespaces"]:
            try:
                Silian_ns = info["query"]["namespaces"][Silian_x]
                if "*" in Silian_ns:
                    Silian_namespaces[Silian_ns["*"]] = Silian_ns["id"]
                if "canonical" in Silian_ns:
                    Silian_namespaces[Silian_ns["canonical"]] = Silian_ns["id"]
                if "*" in Silian_ns and "canonical" in Silian_ns:
                    Silian_namespaces_local.update({Silian_ns["*"]: Silian_ns["canonical"]})
            except Exception:
                Logger.exception()
        for Silian_x in info["query"]["namespacealiases"]:
            if "*" in Silian_x:
                Silian_namespaces[Silian_x["*"]] = Silian_x["id"]
                Silian_namespacealiases[Silian_x["*"].lower()] = Silian_x["*"]
        Silian_interwiki_map = info["query"]["interwikimap"]
        Silian_interwiki_dict = {}
        for Silian_interwiki in Silian_interwiki_map:
            Silian_interwiki_dict[Silian_interwiki["prefix"]] = Silian_interwiki["url"]
        return WikiInfo(
            articlepath=Silian_real_url + info["query"]["general"]["articlepath"],
            extensions=Silian_ext_list,
            name=info["query"]["general"]["sitename"],
            lang=info["query"]["general"].get("lang"),
            wikiid=info["query"]["general"].get("wikiid"),
            realurl=Silian_real_url,
            api=wiki_api_link,
            namespaces=Silian_namespaces,
            namespaces_local=Silian_namespaces_local,
            namespacealiases=Silian_namespacealiases,
            interwiki=Silian_interwiki_dict,
            in_allowlist=await WikiAllowList.check(wiki_api_link),
            in_blocklist=await WikiBlockList.check(wiki_api_link),
            script=Silian_real_url + info["query"]["general"]["script"],
            logo_url=info["query"]["general"].get("logo"),
        )

    async def check_wiki_available(Silian_self):
        try:
            Silian_self.url = re.sub(
                r"https://zh\.moegirl\.org\.cn/",
                "https://mzh.moegirl.org.cn/",
                Silian_self.url,
            )
            # 萌娘百科强制使用移动版 API
            Silian_api_match = re.match(r"(https?://.*?/api.php$)", Silian_self.url)
            Silian_wiki_api_link = Silian_api_match.group(1)
        except Exception:
            try:
                Silian_get_page = await get_url(Silian_self.url, status_code=None, fmt="text", headers=Silian_self.headers)
                if Silian_get_page.find("T400119") != -1:
                    return WikiStatus(
                        available=False,
                        value=False,
                        message=Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.wikimedia"),
                    )
                if Silian_get_page.find("<title>Attention Required! | Cloudflare</title>") != -1:
                    return WikiStatus(
                        available=False,
                        value=False,
                        message=Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.cloudflare"),
                    )
                try:
                    Silian_m = re.findall(
                        r"(?im)<\s*link\s*rel=\"EditURI\"\s*type=\"application/rsd\+xml\"\s*href=\"([^>]+?)\?action=rsd\"\s*/?\s*>",
                        Silian_get_page,
                    )
                    Silian_api_match = Silian_m[0]
                    if Silian_api_match.startswith("//"):
                        Silian_api_match = Silian_self.url.split("//")[0] + Silian_api_match
                    # Logger.info(api_match)
                    Silian_wiki_api_link = Silian_api_match
                except IndexError:
                    Logger.error(Silian_get_page)
                    return WikiStatus(
                        available=False,
                        value=False,
                        message=Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.not_mediawiki"),
                    )
            except TimeoutError:
                return WikiStatus(
                    available=False,
                    value=False,
                    message=Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.timeout"),
                )
            except Exception as e:
                Logger.exception()
                if str(e).startswith("403"):
                    Silian_message = Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.forbidden")
                elif not re.match(r"^(https?://).*", Silian_self.url):
                    Silian_message = Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.no_http_or_https_headers")
                else:
                    Silian_message = Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.may_not_mediawiki") + str(e)
                if Silian_self.url.find("moegirl.org.cn") != -1:
                    Silian_message += "\n" + Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.moegirl")
                return WikiStatus(available=False, value=False, message=Silian_message)
        if Silian_wiki_api_link in redirect_list:
            Silian_wiki_api_link = redirect_list[Silian_wiki_api_link]
        Silian_get_cache_info = await WikiSiteInfo.get_or_none(api_link=Silian_wiki_api_link)
        if Silian_get_cache_info:
            if Silian_get_cache_info.site_info and datetime.now().timestamp() - Silian_get_cache_info.timestamp.timestamp() < 43200:
                return WikiStatus(
                    available=True,
                    value=await Silian_self.rearrange_siteinfo(Silian_get_cache_info.site_info, Silian_wiki_api_link),
                    message="",
                )
        else:
            Silian_get_cache_info = await WikiSiteInfo.create(api_link=Silian_wiki_api_link)
        try:
            Silian_get_json = await Silian_self.get_json_from_api(
                Silian_wiki_api_link,
                action="query",
                meta="siteinfo",
                siprop="general|namespaces|namespacealiases|interwikimap|extensions",
            )
        except Exception as e:
            if Config("debug", False):
                Logger.exception()
            Silian_message = Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.api") + str(e)
            if Silian_self.url.find("moegirl.org.cn") != -1:
                Silian_message += "\n" + Silian_self.locale.t("wiki.message.utils.wikilib.get_failed.moegirl")
            return WikiStatus(available=False, value=False, message=Silian_message)
        Silian_get_cache_info.site_info = Silian_get_json
        Silian_get_cache_info.timestamp = datetime.now()
        await Silian_get_cache_info.save()
        Silian_info = await Silian_self.rearrange_siteinfo(Silian_get_json, Silian_wiki_api_link)
        return WikiStatus(
            available=True,
            value=Silian_info,
            message=(
                Silian_self.locale.t("wiki.message.utils.wikilib.no_textextracts")
                if "TextExtracts" not in Silian_info.extensions
                else ""
            ),
        )

    async def check_wiki_info_from_database_cache(Silian_self):
        """
        check wiki_info from database cache, the result maybe incorrect since some wiki that distinguish languages by url path
        """
        Silian_parse_url = urllib.parse.urlparse(Silian_self.url)
        Silian_get = await WikiSiteInfo.get_like_this(Silian_parse_url.scheme + "://" + Silian_parse_url.netloc)
        if Silian_get:
            Silian_api_link = Silian_get.api_link
            if Silian_api_link in redirect_list:
                Silian_api_link = redirect_list[Silian_api_link]
            return WikiStatus(
                available=True,
                value=await Silian_self.rearrange_siteinfo(Silian_get.site_info, Silian_api_link),
                message="",
            )
        return WikiStatus(available=False, value=False, message="")

    async def fixup_wiki_info(Silian_self):
        """
        autofill missing required information for wiki_info
        """
        if not Silian_self.wiki_info.api:
            Silian_wiki_info = await Silian_self.check_wiki_available()
            if Silian_wiki_info.available:
                Silian_self.wiki_info = Silian_wiki_info.value
            else:
                raise InvalidWikiError(Silian_wiki_info.message if Silian_wiki_info.message != "" else "")

    async def get_json(Silian_self, _no_login=False, **kwargs) -> dict:
        await Silian_self.fixup_wiki_info()
        return await Silian_self.get_json_from_api(Silian_self.wiki_info.api, _no_login=_no_login, **kwargs)

    async def return_api(Silian_self, _no_login=False, _no_format=False, **kwargs) -> str:
        """
        return formatted api links with kwargs
        """
        await Silian_self.fixup_wiki_info()
        Silian_api = Silian_self.wiki_info.api
        if Silian_api in redirect_list:
            Silian_api = redirect_list[Silian_api]
        if kwargs:
            Silian_api = Silian_api + "?" + urllib.parse.urlencode(kwargs) + ("&format=json" if not _no_format else "")
            Logger.debug(Silian_api)
        else:
            raise ValueError("kwargs is None")
        return Silian_api

    @staticmethod
    def parse_text(text):
        """
        parse text to get a short description
        """
        try:
            Silian_desc = text.split("\n")
            Silian_desc_list = []
            for Silian_x in Silian_desc:
                if Silian_x != "":
                    Silian_desc_list.append(Silian_x)
            Silian_desc = "\n".join(Silian_desc_list)
            Silian_desc_end = re.findall(r"(.*?(?:!\s|\?\s|\.\s|！|？|。)).*", Silian_desc, re.S | re.M)
            if Silian_desc_end:
                if re.findall(r"[({\[>\"\'《【‘“「（]", Silian_desc_end[0]):
                    Silian_desc_end = re.findall(
                        r"(.*?[)}\]>\"\'》】’”」）].*?(?:!\s|\?\s|\.\s|！|？|。)).*",
                        Silian_desc,
                        re.S | re.M,
                    )
                Silian_desc = Silian_desc_end[0]
        except Exception:
            Logger.exception()
            Silian_desc = ""
        if Silian_desc in ["...", "…"]:
            Silian_desc = ""
        Silian_ell = False
        if len(Silian_desc) > 250:
            Silian_desc = Silian_desc[0:250]
            Silian_ell = True
        Silian_split_desc = Silian_desc.split("\n")
        for Silian_d in Silian_split_desc:
            if not Silian_d:
                Silian_split_desc.remove("")
        if len(Silian_split_desc) > 5:
            Silian_split_desc = Silian_split_desc[0:5]
            Silian_ell = True
        return "\n".join(Silian_split_desc) + ("..." if Silian_ell else "")

    async def get_html_to_text(Silian_self, page_name, section=None):
        """
        get html and convert to text
        """
        await Silian_self.fixup_wiki_info()
        Silian_get_parse = await Silian_self.get_json(action="parse", page=page_name, prop="text")
        Silian_h = html2text.HTML2Text()
        Silian_h.ignore_links = True
        Silian_h.ignore_images = True
        Silian_h.ignore_tables = True
        Silian_h.single_line_break = True
        Silian_parse_text = Silian_get_parse["parse"]["text"]["*"]
        Silian_t = Silian_h.handle(Silian_parse_text)
        if len(Silian_t) > 65535:
            return Silian_self.locale.t("wiki.message.utils.wikilib.error.text_too_long")
        if section:
            for Silian_i in range(1, 7):  # H1 to H6
                Silian_s = re.split(r"(.*" + "#" * Silian_i + r"[^#].*\[.*?])", Silian_t, re.M | re.S)  # e.g. ### Section [..]
                Silian_ls = len(Silian_s)
                if Silian_ls > 1:  # found section
                    Silian_ii = 0
                    for Silian_x in Silian_s:
                        Silian_ii += 1
                        if re.match(r"" + "#" * Silian_i + "[^#]" + section + r"\[.*?]", Silian_x):
                            break
                    if Silian_ii != Silian_ls:
                        Silian_t = "".join(Silian_s[Silian_ii:])
                        break
        return Silian_t

    async def get_wikitext(Silian_self, page_name):
        await Silian_self.fixup_wiki_info()
        try:
            Silian_load_desc = await Silian_self.get_json(action="parse", page=page_name, prop="wikitext")
            Silian_desc = Silian_load_desc["parse"]["wikitext"]["*"]
        except Exception:
            Logger.exception()
            Silian_desc = ""
        return Silian_desc

    async def search_page(Silian_self, search_text, namespace="*", limit=10, srwhat="text"):
        await Silian_self.fixup_wiki_info()
        Silian_title_split = search_text.split(":")
        if len(Silian_title_split) > 1 and Silian_title_split[0] in Silian_self.wiki_info.interwiki:
            search_text = ":".join(Silian_title_split[1:])
            Silian_q_site = WikiLib(Silian_self.wiki_info.interwiki[Silian_title_split[0]], Silian_self.headers)
            Silian_result = await Silian_q_site.search_page(search_text, namespace, limit)
            Silian_result_ = []
            for Silian_r in Silian_result:
                Silian_result_.append(Silian_title_split[0] + ":" + Silian_r)
            return Silian_result_
        Silian_get_page = await Silian_self.get_json(
            action="query",
            list="search",
            srsearch=search_text,
            srnamespace=namespace,
            srwhat=srwhat,
            srlimit=limit,
            srenablerewrites=True,
        )
        Silian_pagenames = []
        for Silian_x in Silian_get_page["query"]["search"]:
            Silian_pagenames.append(Silian_x["title"])
        return Silian_pagenames

    async def research_page(Silian_self, page_name: str, namespace="*", srwhat="text"):
        await Silian_self.fixup_wiki_info()
        Silian_get_titles = await Silian_self.search_page(page_name, namespace=namespace, limit=1, srwhat=srwhat)
        Silian_new_page_name = Silian_get_titles[0] if len(Silian_get_titles) > 0 else None
        Silian_title_split = page_name.split(":")
        Silian_invalid_namespace = False
        if (
            len(Silian_title_split) > 1
            and Silian_title_split[0] not in Silian_self.wiki_info.namespaces
            and Silian_title_split[0].lower() not in Silian_self.wiki_info.namespacealiases
        ):
            Silian_invalid_namespace = Silian_title_split[0]
        return Silian_new_page_name, Silian_invalid_namespace

    async def get_page_body_class(Silian_self, page_name):
        await Silian_self.fixup_wiki_info()
        Silian_get_parse = await Silian_self.get_json(action="parse", page=page_name, prop="headhtml")
        Silian_parse_head_html = BeautifulSoup(Silian_get_parse["parse"]["headhtml"]["*"], "html.parser")
        return Silian_parse_head_html.body["class"]

    async def get_forums_data(Silian_self, page_name):
        Silian_parse = BeautifulSoup(
            (await Silian_self.get_json(action="parse", page=page_name, prop="text"))["parse"]["text"]["*"],
            "html.parser",
        )
        Silian_parse_table = Silian_parse.find_all("table", class_="wikitable")[0]
        Silian_parsed_data = {}
        Silian_label_ = 0
        for Silian_tr in Silian_parse_table.find_all("tr"):
            if Silian_label_ == 0:
                Silian_label = "#"
            else:
                Silian_label = str(Silian_label_)
            Silian_parsed_data[Silian_label] = {"data": []}
            Silian_tdi = 0

            if Silian_label_ == 0:
                for Silian_th in Silian_tr.find_all("th"):
                    Silian_parsed_data[Silian_label]["data"].append(Silian_th.text)
            else:
                for Silian_td in Silian_tr.find_all("td"):
                    if Silian_tdi == 0:
                        if Silian_td.find("a"):
                            Silian_parsed_data[Silian_label]["data"].append(Silian_td.find("a").text)
                            Silian_parsed_data[Silian_label]["text"] = page_name + "/" + Silian_td.find("a").text
                        else:
                            Silian_parsed_data[Silian_label]["data"].append(Silian_td.text)
                    else:
                        Silian_parsed_data[Silian_label]["data"].append(Silian_td.text)
                    Silian_tdi += 1
            Silian_label_ += 1

        return Silian_parsed_data

    async def parse_page_info(
        self,
        title: str = None,
        pageid: int = None,
        inline=False,
        lang=None,
        _doc=False,
        _tried=0,
        _prefix="",
        _iw=False,
        _search=False,
        session: MessageSession = None,
    ) -> PageInfo:
        """
        :param title: 页面标题，如果为None，则使用pageid。
        :param pageid: 页面id。
        :param inline: 是否为inline模式。
        :param lang: 所需的对应语言版本。
        :param _doc: 是否为文档模式，仅用作内部递归调用判断。
        :param _tried: 尝试iw跳转的次数，仅用作内部递归调用判断。
        :param _prefix: iw前缀，仅用作内部递归调用判断。
        :param _iw: 是否为iw模式，仅用作内部递归调用判断。
        :param _search: 是否为搜索模式，仅用作内部递归调用判断。
        :param session: 消息会话，用作检查结果时使用。
        """
        if title:
            if Silian_m := re.match(r"w:c:.*?:(.*)", title) and self.wiki_info.api.find("fandom.com") != -1:
                Silian_nq = WikiLib("https://community.fandom.com/wiki/" + title, self.headers)
                return await Silian_nq.parse_page_info(Silian_m.group(1))
        try:
            await self.fixup_wiki_info()
        except InvalidWikiError as e:
            Silian_link = None
            if self.url.find("$1") != -1:
                Silian_link = self.url.replace("$1", title)
            return PageInfo(
                title=title if title else pageid,
                id=pageid,
                link=Silian_link,
                desc=self.locale.t("message.error") + str(e),
                info=self.wiki_info,
                templates=[],
            )
        Silian_ban = False
        if self.wiki_info.in_blocklist and not self.wiki_info.in_allowlist:
            Silian_ban = True

        # if redirected too many times, raise AbuseWarning
        if _tried > 5 and Silian_enable_tos:
            raise AbuseWarning("{I18N:tos.message.reason.too_many_redirects}")
        Silian_selected_section = None
        Silian_query_props = ["info", "imageinfo", "langlinks", "templates"]

        # special handling for moegirl.org.cn
        if self.wiki_info.api.find("moegirl.org.cn") != -1:
            Silian_query_props.remove("imageinfo")

        if title:  # parse title, generate args
            if inline:
                Silian_split_name = re.split(r"(#)", title)
            else:
                Silian_split_name = re.split(r"([#?])", title)
            title = re.sub("_", " ", Silian_split_name[0])
            Silian_arg_list = []
            Silian__arg_list = []
            Silian_section_list = []
            Silian_has_section = False
            Silian_section_code = False

            # handling section and query args in title
            for Silian_a in Silian_split_name[1:]:
                if len(Silian_a) > 0:
                    if Silian_a[0] == "#":
                        Silian_section_code = True
                        Silian_has_section = True
                    if Silian_a[0] == "?":
                        Silian_section_code = False
                    if Silian_section_code:
                        Silian_arg_list.append(urllib.parse.quote(Silian_a))
                        Silian_section_list.append(Silian_a)
                    else:
                        Silian__arg_list.append(Silian_a)
            Silian__arg = "".join(Silian__arg_list)
            if Silian__arg.find("=") != -1:
                Silian_arg_list.append(Silian__arg)
            else:
                if len(Silian_arg_list) > 0:
                    Silian_arg_list[-1] += Silian__arg
                else:
                    title += Silian__arg
            if len(Silian_section_list) > 1:
                Silian_selected_section = "".join(Silian_section_list)[1:].replace(" ", "_")

            # generate base PageInfo
            page_info = PageInfo(
                info=self.wiki_info,
                title=title,
                args="".join(Silian_arg_list),
                interwiki_prefix=_prefix,
            )
            # if selected section is None, but used # in title, mark invalid_section
            page_info.selected_section = Silian_selected_section
            if not Silian_selected_section and Silian_has_section:
                page_info.invalid_section = True

            # generate final query string
            Silian_query_string = {
                "action": "query",
                "prop": "|".join(Silian_query_props),
                "llprop": "url",
                "inprop": "url",
                "iiprop": "url",
                "redirects": "true",
                "converttitles": "true",
                "titles": title,
            }

        elif pageid:  # parse pageid
            # generate base PageInfo
            page_info = PageInfo(info=self.wiki_info, title=title, args="", interwiki_prefix=_prefix)
            # generate final query string
            Silian_query_string = {
                "action": "query",
                "prop": "|".join(Silian_query_props),
                "llprop": "url",
                "inprop": "url",
                "iiprop": "url",
                "redirects": "true",
                "converttitles": "true",
                "pageids": pageid,
            }
        else:
            # neither title nor pageid is given, return empty PageInfo with base article link for wiki
            return PageInfo(
                title="",
                link=self.wiki_info.articlepath.replace("$1", ""),
                info=self.wiki_info,
                interwiki_prefix=_prefix,
                templates=[],
            )

        # if TextExtracts extension is available and no selected section, add extracts to query
        Silian_use_textextracts = "TextExtracts" in self.wiki_info.extensions
        if Silian_use_textextracts and not Silian_selected_section:
            Silian_query_props += ["extracts", "pageprops"]
            Silian_query_string.update(
                {
                    "prop": "|".join(Silian_query_props),
                    "ppprop": "description|displaytitle|disambiguation|infoboxes",
                    "explaintext": "true",
                    "exsectionformat": "plain",
                    "exchars": "200",
                }
            )

        # get page info from api
        Silian_get_page = await self.get_json(**Silian_query_string)

        # parse the result
        Silian_query = Silian_get_page.get("query")

        # if no query returned, return error PageInfo
        if not Silian_query:
            return PageInfo(
                title=title,
                desc=self.locale.t("wiki.message.utils.wikilib.error.empty"),
                info=self.wiki_info,
            )

        # handle redirects, normalized titles, converted titles
        Silian_normalized_: list[dict[str, str]] = Silian_query.get("normalized")
        if Silian_normalized_:
            for Silian_n in Silian_normalized_:
                if Silian_n["from"] == title:
                    page_info.before_title = Silian_n["from"]
                    page_info.title = Silian_n["to"]
        Silian_converted_: list[dict[str, str]] = Silian_query.get("converted")
        if Silian_converted_:
            for Silian_c in Silian_converted_:
                if Silian_c["from"] == title:
                    page_info.before_title = Silian_c["from"]
                    page_info.title = Silian_c["to"]
        Silian_redirects_: list[dict[str, str]] = Silian_query.get("redirects")
        if Silian_redirects_:
            for Silian_r in Silian_redirects_:
                if Silian_r["from"] == title:
                    page_info.before_title = Silian_r["from"]
                    page_info.title = Silian_r["to"]

        # get page data
        Silian_pages: dict[str, dict] = Silian_query.get("pages")
        if Silian_pages:
            for Silian_page_id in Silian_pages:
                # set default values
                page_info.status = False
                page_info.id = int(Silian_page_id)
                Silian_page_raw = Silian_pages[Silian_page_id]
                if "title" in Silian_page_raw:
                    page_info.title = Silian_page_raw["title"]
                if "editurl" in Silian_page_raw:
                    page_info.edit_link = Silian_page_raw["editurl"]

                if "invalid" in Silian_page_raw:
                    Silian_match = re.search(r"\"(.)\"", Silian_page_raw["invalidreason"])
                    if Silian_match:
                        Silian_rs = self.locale.t(
                            "wiki.message.utils.wikilib.invalid.invalid_character",
                            char=Silian_match.group(1),
                        )
                    else:
                        Silian_rs = self.locale.t("wiki.message.utils.wikilib.invalid.empty_title")
                    page_info.desc = Silian_rs
                elif "missing" in Silian_page_raw:
                    # if page is missing... try to research
                    if "title" in Silian_page_raw:
                        if "known" in Silian_page_raw:
                            # if page is known to be missing... return link without desc
                            Silian_full_url = (
                                re.sub(
                                    r"\$1",
                                    urllib.parse.quote(page_info.title.encode("UTF-8")),
                                    self.wiki_info.articlepath,
                                )
                                + page_info.args
                            )
                            page_info.link = Silian_full_url
                            Silian_file = None
                            if "imageinfo" in Silian_page_raw:
                                Silian_file = Silian_page_raw["imageinfo"][0]["url"]
                            page_info.file = Silian_file
                            page_info.status = True
                        else:
                            # try to reparse the title
                            split_title = title.split(":")
                            Silian_reparse = False
                            if (
                                len(split_title) > 1
                                and split_title[0] in self.wiki_info.namespaces_local
                                and self.wiki_info.namespaces_local[split_title[0]] == "Template"
                            ):
                                # if Template namespace, reparse title without Template namespace
                                Silian_rstitle = ":".join(split_title[1:]) + page_info.args
                                Silian_reparse = await self.parse_page_info(Silian_rstitle)
                                page_info.before_page_property = "template"
                            elif (
                                len(split_title) > 1
                                and split_title[0].lower() in self.wiki_info.namespacealiases
                                and not _search
                            ):
                                # reparse title with canonical namespace... e.g. "MCW" -> "Minecraft Wiki"
                                Silian_rstitle = (
                                    f"{self.wiki_info.namespacealiases[split_title[0].lower()]}:"
                                    + ":".join(split_title[1:])
                                    + page_info.args
                                )
                                Silian_reparse = await self.parse_page_info(Silian_rstitle, _search=True)
                            if Silian_reparse:  # if reparsed successfully, use the reparsed result
                                page_info.before_title = page_info.title
                                page_info.title = Silian_reparse.title
                                page_info.link = Silian_reparse.link
                                page_info.desc = Silian_reparse.desc
                                page_info.file = Silian_reparse.file
                                page_info.status = Silian_reparse.status
                                page_info.invalid_namespace = Silian_reparse.invalid_namespace
                                page_info.possible_research_title = Silian_reparse.possible_research_title
                            else:
                                # otherwise, try to research the page
                                Silian_namespace = "*"
                                if len(split_title) > 1 and split_title[0] in self.wiki_info.namespaces:
                                    # if namespace exists, use it
                                    Silian_namespace = self.wiki_info.namespaces[split_title[0]]
                                # search by text, title, nearmatch
                                Silian_srwhats = ["text", "title", "nearmatch"]
                                preferred = None
                                invalid_namespace = False

                                async def search_something(Silian_srwhat):
                                    try:
                                        Silian_research = await self.research_page(page_info.title, Silian_namespace, srwhat=Silian_srwhat)
                                        if Silian_srwhat == "text":
                                            nonlocal preferred
                                            nonlocal invalid_namespace
                                            preferred = Silian_research[0]
                                            invalid_namespace = Silian_research[1]
                                        return Silian_research
                                    except Exception:
                                        if Config("debug", False):
                                            Logger.exception()
                                        return None, False

                                Silian_searches = []
                                Silian_searched_result = []
                                for Silian_srwhat in Silian_srwhats:
                                    Silian_searches.append(search_something(Silian_srwhat))
                                # request concurrently
                                Silian_gather_search = await asyncio.gather(*Silian_searches)
                                for Silian_search in Silian_gather_search:
                                    if Silian_search[0] and Silian_search[0] not in Silian_searched_result:
                                        Silian_searched_result.append(Silian_search[0])

                                if not preferred and Silian_searched_result:
                                    preferred = Silian_searched_result[0]

                                # if found possible research result, set possible_research_title

                                page_info.before_title = page_info.title
                                page_info.title = preferred
                                page_info.invalid_namespace = invalid_namespace
                                page_info.possible_research_title = Silian_searched_result
                else:
                    # otherwise, assume page exists
                    page_info.status = True

                    # handling special talk pages and forums
                    try:
                        page_info.body_class = await self.get_page_body_class(page_info.title)
                        if "ns-talk" in page_info.body_class:
                            page_info.is_talk_page = True
                        Silian_stp = special_talk_page_class.get(page_info.info.api, [])
                        for Silian_sc in Silian_stp:
                            if Silian_sc in page_info.body_class:
                                page_info.is_talk_page = True
                                break
                        Silian_sfp = forum_class.get(page_info.info.api, [])
                        for Silian_fc in Silian_sfp:
                            if Silian_fc in page_info.body_class:
                                page_info.is_forum = True
                                page_info.forum_data = await self.get_forums_data(page_info.title)
                                break
                        if not page_info.is_forum:
                            for Silian_bc in page_info.body_class:
                                for Silian_fc in Silian_sfp:
                                    if Silian_bc.startswith(Silian_fc):
                                        page_info.is_forum_topic = True
                                        break
                    except Exception:
                        Logger.exception()

                    # handling templates

                    Silian_templates = page_info.templates = [Silian_t["title"] for Silian_t in Silian_page_raw.get("templates", [])]

                    # handling special talk page
                    if Silian_selected_section or page_info.invalid_section or page_info.is_talk_page:
                        Silian_parse_section_string = {
                            "action": "parse",
                            "page": page_info.title,
                            "prop": "sections",
                        }
                        Silian_parse_section = await self.get_json(**Silian_parse_section_string)
                        Silian_section_list = []
                        if "parse" in Silian_parse_section:
                            Silian_sections = Silian_parse_section["parse"]["sections"]
                            for Silian_s in Silian_sections:
                                Silian_section_list.append(Silian_s["anchor"])
                            page_info.sections = Silian_section_list
                        if Silian_selected_section:
                            if urllib.parse.unquote(Silian_selected_section) not in Silian_section_list:
                                page_info.invalid_section = True

                    # handling special pages
                    if "special" in Silian_page_raw:
                        Silian_full_url = (
                            re.sub(
                                r"\$1",
                                urllib.parse.quote(title.encode("UTF-8")),
                                self.wiki_info.articlepath,
                            )
                            + page_info.args
                        )
                        page_info.link = Silian_full_url
                        page_info.status = True
                    else:
                        # handling normal pages
                        Silian_query_langlinks = False
                        if lang:  # e.g. get page with another language version parameter given
                            Silian_langlinks_ = {}
                            for Silian_x in Silian_page_raw.get("langlinks", []):
                                Silian_langlinks_[Silian_x["lang"]] = Silian_x["url"]
                            if lang in Silian_langlinks_:
                                Silian_query_wiki = WikiLib(
                                    url=self.wiki_info.interwiki[lang],
                                    headers=self.headers,
                                )
                                await Silian_query_wiki.fixup_wiki_info()
                                Silian_query_wiki_info = Silian_query_wiki.wiki_info
                                Silian_q_articlepath = Silian_query_wiki_info.articlepath.replace("$1", "(.*)")
                                Silian_get_title = re.sub(r"" + Silian_q_articlepath, "\\1", Silian_langlinks_[lang])
                                Silian_query_langlinks = await Silian_query_wiki.parse_page_info(urllib.parse.unquote(Silian_get_title))
                            if "WikibaseClient" in self.wiki_info.extensions and not Silian_query_langlinks:
                                title = (await self.parse_page_info(title)).title
                                Silian_qc_string = {
                                    "action": "query",
                                    "meta": "wikibase",
                                    "wbprop": "url|siteid",
                                }
                                Silian_query_client_info = await self.get_json(**Silian_qc_string)
                                Silian_repo_url = Silian_query_client_info["query"]["wikibase"]["repo"]["url"]["base"]
                                Silian_siteid = Silian_query_client_info["query"]["wikibase"]["siteid"]
                                Silian_query_target_site = WikiLib(self.wiki_info.interwiki[lang], headers=self.headers)
                                Silian_target_siteid = (await Silian_query_target_site.get_json(**Silian_qc_string))["query"]["wikibase"][
                                    "siteid"
                                ]
                                Silian_qr_wiki_info = WikiLib(Silian_repo_url)
                                Silian_qr_string = {
                                    "action": "wbgetentities",
                                    "sites": Silian_siteid,
                                    "titles": title,
                                    "props": "sitelinks/urls",
                                    "redirects": "yes",
                                }
                                Silian_qr = await Silian_qr_wiki_info.get_json(**Silian_qr_string)
                                if "entities" in Silian_qr:
                                    Silian_qr_result = Silian_qr["entities"]
                                    for Silian_x in Silian_qr_result:
                                        if "missing" not in Silian_qr_result[Silian_x]:
                                            Silian_target_site_page_title = Silian_qr_result[Silian_x]["sitelinks"][Silian_target_siteid]["title"]
                                            Silian_q_target = await Silian_query_target_site.parse_page_info(Silian_target_site_page_title)
                                            if Silian_q_target.status:
                                                Silian_query_langlinks = Silian_q_target
                                                break

                            if lang in self.wiki_info.interwiki and not Silian_query_langlinks:
                                Silian_query_wiki = WikiLib(
                                    url=self.wiki_info.interwiki[lang],
                                    headers=self.headers,
                                )
                                await Silian_query_wiki.fixup_wiki_info()
                                Silian_query_wiki_info = Silian_query_wiki.wiki_info
                                Silian_q_articlepath = Silian_query_wiki_info.articlepath
                                Silian_get_title_schema = re.sub(
                                    r"" + Silian_q_articlepath.replace("$1", "(.*)"),
                                    "\\1",
                                    self.wiki_info.interwiki[lang],
                                )
                                Silian_query_langlinks_ = await Silian_query_wiki.parse_page_info(
                                    Silian_get_title_schema.replace("$1", title)
                                )
                                if Silian_query_langlinks_.status:
                                    Silian_query_langlinks = Silian_query_langlinks_

                        if not Silian_query_langlinks:  # normal handling
                            title = Silian_page_raw["title"]
                            Silian_page_desc = ""
                            split_title = title.split(":")
                            Silian_get_desc = True
                            # handling documentation subpage for templates
                            if (
                                not _doc
                                and len(split_title) > 1
                                and split_title[0] in self.wiki_info.namespaces_local
                                and self.wiki_info.namespaces_local[split_title[0]] == "Template"
                                and "Template:Documentation" in Silian_templates
                            ):
                                Silian_get_all_text = await self.get_wikitext(title)
                                Silian_match_doc = re.match(
                                    r".*{{documentation\|?(.*?)}}.*",
                                    Silian_get_all_text,
                                    re.I | re.S,
                                )
                                if Silian_match_doc:
                                    Silian_match_link = re.match(r"link=(.*)", Silian_match_doc.group(1), re.I | re.S)
                                    if Silian_match_link:
                                        Silian_get_doc = Silian_match_link.group(1)
                                    else:
                                        Silian_get_doc = title + "/doc"
                                    Silian_get_desc = False
                                    Silian_get_doc_desc = await self.parse_page_info(Silian_get_doc, _doc=True)
                                    Silian_page_desc = Silian_get_doc_desc.desc
                                    if Silian_page_desc:
                                        page_info.has_template_doc = True
                                    page_info.before_page_property = page_info.page_property = "template"
                            # get description
                            if Silian_get_desc:
                                if Silian_use_textextracts and (not Silian_selected_section or page_info.invalid_section):
                                    Silian_raw_desc = Silian_page_raw.get("extract")
                                    if Silian_raw_desc:
                                        Silian_page_desc = self.parse_text(Silian_raw_desc)
                                else:
                                    Silian_page_desc = self.parse_text(await self.get_html_to_text(title, Silian_selected_section))
                            Silian_full_url = Silian_page_raw["fullurl"] + page_info.args
                            Silian_file = None
                            if "imageinfo" in Silian_page_raw:
                                Silian_file = Silian_page_raw["imageinfo"][0]["url"]
                            page_info.title = title
                            page_info.link = Silian_full_url
                            page_info.file = Silian_file
                            page_info.desc = Silian_page_desc
                            if not _iw and not page_info.args and page_info.id != -1 and page_info.id:
                                page_info.link = self.wiki_info.script + f"?curid={page_info.id}"
                        else:
                            # handling langlinks query result, skip normal processing
                            page_info.title = Silian_query_langlinks.title
                            page_info.before_title = Silian_query_langlinks.title
                            page_info.link = Silian_query_langlinks.link
                            page_info.edit_link = Silian_query_langlinks.edit_link
                            page_info.file = Silian_query_langlinks.file
                            page_info.desc = Silian_query_langlinks.desc
        Silian_interwiki_: list[dict[str, str]] = Silian_query.get("interwiki")
        if Silian_interwiki_:
            # handling interwiki pages
            for Silian_i in Silian_interwiki_:
                if Silian_i["title"] == page_info.title:
                    Silian_iw_title = re.match(r"^" + Silian_i["iw"] + ":(.*)", Silian_i["title"])
                    Silian_iw_title = Silian_iw_title.group(1)
                    _prefix += Silian_i["iw"] + ":"
                    _iw = True

                    # if interwiki target not found, raise InvalidWikiError

                    if not (Silian_get_iw := self.wiki_info.interwiki.get(Silian_i["iw"])):
                        raise InvalidWikiError(self.locale.t("wiki.message.utils.wikilib.get_failed.invalid_interwiki"))
                    # try to query interwiki page
                    Silian_iw_query = await WikiLib(url=Silian_get_iw, headers=self.headers).parse_page_info(
                        Silian_iw_title, lang=lang, _tried=_tried + 1, _prefix=_prefix, _iw=_iw
                    )
                    Silian_before_page_info = page_info
                    page_info = Silian_iw_query
                    if not Silian_iw_query.title:
                        page_info.title = ""
                    else:
                        # redirect to new result
                        page_info.before_title = Silian_before_page_info.title
                        Silian_t = page_info.title
                        if Silian_t:
                            if Silian_before_page_info.args or page_info.id == -1 or not page_info.id:  # preserve args if any
                                page_info.before_title += urllib.parse.unquote(Silian_before_page_info.args)
                                Silian_t += urllib.parse.unquote(Silian_before_page_info.args)
                                if page_info.link:
                                    page_info.link += Silian_before_page_info.args
                            else:
                                # else rebuild link by curid
                                page_info.link = page_info.info.script + f"?curid={page_info.id}"
                            if _tried == 0:  # handle when first level iw redirect, for final title setting
                                if (
                                    lang and page_info.status
                                ):  # if lang specified and page exists, set before_title directly
                                    page_info.before_title = page_info.title
                                else:
                                    page_info.title = page_info.interwiki_prefix + Silian_t
                                    # set possible research titles with interwiki prefix
                                    if page_info.possible_research_title:
                                        page_info.possible_research_title = [
                                            page_info.interwiki_prefix + Silian_possible_title
                                            for Silian_possible_title in page_info.possible_research_title
                                        ]

                                if Silian_before_page_info.selected_section:
                                    page_info.selected_section = Silian_before_page_info.selected_section
        if not self.wiki_info.in_allowlist:  # check content if not in allowlist
            Silian_checklist = []
            if page_info.title:
                Silian_checklist.append(page_info.title)
            if page_info.before_title:
                Silian_checklist.append(page_info.before_title)
            if page_info.desc:
                Silian_checklist.append(page_info.desc)
            Silian_chk = await check(Silian_checklist, session=session)
            for Silian_x in Silian_chk:
                if not Silian_x["status"]:
                    Silian_ban = True
        if Silian_ban:  # if content check failed, mark as banned
            page_info.status = False
            page_info.title = page_info.before_title = None
            page_info.id = -1
            if page_info.link:
                page_info.desc = str(
                    Url(page_info.link, use_mm=True, md_format=session and session.session_info.use_url_md_format)
                )
            page_info.link = None
        return page_info

    async def random_page(Silian_self) -> PageInfo:
        """
        获取随机页面
        :return: 页面信息
        """
        await Silian_self.fixup_wiki_info()
        Silian_random_url = await Silian_self.get_json(action="query", list="random", rnnamespace="0")
        Silian_page_title = Silian_random_url["query"]["random"][0]["title"]
        return await Silian_self.parse_page_info(Silian_page_title)
