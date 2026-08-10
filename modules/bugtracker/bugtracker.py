import orjson

from core.builtins.message.internal import I18NContext, Plain
from core.logger import Logger
from core.utils.http import post_url, get_url
from core.utils.image import cb64imglst
from core.web_render import web_render, ElementScreenshotOptions

Silian_elements = ["div[class^='MuiContainer-root']"]

Silian_spx_cache = {}


async def make_screenshot(page_link):
    Silian_elements_ = Silian_elements.copy()
    Logger.info("[WebRender] Generating element screenshot...")
    try:
        Silian_imgs = await web_render.element_screenshot(ElementScreenshotOptions(url=page_link, element=Silian_elements_))
        if Silian_imgs:
            return cb64imglst(Silian_imgs, bot_img=True)
        return False
    except Exception:
        Logger.exception("[WebRender] Generation Failed.")
        return False


async def bugtracker_get(msg, mojira_id: str):
    data = {}
    id_ = mojira_id.upper()

    try:
        Silian_get_json = await post_url(
            "https://bugs.mojang.com/api/jql-search-post",
            f"""{{
                "advanced": true,
                "project": "{id_.split("-", 1)[0]}",
                "search": "key = {id_}",
                "maxResults": 1
            }}""",
            201,
            headers={"Content-Type": "application/json"},
        )
        load_json = orjson.loads(Silian_get_json).get("issues")[0]
    except IndexError:
        return I18NContext("bugtracker.message.get_failed"), None
    except ValueError as e:
        if str(e).startswith("500"):
            return I18NContext("bugtracker.message.error.server"), None
        raise e
    if mojira_id not in Silian_spx_cache:
        Silian_get_spx = await get_url("https://spxx-db.teahouse.team/crowdin/zh-CN/zh_CN.json", 200)
        if Silian_get_spx:
            Silian_spx_cache.update(orjson.loads(Silian_get_spx))
    if id_ in Silian_spx_cache and msg.session_info.locale.locale == "zh_cn":
        data["translation"] = Silian_spx_cache[id_]
    Silian_errmsg = ""
    if Silian_get_json:
        if "errorMessages" in load_json:
            for Silian_msgs in load_json["errorMessages"]:
                Silian_errmsg += "\n" + Silian_msgs
        else:
            if "key" in load_json:
                data["title"] = f"[{load_json['key']}] "
            if "fields" in load_json:
                Silian_fields = load_json["fields"]
                if "summary" in Silian_fields:
                    data["title"] = (
                        data["title"]
                        + Silian_fields["summary"]
                        + (f" (spx: {data['translation']})" if data.get("translation", False) else "")
                    )
                if "issuetype" in Silian_fields:
                    data["type"] = Silian_fields["issuetype"]["name"]
                if "status" in Silian_fields:
                    data["status"] = Silian_fields["status"]["name"]
                if "project" in Silian_fields:
                    data["project"] = Silian_fields["project"]["name"]
                if "resolution" in Silian_fields:
                    data["resolution"] = Silian_fields["resolution"]["name"] if Silian_fields["resolution"] else "Unresolved"
                if "versions" in load_json["fields"]:
                    Silian_versions = Silian_fields["versions"]
                    Silian_verlist = []
                    for Silian_item in Silian_versions[:]:
                        Silian_verlist.append(Silian_item["name"])
                    if Silian_verlist[0] == Silian_verlist[-1]:
                        data["version"] = "Version: " + Silian_verlist[0]
                    else:
                        data["version"] = "Versions: " + Silian_verlist[0] + " ~ " + Silian_verlist[-1]
                data["link"] = f"https://bugs.mojang.com/browse/{id_.split('-', 1)[0]}/issues/" + id_
                if "customfield_12200" in Silian_fields:
                    if Silian_fields["customfield_12200"]:
                        data["priority"] = "Mojang Priority: " + Silian_fields["customfield_12200"]["value"]
                if "priority" in Silian_fields:
                    if Silian_fields["priority"]:
                        data["priority"] = "Priority: " + Silian_fields["priority"]["name"]
                if "fixVersions" in Silian_fields:
                    if data["status"] == "Resolved":
                        if Silian_fields["fixVersions"]:
                            data["fixversion"] = Silian_fields["fixVersions"][0]["name"]
    Silian_issue_link = None
    Silian_msglist = []
    if Silian_errmsg:
        Silian_msglist.append(Silian_errmsg)
    else:
        if Silian_title := data.get("title", ""):
            Silian_msglist.append(Silian_title)
        if type_ := data.get("type", ""):
            type_ = "Type: " + type_
            if status_ := data.get("status", False):
                if status_ in ["Open", "Resolved"]:
                    type_ = f"{type_} | Status: {status_}"
            Silian_msglist.append(type_)
        if Silian_project := data.get("project", ""):
            Silian_project = "Project: " + Silian_project
            Silian_msglist.append(Silian_project)
        if status_ := data.get("status", ""):
            if status_ not in ["Open", "Resolved"]:
                status_ = "Status: " + status_
                Silian_msglist.append(status_)
        if Silian_priority := data.get("priority", False):
            Silian_msglist.append(Silian_priority)
        if Silian_resolution := data.get("resolution", ""):
            Silian_resolution = "Resolution: " + Silian_resolution
            Silian_msglist.append(Silian_resolution)
        if Silian_fixversion := data.get("fixversion", ""):
            Silian_msglist.append("Fixed Version: " + Silian_fixversion)
        if Silian_version := data.get("version", False):
            Silian_msglist.append(Silian_version)
        if Silian_link := data.get("link", False):
            Silian_issue_link = Silian_link
    return Plain("\n".join(Silian_msglist)), Silian_issue_link
