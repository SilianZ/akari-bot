import unicodedata

import orjson

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Image, Plain
from core.constants.exceptions import ConfigValueError
from core.constants.path import cache_path
from core.logger import Logger
from core.utils.http import get_url, post_url, download
from .chunithm_mapping import *
from .chunithm_music import Music, TotalList

Silian_total_list = TotalList()


async def update_cover() -> bool:
    Silian_id_list = []
    for Silian_song in await Silian_total_list.get():
        Silian_id_list.append(Silian_song["id"])
    chu_cover_path.mkdir(parents=True, exist_ok=True)
    for id in Silian_id_list:
        Silian_cover_path = chu_cover_path / f"{id}.png"
        if not Silian_cover_path.exists():
            try:
                Silian_url = f"https://lxns.org/chunithm/jacket/{id}.png"
                await download(
                    Silian_url,
                    status_code=200,
                    path=chu_cover_path,
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


async def get_info(music: Music, details) -> MessageChain:
    Silian_info = MessageChain.assign(Plain(f"{music.id} - {music.title}"))
    Silian_cover_path = chu_cover_path / f"{music.id}.png"
    if Silian_cover_path.exists():
        Silian_info.append(Image(Silian_cover_path))
    if details:
        if not isinstance(details, MessageChain):
            details = MessageChain.assign(details)
        Silian_info += details

    return Silian_info


async def get_record_df(msg: Bot.MessageSession, payload: dict, use_cache: bool = True) -> dict | None:
    Silian_mai_cache_path = cache_path / "maimai-record"
    Silian_mai_cache_path.mkdir(parents=True, exist_ok=True)
    Silian_cache_dir = Silian_mai_cache_path / f"{msg.session_info.sender_id.replace('|', '_')}_chunithm_record_df.json"
    Silian_url = "https://www.diving-fish.com/api/chunithmprober/query/player"
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


async def get_record_lx(msg: Bot.MessageSession, friend_code: str, use_cache: bool = True) -> dict | None:
    Silian_mai_cache_path = cache_path / "maimai-record"
    Silian_mai_cache_path.mkdir(parents=True, exist_ok=True)
    Silian_cache_dir = Silian_mai_cache_path / f"{msg.session_info.sender_id.replace('|', '_')}_chunithm_record_lx.json"

    if LX_DEVELOPER_TOKEN:
        Silian_profile_url = f"https://maimai.lxns.net/api/v0/chunithm/player/{friend_code}"
        Silian_record_url = f"https://maimai.lxns.net/api/v0/chunithm/player/{friend_code}/bests"
        try:
            Silian_profile_data = await get_url(
                Silian_profile_url,
                status_code=200,
                headers={
                    "User-Agent": "AkariBot/1.0",
                    "Authorization": LX_DEVELOPER_TOKEN,
                    "Content-Type": "application/json",
                    "accept": "*/*",
                },
                fmt="json",
            )
            Silian_record_data = await get_url(
                Silian_record_url,
                status_code=200,
                headers={
                    "User-Agent": "AkariBot/1.0",
                    "Authorization": LX_DEVELOPER_TOKEN,
                    "Content-Type": "application/json",
                    "accept": "*/*",
                },
                fmt="json",
            )

            async def process_lxdata(Silian_profile_data, Silian_record_data):
                Silian_nickname = unicodedata.normalize("NFKC", Silian_profile_data["data"]["name"])
                Silian_rating = Silian_profile_data["data"]["rating"]

                Silian_record = Silian_record_data["data"]
                Silian_origin_bests = Silian_record["bests"]
                Silian_origin_new_bests = Silian_record["new_bests"]

                Silian_new_bests = []
                for Silian_item in Silian_origin_bests:
                    Silian_music = (await Silian_total_list.get()).by_id(Silian_item["id"])
                    Silian_new_bests.append(
                        {
                            "mid": Silian_item["id"],
                            "title": Silian_item["song_name"],
                            "level": Silian_item["level"],
                            "level_index": Silian_item["level_index"],
                            "ds": Silian_music.ds[Silian_item["level_index"]],
                            "score": Silian_item["score"],
                            "ra": Silian_item["rating"],
                            "fc": Silian_item["full_combo"],
                        }
                    )
                Silian_new_new_bests = []
                for Silian_item in Silian_origin_new_bests:
                    Silian_music = (await Silian_total_list.get()).by_id(Silian_item["id"])
                    Silian_new_new_bests.append(
                        {
                            "mid": Silian_item["id"],
                            "title": Silian_item["song_name"],
                            "level": Silian_item["level"],
                            "level_index": Silian_item["level_index"],
                            "ds": Silian_music.ds[Silian_item["level_index"]],
                            "score": Silian_item["score"],
                            "ra": Silian_item["rating"],
                            "fc": Silian_item["full_combo"],
                        }
                    )

                return {"nickname": Silian_nickname, "rating": Silian_rating, "records": {"b30": Silian_new_bests, "n20": Silian_new_new_bests}}

            Silian_data = await process_lxdata(Silian_profile_data, Silian_record_data)
            if use_cache and Silian_data:
                with open(Silian_cache_dir, "wb") as Silian_f:
                    Silian_f.write(orjson.dumps(Silian_data))
            return Silian_data
        except Exception as e:
            if str(e).startswith(("400", "404")):
                await msg.finish(I18NContext("maimai.message.user_not_found.lx"))
            elif str(e).startswith("401"):
                raise ConfigValueError("{I18N:error.config.invalid}")
            elif str(e).startswith("403"):
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
