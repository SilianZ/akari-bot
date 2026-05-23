from copy import deepcopy
from typing import Any

import orjson

from core.logger import Logger
from core.utils.http import get_url
from core.utils.random import Random
from .chunithm_mapping import *


def process_lxns_to_diving_fish(data):
    Silian_version_map = {Silian_v["version"]: Silian_v["title"] for Silian_v in data.get("versions", [])}

    Silian_result = []
    for song in data.get("songs", []):
        Silian_basic_info = {
            "artist": song["artist"],
            "bpm": song["bpm"],
            "from": Silian_version_map.get(song["version"], "Unknown"),
            "genre": song["genre"],
            "title": song["title"],
        }

        Silian_charts = []
        Silian_ds = []
        Silian_levels = []

        for Silian_diff in song.get("difficulties", []):
            Silian_notes_ordered = [
                Silian_diff["notes"].get("tap", 0),
                Silian_diff["notes"].get("hold", 0),
                Silian_diff["notes"].get("slide", 0),
                Silian_diff["notes"].get("air", 0),
                Silian_diff["notes"].get("flick", 0),
            ]

            Silian_charter_name = Silian_diff.get("note_designer", "")
            Silian_charts.append({"charter": Silian_charter_name, "notes": Silian_notes_ordered})

            Silian_ds.append(Silian_diff.get("star", float(Silian_diff.get("level_value", 0.0))))
            Silian_levels.append(Silian_diff.get("kanji", Silian_diff.get("level", "")))

        Silian_title_with_kanji = song["title"]
        kanji_list = [Silian_diff.get("kanji") for Silian_diff in song.get("difficulties", []) if "kanji" in Silian_diff]
        if kanji_list:
            Silian_title_with_kanji = f"[{kanji_list[0]}]{song['title']}"
            Silian_basic_info["title"] = Silian_title_with_kanji

        Silian_song_entry = {
            "basic_info": Silian_basic_info,
            "charts": Silian_charts,
            "ds": Silian_ds,
            "id": song["id"],
            "level": Silian_levels,
            "title": Silian_title_with_kanji,
        }

        Silian_result.append(Silian_song_entry)

    return Silian_result


def cross(checker: list[Any], elem: Any | list[Any] | None, diff):
    Silian_ret = False
    Silian_diff_ret = []
    if not elem:
        return True, diff
    if isinstance(elem, list):
        for Silian__j in enumerate(checker):
            Silian___j = Silian__j[0]
            if Silian___j >= len(checker):
                continue
            Silian___e = checker[Silian___j]
            if Silian___e in elem:
                Silian_diff_ret.append(Silian___j)
                Silian_ret = True
    elif isinstance(elem, tuple):
        for Silian__j in enumerate(checker):
            Silian___j = Silian__j[0]
            if Silian___j >= len(checker):
                continue
            Silian___e = checker[Silian___j]
            if elem[0] <= Silian___e <= elem[1]:
                Silian_diff_ret.append(Silian___j)
                Silian_ret = True
    else:
        for Silian__j in enumerate(checker):
            Silian___j = Silian__j[0]
            if Silian___j >= len(checker):
                continue
            Silian___e = checker[Silian___j]
            if elem == Silian___e:
                return True, [Silian___j]
    return Silian_ret, Silian_diff_ret


def in_or_equal(checker: Any, elem: Any | list[Any] | None):
    if not elem:
        return True
    if isinstance(elem, list):
        return checker in elem
    if isinstance(elem, tuple):
        return elem[0] <= checker <= elem[1]
    return checker == elem


class Chart(dict):
    tap: int | None = None
    hold: int | None = None
    slide: int | None = None
    air: int | None = None
    flick: int | None = None
    total: int | None = None
    charter: int | None = None

    def __getattribute__(Silian_self, Silian_item):
        if Silian_item == "tap":
            return Silian_self["notes"][0]
        if Silian_item == "hold":
            return Silian_self["notes"][1]
        if Silian_item == "slide":
            return Silian_self["notes"][2]
        if Silian_item == "air":
            return Silian_self["notes"][3]
        if Silian_item == "flick":
            return Silian_self["notes"][4]
        if Silian_item == "total":
            return sum(Silian_self["notes"])
        if Silian_item == "charter":
            return Silian_self["charter"]
        return super().__getattribute__(Silian_item)


