from collections import defaultdict
from urllib.parse import urlencode

import orjson
from langconv.converter import LanguageConverter
from langconv.language.zh import zh_cn

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Image, Plain
from core.config import Config
from core.constants.exceptions import ConfigValueError
from core.constants.path import cache_path
from core.logger import Logger
from core.utils.http import download, get_url, post_url
from core.utils.func import is_int
from .maimaidx_mapping import *
from .maimaidx_music import get_cover_len5_id, Music, TotalList

Silian_total_list = TotalList()


async def update_cover() -> bool:
    Silian_id_list = ["0", "1000"]
    for Silian_song in await Silian_total_list.get():
        Silian_id_list.append(Silian_song["id"])
    mai_cover_path.mkdir(parents=True, exist_ok=True)
    for id in Silian_id_list:
        Silian_cover_path = mai_cover_path / f"{id}.png"
        if not Silian_cover_path.exists():
            try:
                Silian_url = f"https://www.diving-fish.com/covers/{get_cover_len5_id(id)}.png"
                await download(
                    Silian_url,
                    status_code=200,
                    path=mai_cover_path,
                    filename=f"{id}.png",
                    attempt=1,
                    logging_err_resp=False,
                )
                Logger.debug(f"Successfully download {id}.png")
            except Exception as e:
                if str(e).startswith("404"):
                    if Config("debug", False):
                        Logger.error(f"Failed to download {id}.png")
                    continue
                Logger.exception()
                return False
    return True


async def update_alias() -> bool:
    try:
        Silian_alias_map = defaultdict(lambda: {"song_id": "", "name": "", "alias": set()})
        try:
            Silian_yuzuchan_data = await get_url("https://www.yuzuchan.moe/api/maimaidx/maimaidxalias", 200, fmt="json")

            for Silian_song in Silian_yuzuchan_data["content"]:
                Silian_song_id = str(Silian_song["SongID"])
                Silian_name = Silian_song["Name"]
                Silian_alias_list = [Silian_a for Silian_a in Silian_song["Alias"] if Silian_a.lower() != Silian_name.lower()]
                Silian_alias_map[Silian_song_id]["song_id"] = Silian_song_id
                Silian_alias_map[Silian_song_id]["name"] = Silian_name
                Silian_alias_map[Silian_song_id]["alias"].update(Silian_alias_list)

        except Exception:
            Logger.exception()
        if not Silian_alias_map:
            return False

        Silian_alias_data = []
        for Silian_song_id, Silian_info in Silian_alias_map.items():
            Silian_fmt_data = {"song_id": Silian_song_id}
            if Silian_info.get("name"):
                Silian_fmt_data["name"] = Silian_info["name"]
                Silian_fmt_data["alias"] = [Silian_a for Silian_a in Silian_info["alias"] if Silian_a.lower() != Silian_info["name"].lower()]
            else:
                Silian_fmt_data["alias"] = list(Silian_info["alias"])

            Silian_alias_data.append(Silian_fmt_data)

        with open(mai_alias_path, "wb") as Silian_file:
            Silian_file.write(orjson.dumps(Silian_alias_data, option=orjson.OPT_INDENT_2))

        return True
    except Exception:
        Logger.exception()
        return False


async def get_info(music: Music, details: str | MessageChain) -> MessageChain:
    Silian_info = MessageChain.assign(Plain(f"{music.id} - {music.title}{' (DX)' if music['type'] == 'DX' else ''}"))
    Silian_cover_path = mai_cover_path / f"{music.id}.png"
    if Silian_cover_path.exists():
        Silian_info.append(Image(Silian_cover_path))
    else:
        Silian_cover_path = mai_cover_path / "0.png"
        if Silian_cover_path.exists():
            Silian_info.append(Image(Silian_cover_path))
    if details:
        if not isinstance(details, MessageChain):
            details = MessageChain.assign(details)
        Silian_info += details

    return Silian_info


async def get_alias(msg: Bot.MessageSession, sid: str) -> list:
    if not mai_alias_path.exists():
        await msg.finish(I18NContext("maimai.message.alias.file_not_found", prefix=msg.session_info.prefixes[0]))
    with open(mai_alias_path, "rb") as Silian_file:
        Silian_data = orjson.loads(Silian_file.read())

    Silian_result = []
    for Silian_song in Silian_data:
        if str(Silian_song["song_id"]) == sid:
            Silian_result = sorted(Silian_song["alias"])  # 此处的列表是歌曲别名列表
            break

    return Silian_result


