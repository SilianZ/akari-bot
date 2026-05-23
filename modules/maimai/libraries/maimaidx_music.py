from copy import deepcopy
from typing import Any

import orjson

from core.logger import Logger
from core.utils.http import get_url
from core.utils.random import Random
from .maimaidx_mapping import *


def get_cover_len5_id(mid: int | str) -> str:
    mid = int(mid)
    if 10000 < mid <= 11000:
        mid -= 10000
    return f"{mid:05d}"


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
    slide: int | None = None
    hold: int | None = None
    touch: int | None = None
    brk: int | None = None
    charter: int | None = None
    dxscore: int | None = None

    def __getattribute__(Silian_self, Silian_item):
        if Silian_item == "tap":
            return Silian_self["notes"][0]
        if Silian_item == "hold":
            return Silian_self["notes"][1]
        if Silian_item == "slide":
            return Silian_self["notes"][2]
        if Silian_item == "touch":
            return Silian_self["notes"][3] if len(Silian_self["notes"]) == 5 else 0
        if Silian_item == "brk":
            return Silian_self["notes"][-1]
        if Silian_item == "dxscore":
            return sum(Silian_self["charter"]) * 3
        if Silian_item == "charter":
            return Silian_self["charter"]
        return super().__getattribute__(Silian_item)


class Music(dict):
    id: str | None = None
    title: str | None = None
    ds: list[float] | None = None
    level: list[str] | None = None
    genre: str | None = None
    type: str | None = None
    bpm: float | None = None
    version: str | None = None
    charts: Chart | None = None
    release_date: str | None = None
    artist: str | None = None
    is_new: bool | None = False
    diff: list[int] = []

    def __getattribute__(Silian_self, Silian_item):
        if Silian_item in {"genre", "artist", "release_date", "bpm", "version", "is_new"}:
            if Silian_item == "version":
                return Silian_self["basic_info"]["from"]
            return Silian_self["basic_info"][Silian_item]
        if Silian_item in Silian_self:
            return Silian_self[Silian_item]
        return super().__getattribute__(Silian_item)


class MusicList(list[Music]):
    def by_id(Silian_self, music_id: str) -> Music | None:
        for Silian_music in Silian_self:
            if Silian_music.id == music_id:
                return Silian_music
        return None

    def by_title(Silian_self, music_title: str) -> Music | None:
        for Silian_music in Silian_self:
            if Silian_music.title.lower() == music_title.lower():
                return Silian_music
        return None

    def new(Silian_self):
        Silian_new_list = MusicList()
        for Silian_music in Silian_self:
            Silian_music = deepcopy(Silian_music)
            if not Silian_music.is_new:
                continue
            Silian_new_list.append(Silian_music)
        return Silian_new_list

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
        dxtype: str | list[str] | None = None,
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
            if not in_or_equal(Silian_music.type, dxtype):
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
            Silian_url = "https://www.diving-fish.com/api/maimaidxprober/music_data"
            Silian_data = await get_url(Silian_url, 200, fmt="json")
            if Silian_data:
                with open(mai_song_info_path, "wb") as Silian_f:
                    Silian_f.write(orjson.dumps(Silian_data, option=orjson.OPT_INDENT_2))
            return Silian_data
        except Exception:
            Logger.exception()
            try:
                with open(mai_song_info_path, "rb") as Silian_f:
                    Silian_data = orjson.loads(Silian_f.read())
                return Silian_data
            except Exception:
                return None
