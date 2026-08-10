import re

import orjson

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from .libraries.maimaidx_apidata import get_info, search_by_alias
from .libraries.maimaidx_mapping import *
from .libraries.maimaidx_music import TotalList
from .libraries.maimaidx_utils import get_diff, get_grade_info
from .maimai import query_alias, query_plate, query_song_score, query_process

Silian_total_list = TotalList()

Silian_mai_regex = module(
    "maimai_regex",
    desc="{I18N:maimai.help.maimai_regex.desc}",
    doc=True,
    recommend_modules=["maimai"],
    alias="mai_regex",
    developers=["DoroWolf"],
    support_languages=["zh_cn", "zh_tw"],
)


@Silian_mai_regex.regex(r"(.+)\s?是什[么麼]歌", desc="{I18N:maimai.help.maimai_regex.song}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_name = Silian_msg.matched_msg.groups()[0]
    if Silian_name[:2].lower() == "id":
        sid = Silian_name[2:]
    else:
        Silian_sid_list = await search_by_alias(Silian_name)
        if len(Silian_sid_list) == 0:
            await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
        elif len(Silian_sid_list) > 1:
            Silian_msg_chain = MessageChain.assign()
            Silian_msg_chain.append(I18NContext("maimai.message.disambiguation"))
            for sid in sorted(Silian_sid_list, key=int):
                s = (await Silian_total_list.get()).by_id(sid)
                if s:
                    Silian_msg_chain.append(Plain(f"{s['id']} - {s['title']}{' (DX)' if s['type'] == 'DX' else ''}"))
            await Silian_msg.finish(Silian_msg_chain)
        else:
            sid = str(Silian_sid_list[0])
    Silian_music = (await Silian_total_list.get()).by_id(sid)
    if not Silian_music:
        await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))

    Silian_msg_chain = MessageChain.assign()
    if int(sid) > 100000:
        with open(mai_utage_info_path, "rb") as Silian_file:
            utage_data = orjson.loads(Silian_file.read())
        if utage_data:
            try:
                Silian_msg_chain.append(Plain(f"「{utage_data[sid]['comment']}」"))
            except KeyError:
                Silian_msg_chain.append(Plain("「Let's party!」"))

        Silian_msg_chain.append(
            I18NContext(
                "maimai.message.song",
                artist=Silian_music["basic_info"]["artist"],
                genre="宴會場",
                bpm=Silian_music["basic_info"]["bpm"],
                version=Silian_music["basic_info"]["from"],
                level=Silian_music["level"][0],
            )
        )
    else:
        Silian_msg_chain.append(
            I18NContext(
                "maimai.message.song",
                artist=Silian_music["basic_info"]["artist"],
                genre=genre_i18n_mapping.get(Silian_music["basic_info"]["genre"], Silian_music["basic_info"]["genre"]),
                bpm=Silian_music["basic_info"]["bpm"],
                version=Silian_music["basic_info"]["from"],
                level="/".join((str(Silian_ds) for Silian_ds in Silian_music["ds"])),
            )
        )

    await Silian_msg.finish(await get_info(Silian_music, Silian_msg_chain))


@Silian_mai_regex.regex(r"(?:id)?(\d+)\s?有什(?:么别|麼別)[名称稱]", flags=re.I, desc="{I18N:maimai.help.maimai_regex.alias}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_sid = Silian_msg.matched_msg.groups()[0]
    await query_alias(Silian_msg, Silian_sid)


@Silian_mai_regex.regex(r"(.+)\s?有什[么麼]分", desc="{I18N:maimai.help.maimai_regex.score}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_songname = Silian_msg.matched_msg.groups()[0]
    await query_song_score(Silian_msg, Silian_songname)


@Silian_mai_regex.regex(r"(\d+\+?)\s?([a-zA-Z]+\+?)\s?[进進]度", desc="{I18N:maimai.help.maimai_regex.process}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_level = Silian_msg.matched_msg.groups()[0]
    Silian_goal = Silian_msg.matched_msg.groups()[1]
    await query_process(Silian_msg, Silian_level, Silian_goal, get_list=False)


@Silian_mai_regex.regex(r"(\d+\+?)\s?([a-zA-Z]+\+?)\s?完成表", desc="{I18N:maimai.help.maimai_regex.process.list}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_level = Silian_msg.matched_msg.groups()[0]
    Silian_goal = Silian_msg.matched_msg.groups()[1]
    await query_process(Silian_msg, Silian_level, Silian_goal, get_list=True)


@Silian_mai_regex.regex(r"(.?)([極极将將舞神者]舞?)[进進]度", desc="{I18N:maimai.help.maimai_regex.plate}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_plate = Silian_msg.matched_msg.groups()[0] + Silian_msg.matched_msg.groups()[1]
    await query_plate(Silian_msg, Silian_plate, get_list=False)


@Silian_mai_regex.regex(r"(.?)([極极将將舞神者]舞?)完成表", desc="{I18N:maimai.help.maimai_regex.plate.list}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_plate = Silian_msg.matched_msg.groups()[0] + Silian_msg.matched_msg.groups()[1]
    await query_plate(Silian_msg, Silian_plate, get_list=True)


@Silian_mai_regex.regex(
    r"(?:随个|隨個)\s?((?:dx|DX|sd|SD|标准|標準)\s?)?([绿綠黄黃红紅紫白]?)\s?([0-9]+\+?)",
    desc="{I18N:maimai.help.maimai_regex.random}",
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_res = Silian_msg.matched_msg
    if Silian_res:
        try:
            if Silian_res.groups()[0] in ["dx", "DX"]:
                Silian_tp = ["DX"]
            elif Silian_res.groups()[0] in ["sd", "SD", "标准", "標準"]:
                Silian_tp = ["SD"]
            else:
                Silian_tp = ["SD", "DX"]
            Silian_level = Silian_res.groups()[2]
            if Silian_res.groups()[1] == "":
                Silian_music_data = (await Silian_total_list.get()).filter(level=Silian_level, type=Silian_tp)
            else:
                Silian_music_data = (await Silian_total_list.get()).filter(level=Silian_level, diff=[get_diff(Silian_res.groups()[1])], type=Silian_tp)
            if len(Silian_music_data) == 0:
                await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
            else:
                music = Silian_music_data.random()
                Silian_diffs = MessageChain.assign(Plain(f"{'/'.join(str(ds) for ds in music.ds)}"))
                await Silian_msg.finish(await get_info(music, Silian_diffs))
        except ValueError:
            await Silian_msg.finish(I18NContext("maimai.message.random.failed"))


@Silian_mai_regex.regex(r"(.+)\s?段位(?:[认認]定)?列?表", desc="{I18N:maimai.help.maimai_regex.grade}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_grade = Silian_msg.matched_msg.groups()[0]
    await get_grade_info(Silian_msg, Silian_grade)