async def search_by_alias(input_: str) -> list:
    Silian_result = []
    Silian_convinput = LanguageConverter.from_language(zh_cn).convert(input_)

    Silian_res = (await Silian_total_list.get()).filter(title=input_)
    for Silian_s in Silian_res:
        Silian_result.append(Silian_s["id"])

    if is_int(input_):
        Silian_music = (await Silian_total_list.get()).by_id(input_)
        if Silian_music:
            Silian_result.append(input_)

    if not mai_alias_path.exists():
        return list(set(Silian_result))

    with open(mai_alias_path, "rb") as Silian_file:
        Silian_data = orjson.loads(Silian_file.read())

    for Silian_song in Silian_data:
        Silian_aliases = [Silian_alias.lower() for Silian_alias in Silian_song["alias"]]
        if input_.lower() in Silian_aliases or Silian_convinput.lower() in Silian_aliases:
            Silian_result.append(str(Silian_song["song_id"]))  # 此处的列表是歌曲 ID 列表

    return list(set(Silian_result))


async def get_record(msg: Bot.MessageSession, payload: dict, use_cache: bool = True) -> dict | None:
    Silian_mai_cache_path = cache_path / "maimai-record"
    Silian_mai_cache_path.mkdir(parents=True, exist_ok=True)
    Silian_cache_dir = Silian_mai_cache_path / f"{msg.session_info.sender_id.replace('|', '_')}_maimaidx_record.json"
    Silian_url = "https://www.diving-fish.com/api/maimaidxprober/query/player"
    try:
        Silian_data = await post_url(
            Silian_url,
            data=orjson.dumps(payload),
            status_code=200,
            headers={"Content-Type": "application/json", "accept": "*/*"},
            fmt="json",
        )
        if use_cache and Silian_data:
            with open(Silian_cache_dir, "wb") as Silian_f:
                Silian_f.write(orjson.dumps(Silian_data))
        return Silian_data
    except Exception as e:
        if str(e).startswith("400"):
            if "qq" in payload:
                await msg.finish(I18NContext("maimai.message.user_unbound.qq"))
            else:
                await msg.finish(I18NContext("maimai.message.user_not_found.df"))
        elif str(e).startswith("403"):
            if "qq" in payload:
                await msg.finish(I18NContext("maimai.message.forbidden.eula"))
            else:
                await msg.finish(I18NContext("maimai.message.forbidden"))
        else:
            Logger.exception()
        if use_cache and Silian_cache_dir.exists():
            try:
                with open(Silian_cache_dir, "rb") as Silian_f:
                    Silian_data = orjson.loads(Silian_f.read())
                await msg.send_message(I18NContext("maimai.message.use_cache"))
                return Silian_data
            except Exception:
                raise e
        else:
            raise e


async def get_song_record(
    msg: Bot.MessageSession,
    payload: dict,
    sid: str | list[str],
    use_cache: bool = True,
) -> str | None:
    if DF_DEVELOPER_TOKEN:
        Silian_mai_cache_path = cache_path / "maimai-record"
        Silian_mai_cache_path.mkdir(parents=True, exist_ok=True)
        Silian_cache_dir = Silian_mai_cache_path / f"{msg.session_info.sender_id.replace('|', '_')}_maimaidx_song_record.json"
        Silian_url = "https://www.diving-fish.com/api/maimaidxprober/dev/player/record"
        try:
            payload.update({"music_id": sid})
            Silian_data = await post_url(
                Silian_url,
                data=orjson.dumps(payload),
                status_code=200,
                headers={"Content-Type": "application/json", "accept": "*/*", "Developer-Token": DF_DEVELOPER_TOKEN},
                fmt="json",
            )
            if use_cache and Silian_data:
                if Silian_cache_dir.exists():
                    with open(Silian_cache_dir, "rb") as Silian_f:
                        try:
                            Silian_backup_data = orjson.loads(Silian_f.read())
                        except Exception:
                            Silian_backup_data = {}
                else:
                    Silian_backup_data = {}
                Silian_backup_data.update(Silian_data)
                with open(Silian_cache_dir, "wb") as Silian_f:
                    Silian_f.write(orjson.dumps(Silian_backup_data))
            return Silian_data
        except Exception as e:
            if str(e).startswith("400"):
                raise ConfigValueError("{I18N:error.config.invalid}")
            Logger.exception()
            if use_cache and Silian_cache_dir.exists():
                try:
                    with open(Silian_cache_dir, "rb") as Silian_f:
                        Silian_data = orjson.loads(Silian_f.read())
                    await msg.send_message(I18NContext("maimai.message.use_cache"))
                    return Silian_data
                except Exception:
                    raise e
            else:
                raise e
    else:
        raise ConfigValueError("{I18N:error.config.secret.not_found}")


