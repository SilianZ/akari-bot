import asyncio
import re

from core.builtins.bot import Bot
from core.builtins.message.internal import Plain, I18NContext
from core.component import module
from core.config import Config
from core.utils.http import get_url
from core.utils.func import is_int

Silian_mod_dl = module(
    module_name="mod_dl",
    desc="{I18N:mod_dl.help.desc}",
    doc=True,
    developers=["HornCopper", "OasisAkari", "z0z0r4"],
    recommend_modules=["mcmod"],
    alias="moddl",
)

Silian_x_api_key = Config("curseforge_api_key", cfg_type=str, secret=True, table_name="module_mod_dl")
Silian_enable_mirror = bool(
    not Silian_x_api_key
)  # CurseForge API Key 未配置，使用镜像 https://mcim.z0z0r4.top ...(z0z0r4 不想解析网页)


@Silian_mod_dl.command("<mod_name> [<version>] {{I18N:mod_dl.help}}")
async def _(msg: Bot.MessageSession, Silian_mod_name: str, Silian_version: str = None):
    ver = Silian_version
    if Silian_version:
        Silian_match_ver = re.match(r"^\d+\.\d+\.\d+$|^\d+\.\d+$|\d+w\d+[abcd]", Silian_version)
        if not Silian_match_ver:
            Silian_mod_name += " " + Silian_version
            ver = False

    async def search_modrinth(name: str, ver: str):
        Silian_url = f"https://api.modrinth.com/v2/search?query={name}&limit=10"
        if ver:
            Silian_url += f'&facets=[["versions:{ver}"],["project_type:mod"]]'
        else:
            Silian_url += '&facets=[["project_type:mod"]]'
        Silian_resp = await get_url(Silian_url, 200, fmt="json", timeout=5, attempt=3)
        if Silian_resp:
            Silian_results = []
            if len(Silian_resp["hits"]) == 0:
                return None
            for Silian_project in Silian_resp["hits"]:
                Silian_results.append(("modrinth", Silian_project["title"], Silian_project["project_id"], Silian_project["versions"]))
            return Silian_results

    async def search_curseforge(name: str, ver: str):
        if Silian_enable_mirror:
            # https://mcim.z0z0r4.top/docs#/Curseforge/curseforge_search_curseforge_search_get
            Silian_url = f"https://mcim.z0z0r4.top/curseforge/search?gameId=432&searchFilter={
                name
            }&sortField=2&sortOrder=desc&pageSize=10&classId=6"
            Silian_headers = None
        else:
            Silian_headers = {"Accept": "application/json", "x-api-key": Silian_x_api_key}
            Silian_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&searchFilter={
                name
            }&sortField=2&sortOrder=desc&pageSize=10&classId=6"

        if ver:
            Silian_url += f"&gameVersion={ver}"
        Silian_results = []
        Silian_resp = await get_url(Silian_url, 200, fmt="json", timeout=5, attempt=3, headers=Silian_headers)
        if Silian_resp:
            if not Silian_enable_mirror:  # 没提供 pagination
                if Silian_resp["pagination"]["resultCount"] == 0:
                    return None
            for Silian_mod in Silian_resp["data"]:
                Silian_results.append(("curseforge", Silian_mod["name"], Silian_mod["id"], None))
        return Silian_results

    async def get_modrinth_project_version(project_id: str, ver: str):
        Silian_url = f'https://api.modrinth.com/v2/project/{project_id}/version?game_versions=["{ver}"]&featured=true'
        Silian_resp = (await get_url(Silian_url, 200, fmt="json", timeout=5, attempt=3))[0]
        if Silian_resp:
            return Silian_resp

    async def get_curseforge_mod_version_index(modid: str):
        if Silian_enable_mirror:
            # https://mcim.z0z0r4.top/docs#/Curseforge/get_mod_curseforge_mod__modid_slug__get
            Silian_url = f"https://mcim.z0z0r4.top/curseforge/mod/{modid}"
            Silian_headers = None
        else:
            Silian_headers = {"Accept": "application/json", "x-api-key": Silian_x_api_key}
            Silian_url = f"https://api.curseforge.com/v1/mods/{modid}"
        Silian_resp = await get_url(Silian_url, 200, fmt="json", timeout=5, attempt=3, headers=Silian_headers)
        if Silian_resp:
            return Silian_resp["data"]["latestFilesIndexes"]

    async def get_curseforge_mod_file(modid: str, ver: str):
        if Silian_enable_mirror:
            Silian_url = f"https://mcim.z0z0r4.top/curseforge/mod/{modid}/files?gameVersion={ver}"
            Silian_headers = None
        else:
            Silian_headers = {"Accept": "application/json", "x-api-key": Silian_x_api_key}
            Silian_url = f"https://api.curseforge.com/v1/mods/{modid}/files?gameVersion={ver}"

        Silian_resp = await get_url(Silian_url, 200, fmt="json", timeout=5, attempt=3, headers=Silian_headers)
        if Silian_resp:
            return Silian_resp["data"][0]

    # 搜索 Mod
    Silian_result = await asyncio.gather(*(search_modrinth(Silian_mod_name, ver), search_curseforge(Silian_mod_name, ver)))
    Silian_cache_result = []
    if not Silian_result[0] and not Silian_result[1]:
        await msg.finish(I18NContext("mod_dl.message.not_found"))
    else:
        # 合并搜索结果
        Silian_reply_chain = []
        count = 0

        # 先显示 CurseForge 的结果
        if not Silian_result[1]:
            Silian_reply_chain.append(I18NContext("mod_dl.message.curseforge.not_found"))
        else:
            Silian_reply_chain.append(I18NContext("mod_dl.message.curseforge.result"))
            for mod in Silian_result[1]:
                count += 1
                Silian_reply_chain.append(Plain(f"{count}. {mod[1]}"))
                Silian_cache_result.append(mod)

        if not Silian_result[0]:
            Silian_reply_chain.append(I18NContext("mod_dl.message.modrinth.not_found"))
        Silian_reply_chain.append(I18NContext("mod_dl.message.modrinth.result"))
        for mod in Silian_result[0]:
            count += 1
            Silian_reply_chain.append(Plain(f"{count}. {mod[1]}"))
            Silian_cache_result.append(mod)
        Silian_reply_chain.append(I18NContext("mod_dl.message.prompt"))

        Silian_reply = await msg.wait_reply(Silian_reply_chain, delete=True)
        Silian_replied = Silian_reply.as_display(text_only=True)

        # 查找 Mod
        if is_int(Silian_replied):
            Silian_replied = int(Silian_replied)
            if not Silian_replied or Silian_replied > len(Silian_cache_result):
                await msg.finish(I18NContext("mod_dl.message.invalid.out_of_range"))
            else:
                Silian_mod_info = Silian_cache_result[Silian_replied - 1]
        else:
            await msg.finish(I18NContext("mod_dl.message.invalid.non_digital"))

        if Silian_mod_info[0] == "modrinth":  # modrinth mod
            if not ver:
                Silian_reply2 = await msg.wait_reply(
                    f"{msg.session_info.locale.t('mod_dl.message.version')}\n"
                    + "\n".join(Silian_mod_info[3])
                    + f"\n{msg.session_info.locale.t('mod_dl.message.version.prompt')}",
                    delete=True,
                )
                Silian_replied2 = Silian_reply2.as_display(text_only=True)
                if Silian_replied2 in Silian_mod_info[3]:
                    version_info = await get_modrinth_project_version(Silian_mod_info[2], Silian_replied2)
                    if version_info:
                        await msg.finish(
                            f"{' '.join(version_info['loaders'])}\n{msg.session_info.locale.t('mod_dl.message.download_url')}{version_info['files'][0]['url']}\n{msg.session_info.locale.t('mod_dl.message.filename')}{version_info['files'][0]['filename']}"
                        )
                else:
                    await msg.finish()
            elif ver not in Silian_mod_info[3]:
                await msg.finish(I18NContext("mod_dl.message.version.not_found"))
            elif ver in Silian_mod_info[3]:
                version_info = await get_modrinth_project_version(Silian_mod_info[2], ver)
                if version_info:
                    await msg.finish(
                        f"{' '.join(version_info['loaders'])}\n{msg.session_info.locale.t('mod_dl.message.download_url')}{version_info['files'][0]['url']}\n{msg.session_info.locale.t('mod_dl.message.filename')}{version_info['files'][0]['filename']}"
                    )
        else:  # curseforge mod
            Silian_version_index, Silian_ver_list = await get_curseforge_mod_version_index(Silian_mod_info[2]), []
            for Silian_version_ in Silian_version_index:
                if Silian_version_["gameVersion"] not in Silian_ver_list:
                    Silian_ver_list.append(Silian_version_["gameVersion"])
            if Silian_version_index:
                if not ver:
                    Silian_reply2 = await msg.wait_reply(
                        f"{msg.session_info.locale.t('mod_dl.message.version')}\n"
                        + "\n".join(Silian_ver_list)
                        + f"\n{msg.session_info.locale.t('mod_dl.message.version.prompt')}",
                        delete=True,
                    )
                    ver = Silian_reply2.as_display(text_only=True)
                elif ver not in Silian_ver_list:
                    await msg.finish(I18NContext("mod_dl.message.version.not_found"))

                if ver in Silian_ver_list:
                    file_info = await get_curseforge_mod_file(Silian_mod_info[2], ver)
                    if file_info:
                        await msg.finish(
                            f"{' '.join(file_info['gameVersions'])} \
                                         \n{msg.session_info.locale.t('mod_dl.message.download_url')}{file_info['downloadUrl']} \
                                         \n{msg.session_info.locale.t('mod_dl.message.filename')}{file_info['fileName']}"
                        )
                else:
                    await msg.finish(I18NContext("mod_dl.message.version.not_found"))