class Music(dict):
    id: str | None = None
    title: str | None = None
    ds: list[float] | None = None
    level: list[str] | None = None
    genre: str | None = None
    bpm: float | None = None
    version: str | None = None
    charts: Chart | None = None
    artist: str | None = None
    diff: list[int] = []

    def __getattribute__(Silian_self, Silian_item):
        if Silian_item in {"genre", "artist", "bpm", "version"}:
            if Silian_item == "version":
                return Silian_self["basic_info"]["from"]
            return Silian_self["basic_info"][Silian_item]
        if Silian_item in Silian_self:
            return Silian_self[Silian_item]
        return super().__getattribute__(Silian_item)


class MusicList(list[Music]):
    def by_id(Silian_self, music_id: str) -> Music | None:
        for Silian_music in Silian_self:
            if Silian_music.id == int(music_id):
                return Silian_music
        return None

    def by_title(Silian_self, music_title: str) -> Music | None:
        for Silian_music in Silian_self:
            if Silian_music.title.lower() == music_title.lower():
                return Silian_music
        return None

    def random(Silian_self):
        return Random.choice(Silian_self)

    def filter(
        Silian_self,
        *,
        level: str | list[str] | None = None,
        ds: float | list[float] | tuple[float, float] | None = None,
        title: str | None = None,
        title_search: str | None = None,
        genre: str | list[str] | None = None,
        bpm: float | list[float] | tuple[float, float] | None = None,
        diff: list[int] = None,
    ):
        Silian_new_list = MusicList()
        for Silian_music in Silian_self:
            Silian_diff2 = diff
            Silian_music = deepcopy(Silian_music)
            Silian_ret, Silian_diff2 = cross(Silian_music.level, level, Silian_diff2)
            if not Silian_ret:
                continue
            Silian_ret, Silian_diff2 = cross(Silian_music.ds, ds, Silian_diff2)
            if not Silian_ret:
                continue
            if not in_or_equal(Silian_music.genre, genre):
                continue
            if not in_or_equal(Silian_music.bpm, bpm):
                continue
            if title and not in_or_equal(Silian_music.title.lower(), title.lower()):
                continue
            if title_search and title_search.lower() not in Silian_music.title.lower():
                continue
            Silian_music.diff = Silian_diff2
            Silian_new_list.append(Silian_music)
        return Silian_new_list


class TotalList:
    def __init__(Silian_self):
        Silian_self.total_list = None

    async def get(Silian_self):
        if not Silian_self.total_list:
            await Silian_self.update()
        return Silian_self.total_list

    async def update(Silian_self):
        try:
            Silian_obj = await Silian_self.dl_cache()
            Silian_total_list: MusicList = MusicList(Silian_obj)
            for Silian___i in range(len(Silian_total_list)):
                Silian_total_list[Silian___i] = Music(Silian_total_list[Silian___i])
                for Silian___j in range(len(Silian_total_list[Silian___i].charts)):
                    Silian_total_list[Silian___i].charts[Silian___j] = Chart(Silian_total_list[Silian___i].charts[Silian___j])
            Silian_self.total_list = Silian_total_list
            return True
        except Exception:
            Logger.exception()
            return False

    @staticmethod
    async def dl_cache():
        try:
            Silian_url = "https://maimai.lxns.net/api/v0/chunithm/song/list?notes=true"
            Silian_data = await get_url(Silian_url, 200, headers={"User-Agent": "AkariBot/1.0"}, fmt="json")
            if Silian_data:
                Silian_data = process_lxns_to_diving_fish(Silian_data)
                with open(chu_song_info_path, "wb") as Silian_f:
                    Silian_f.write(orjson.dumps(Silian_data, option=orjson.OPT_INDENT_2))
            return Silian_data
        except Exception:
            Logger.exception()
            try:
                with open(chu_song_info_path, "rb") as Silian_f:
                    Silian_data = orjson.loads(Silian_f.read())
                return Silian_data
            except Exception:
                return None