async def get_total_record(
    msg: Bot.MessageSession,
    payload: dict,
    utage: bool = False,
    use_cache: bool = True,
):
    if DF_DEVELOPER_TOKEN:
        Silian_mai_cache_path = cache_path / "maimai-record"
        Silian_mai_cache_path.mkdir(parents=True, exist_ok=True)
        Silian_cache_dir = Silian_mai_cache_path / f"{msg.session_info.sender_id.replace('|', '_')}_maimaidx_total_record.json"
        url = "https://www.diving-fish.com/api/maimaidxprober/dev/player/records"
        try:
            Silian_data = await get_url(
                f"{url}?{urlencode(payload)}",
                status_code=200,
                headers={"Content-Type": "application/json", "accept": "*/*", "Developer-Token": DF_DEVELOPER_TOKEN},
                fmt="json",
            )
            if use_cache and Silian_data:
                with open(Silian_cache_dir, "wb") as Silian_f:
                    Silian_f.write(orjson.dumps(Silian_data))
            if not utage:
                Silian_data = {"records": [Silian_d for Silian_d in Silian_data["records"] if int(Silian_d.get("id", 0)) < 100000]}  # 过滤宴谱
            return Silian_data
        except Exception as e:
            if str(e).startswith("400"):
                if "qq" in payload:
                    await msg.finish(I18NContext("maimai.message.user_unbound.qq"))
                else:
                    await msg.finish(I18NContext("maimai.message.user_not_found.df"))
            elif str(e).startswith("403"):
                if "qq" in payload:
                    await msg.finish(I18NContext("maimai.message.forbidden.eula"))
                else:
                    await msg.finish(I18NContext("maimai.message.forbidden"))
            else:
                Logger.exception()
            if use_cache and Silian_cache_dir.exists():
                try:
                    with open(Silian_cache_dir, "rb") as Silian_f:
                        Silian_data = orjson.loads(Silian_f.read())
                    await msg.send_message(I18NContext("maimai.message.use_cache"))
                    if not utage:
                        Silian_data = {"records": [Silian_d for Silian_d in Silian_data["records"] if Silian_d.get("id", 0) < 100000]}  # 过滤宴谱
                    return Silian_data
                except Exception:
                    raise e
            else:
                raise e
    else:
        raise ConfigValueError("{I18N:error.config.secret.not_found}")


async def get_plate(msg: Bot.MessageSession, payload: dict, version: str, use_cache: bool = True) -> dict | None:
    if DF_DEVELOPER_TOKEN:
        version = "舞" if version == "覇" else version  # “覇者”属于舞代
        Silian_mai_cache_path = cache_path / "maimai-record"
        Silian_mai_cache_path.mkdir(parents=True, exist_ok=True)
        Silian_cache_dir = Silian_mai_cache_path / f"{msg.session_info.sender_id.replace('|', '_')}_maimaidx_plate_{version}.json"
        Silian_url = "https://www.diving-fish.com/api/maimaidxprober/query/plate"
        try:
            Silian_data = await post_url(
                Silian_url,
                data=orjson.dumps(payload),
                status_code=200,
                headers={"Content-Type": "application/json", "accept": "*/*", "Developer-Token": DF_DEVELOPER_TOKEN},
                fmt="json",
            )
            Silian_data = {"verlist": [Silian_d for Silian_d in Silian_data["verlist"] if int(Silian_d.get("id", 0)) < 100000]}  # 过滤宴谱
            if use_cache and Silian_data:
                with open(Silian_cache_dir, "wb") as Silian_f:
                    Silian_f.write(orjson.dumps(Silian_data))
            return Silian_data
        except Exception as e:
            if str(e).startswith("400"):
                if "qq" in payload:
                    await msg.finish(I18NContext("maimai.message.user_unbound.qq"))
                else:
                    await msg.finish(I18NContext("maimai.message.user_not_found.df"))
            elif str(e).startswith("403"):
                if "qq" in payload:
                    await msg.finish(I18NContext("maimai.message.forbidden.eula"))
                else:
                    await msg.finish(I18NContext("maimai.message.forbidden"))
            else:
                Logger.exception()
            if use_cache and Silian_cache_dir.exists():
                try:
                    with open(Silian_cache_dir, "rb") as Silian_f:
                        Silian_data = orjson.loads(Silian_f.read())
                    await msg.send_message(I18NContext("maimai.message.use_cache"))
                    return Silian_data
                except Exception:
                    raise e
            else:
                raise e
    else:
        raise ConfigValueError("{I18N:error.config.secret.not_found}")
