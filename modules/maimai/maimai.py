import orjson

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Image as BImage
from core.component import module
from core.utils.image import msgchain2image
from core.logger import Logger
from core.scheduler import CronTrigger
from core.utils.func import is_int
from .database.models import DivingProberBindInfo
from .libraries.maimaidx_apidata import get_alias, get_info, search_by_alias, update_alias, update_cover
from .libraries.maimaidx_best50 import generate as generate_b50
from .libraries.maimaidx_platelist import generate as generate_plate
from .libraries.maimaidx_scoreline import draw_scoreline_table
from .libraries.maimaidx_scorelist import generate as generate_process
from .libraries.maimaidx_utils import *

Silian_total_list = TotalList()

Silian_mai = module(
    "maimai",
    recommend_modules="maimai_regex",
    developers=["mai-bot", "OasisAkari", "DoroWolf"],
    alias="mai",
    support_languages=["zh_cn"],
    desc="{I18N:maimai.help.desc}",
    doc=True,
)


@Silian_mai.command(
    "base <constant> [<constant_max>] [-p <page>] {{I18N:maimai.help.base}}",
    options_desc={"-p": "{I18N:maimai.help.option.p}"},
)
async def _(Silian_msg: Bot.MessageSession, Silian_constant: float, Silian_constant_max: float = None):
    Silian_result_set = []
    if Silian_constant <= 0:
        await Silian_msg.finish(I18NContext("maimai.message.level_invalid"))
    elif Silian_constant_max:
        if Silian_constant > Silian_constant_max:
            Silian_data = (await Silian_total_list.get()).filter(ds=(Silian_constant_max, Silian_constant))
            Silian_msg_chain = MessageChain.assign(
                I18NContext(
                    "maimai.message.base.range", constant=round(Silian_constant_max, 1), constant_max=round(Silian_constant, 1)
                )
            )
        else:
            Silian_data = (await Silian_total_list.get()).filter(ds=(Silian_constant, Silian_constant_max))
            Silian_msg_chain = MessageChain.assign(
                I18NContext(
                    "maimai.message.base.range", constant=round(Silian_constant, 1), constant_max=round(Silian_constant_max, 1)
                )
            )
    else:
        Silian_data = (await Silian_total_list.get()).filter(ds=Silian_constant)
        Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.base", constant=round(Silian_constant, 1)))

    for Silian_music in sorted(Silian_data, key=lambda Silian_i: int(Silian_i["id"])):
        for Silian_i in Silian_music.diff:
            if int(Silian_music["id"]) < 100000:  # 过滤宴谱
                Silian_result_set.append(
                    (
                        Silian_music["id"],
                        Silian_music["title"],
                        Silian_music["ds"][Silian_i],
                        diff_list[Silian_i],
                        Silian_music["level"][Silian_i],
                        Silian_music["type"],
                    )
                )

    Silian_total_pages = (len(Silian_result_set) + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE
    Silian_get_page = Silian_msg.parsed_msg.get("-p", False)
    if Silian_get_page and is_int(Silian_get_page["<page>"]):
        Silian_page = max(min(int(Silian_get_page["<page>"]), Silian_total_pages), 1)
    else:
        Silian_page = 1
    Silian_start_index = (Silian_page - 1) * SONGS_PER_PAGE
    Silian_end_index = Silian_page * SONGS_PER_PAGE

    for elem in Silian_result_set[Silian_start_index:Silian_end_index]:
        Silian_msg_chain.append(
            Plain(f"{elem[0]} - {elem[1]}{' (DX)' if elem[5] == 'DX' else ''} [{elem[3]}] {elem[4]} ({elem[2]})")
        )
    if len(Silian_result_set) == 0:
        await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
    elif len(Silian_result_set) <= SONGS_PER_PAGE:
        await Silian_msg.finish(Silian_msg_chain)
    else:
        Silian_msg_chain.append(I18NContext("maimai.message.pages", page=Silian_page, total_pages=Silian_total_pages))
        Silian_imgs = await msgchain2image(Silian_msg_chain, Silian_msg)
        if Silian_imgs:
            await Silian_msg.finish(Silian_imgs)
        else:
            await Silian_msg.finish(Silian_msg_chain)


@Silian_mai.command("level <level> [-p <page>] {{I18N:maimai.help.level}}", options_desc={"-p": "{I18N:maimai.help.option.p}"})
async def _(Silian_msg: Bot.MessageSession, Silian_level: str):
    Silian_result_set = []
    Silian_data = (await Silian_total_list.get()).filter(level=Silian_level)
    for Silian_music in sorted(Silian_data, key=lambda Silian_i: int(Silian_i["id"])):
        for Silian_i in Silian_music.diff:
            if int(Silian_music["id"]) < 100000:  # 过滤宴谱
                Silian_result_set.append(
                    (
                        Silian_music["id"],
                        Silian_music["title"],
                        Silian_music["ds"][Silian_i],
                        diff_list[Silian_i],
                        Silian_music["level"][Silian_i],
                        Silian_music["type"],
                    )
                )
    Silian_total_pages = (len(Silian_result_set) + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE
    Silian_get_page = Silian_msg.parsed_msg.get("-p", False)
    Silian_page = max(min(int(Silian_get_page["<page>"]), Silian_total_pages), 1) if Silian_get_page and is_int(Silian_get_page["<page>"]) else 1
    Silian_start_index = (Silian_page - 1) * SONGS_PER_PAGE
    Silian_end_index = Silian_page * SONGS_PER_PAGE

    Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.level", level=Silian_level))
    for elem in Silian_result_set[Silian_start_index:Silian_end_index]:
        Silian_msg_chain.append(
            Plain(f"{elem[0]} - {elem[1]}{' (DX)' if elem[5] == 'DX' else ''} [{elem[3]}] {elem[4]} ({elem[2]})")
        )

    if len(Silian_result_set) == 0:
        await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
    elif len(Silian_result_set) <= SONGS_PER_PAGE:
        await Silian_msg.finish(Silian_msg_chain)
    else:
        Silian_msg_chain.append(I18NContext("maimai.message.pages", page=Silian_page, total_pages=Silian_total_pages))
        Silian_imgs = await msgchain2image(Silian_msg_chain, Silian_msg)
        if Silian_imgs:
            await Silian_msg.finish(Silian_imgs)
        else:
            await Silian_msg.finish(Silian_msg_chain)


@Silian_mai.command("new [-p <page>] {{I18N:maimai.help.new}}", options_desc={"-p": "{I18N:maimai.help.option.p}"})
async def _(Silian_msg: Bot.MessageSession):
    Silian_result_set = []
    Silian_data = (await Silian_total_list.get()).new()

    for Silian_music in sorted(Silian_data, key=lambda Silian_i: int(Silian_i["id"])):
        Silian_result_set.append((Silian_music["id"], Silian_music["title"], Silian_music["type"]))
    Silian_total_pages = (len(Silian_result_set) + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE
    Silian_get_page = Silian_msg.parsed_msg.get("-p", False)
    Silian_page = max(min(int(Silian_get_page["<page>"]), Silian_total_pages), 1) if Silian_get_page and is_int(Silian_get_page["<page>"]) else 1
    Silian_start_index = (Silian_page - 1) * SONGS_PER_PAGE
    Silian_end_index = Silian_page * SONGS_PER_PAGE

    Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.new"))
    for elem in Silian_result_set[Silian_start_index:Silian_end_index]:
        Silian_msg_chain.append(Plain(f"{elem[0]} - {elem[1]}{' (DX)' if elem[2] == 'DX' else ''}"))

    if len(Silian_result_set) == 0:
        await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
    elif len(Silian_result_set) <= SONGS_PER_PAGE:
        await Silian_msg.finish(Silian_msg_chain)
    else:
        Silian_msg_chain.append(I18NContext("maimai.message.pages", page=Silian_page, total_pages=Silian_total_pages))
        Silian_imgs = await msgchain2image(Silian_msg_chain, Silian_msg)
        if Silian_imgs:
            await Silian_msg.finish(Silian_imgs)
        else:
            await Silian_msg.finish(Silian_msg_chain)


@Silian_mai.command(
    "search <keyword> [-p <page>] {{I18N:maimai.help.search}}",
    options_desc={"-p": "{I18N:maimai.help.option.p}"},
)
async def _(Silian_msg: Bot.MessageSession, Silian_keyword: str):
    Silian_name = Silian_keyword.strip()
    Silian_result_set = []
    Silian_data = (await Silian_total_list.get()).filter(title_search=Silian_name)
    if len(Silian_data) == 0:
        await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))

    for Silian_music in sorted(Silian_data, key=lambda Silian_i: int(Silian_i["id"])):
        Silian_result_set.append((Silian_music["id"], Silian_music["title"], Silian_music["type"]))
    Silian_total_pages = (len(Silian_result_set) + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE
    Silian_get_page = Silian_msg.parsed_msg.get("-p", False)
    Silian_page = max(min(int(Silian_get_page["<page>"]), Silian_total_pages), 1) if Silian_get_page and is_int(Silian_get_page["<page>"]) else 1
    Silian_start_index = (Silian_page - 1) * SONGS_PER_PAGE
    Silian_end_index = Silian_page * SONGS_PER_PAGE

    Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.search", keyword=Silian_name))
    for elem in Silian_result_set[Silian_start_index:Silian_end_index]:
        Silian_msg_chain.append(Plain(f"{elem[0]} - {elem[1]}{' (DX)' if elem[2] == 'DX' else ''}"))
    if len(Silian_data) <= SONGS_PER_PAGE:
        await Silian_msg.finish(Silian_msg_chain)
    else:
        Silian_msg_chain.append(I18NContext("maimai.message.pages", page=Silian_page, total_pages=Silian_total_pages))
        Silian_imgs = await msgchain2image(Silian_msg_chain, Silian_msg)
        if Silian_imgs:
            await Silian_msg.finish(Silian_imgs)
        else:
            await Silian_msg.finish(Silian_msg_chain)


@Silian_mai.command("alias <sid> {{I18N:maimai.help.alias}}")
async def _(Silian_msg: Bot.MessageSession, Silian_sid: str):
    if not is_int(Silian_sid):
        if Silian_sid[:2].lower() == "id":
            Silian_sid = Silian_sid[2:]
        else:
            await Silian_msg.finish(I18NContext("maimai.message.id_invalid"))
    await query_alias(Silian_msg, Silian_sid)


async def query_alias(msg, sid):
    music = (await Silian_total_list.get()).by_id(sid)
    if not music:
        await msg.finish(I18NContext("maimai.message.music_not_found"))

    Silian_title = f"{music['id']} - {music['title']}{' (DX)' if music['type'] == 'DX' else ''}"
    Silian_alias = await get_alias(msg, sid)
    if len(Silian_alias) == 0:
        await msg.finish(I18NContext("maimai.message.alias.alias_not_found"))
    else:
        Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.alias", title=Silian_title))
        for Silian_a in Silian_alias:
            Silian_msg_chain.append(Plain(Silian_a))

        if len(Silian_alias) >= 20:
            Silian_imgs = await msgchain2image(Silian_msg_chain, msg)
            if Silian_imgs:
                await msg.finish(Silian_imgs)
            else:
                await msg.finish(Silian_msg_chain)
        else:
            await msg.finish(Silian_msg_chain)


@Silian_mai.command("grade <grade> {{I18N:maimai.help.grade}}")
async def _(Silian_msg: Bot.MessageSession, Silian_grade: str):
    await get_grade_info(Silian_msg, Silian_grade)


@Silian_mai.command("chart <id_or_alias> {{I18N:maimai.help.chart}}")
async def _(Silian_msg: Bot.MessageSession, Silian_id_or_alias: str):
    if Silian_id_or_alias[:2].lower() == "id":
        sid = Silian_id_or_alias[2:]
    else:
        Silian_sid_list = await search_by_alias(Silian_id_or_alias)
        if len(Silian_sid_list) == 0:
            await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
        elif len(Silian_sid_list) > 1:
            Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.disambiguation"))
            for sid in sorted(Silian_sid_list, key=int):
                s = (await Silian_total_list.get()).by_id(sid)
                if s:
                    Silian_msg_chain.append(Plain(f"{s['id']} - {s['title']}{' (DX)' if s['type'] == 'DX' else ''}"))
            Silian_msg_chain.append(
                I18NContext("maimai.message.disambiguation.chart.prompt", prefix=Silian_msg.session_info.prefixes[0])
            )
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
        if utage_data[sid]["referrals_num"]["mode"] == "normal":
            Silian_chart = utage_data[sid]["charts"][0]
            Silian_msg_chain.append(
                I18NContext(
                    "maimai.message.chart.utage",
                    level=utage_data[sid]["level"][0],
                    player=utage_data[sid]["referrals_num"]["player"][0],
                    tap=Silian_chart["notes"][0],
                    hold=Silian_chart["notes"][1],
                    slide=Silian_chart["notes"][2],
                    touch=Silian_chart["notes"][3],
                    brk=Silian_chart["notes"][4],
                )
            )
        else:
            Silian_chartL = utage_data[sid]["charts"][0]
            Silian_chartR = utage_data[sid]["charts"][1]
            Silian_players = utage_data[sid]["referrals_num"]["player"]
            Silian_msg_chain.append(
                I18NContext(
                    "maimai.message.chart.utage.buddy",
                    level=utage_data[sid]["level"][0],
                    playerL=Silian_players[0],
                    playerR=Silian_players[1],
                    tapL=Silian_chartL["notes"][0],
                    tapR=Silian_chartR["notes"][0],
                    holdL=Silian_chartL["notes"][1],
                    holdR=Silian_chartR["notes"][1],
                    slideL=Silian_chartL["notes"][2],
                    slideR=Silian_chartR["notes"][2],
                    touchL=Silian_chartL["notes"][3],
                    touchR=Silian_chartR["notes"][3],
                    brkL=Silian_chartL["notes"][4],
                    brkR=Silian_chartR["notes"][4],
                )
            )
    else:
        for Silian_diff, Silian_ds in enumerate(Silian_music["ds"]):
            Silian_chart = Silian_music["charts"][Silian_diff]
            if len(Silian_chart["notes"]) == 4:
                Silian_msg_chain.append(
                    I18NContext(
                        "maimai.message.chart.sd",
                        diff=diff_list[Silian_diff],
                        level=Silian_music["level"][Silian_diff],
                        ds=Silian_ds,
                        tap=Silian_chart["notes"][0],
                        hold=Silian_chart["notes"][1],
                        slide=Silian_chart["notes"][2],
                        brk=Silian_chart["notes"][3],
                    )
                )
                if Silian_diff >= 2:
                    Silian_msg_chain.append(Plain(str(I18NContext("maimai.message.chart.charter")) + Silian_chart["charter"]))
            else:
                Silian_msg_chain.append(
                    I18NContext(
                        "maimai.message.chart.dx",
                        diff=diff_list[Silian_diff],
                        level=Silian_music["level"][Silian_diff],
                        ds=Silian_ds,
                        tap=Silian_chart["notes"][0],
                        hold=Silian_chart["notes"][1],
                        slide=Silian_chart["notes"][2],
                        touch=Silian_chart["notes"][3],
                        brk=Silian_chart["notes"][4],
                    )
                )
                if Silian_diff >= 2:
                    Silian_msg_chain.append(Plain(str(I18NContext("maimai.message.chart.charter")) + Silian_chart["charter"]))

    await Silian_msg.finish(await get_info(Silian_music, Silian_msg_chain))


@Silian_mai.command("id <id> {{I18N:maimai.help.id}}")
@Silian_mai.command("song <id_or_alias> {{I18N:maimai.help.song}}")
async def _(Silian_msg: Bot.MessageSession, Silian_id_or_alias: str):
    if "<id>" in Silian_msg.parsed_msg:
        sid = Silian_msg.parsed_msg["<id>"]
    elif Silian_id_or_alias[:2].lower() == "id":
        sid = Silian_id_or_alias[2:]
    else:
        Silian_sid_list = await search_by_alias(Silian_id_or_alias)
        if len(Silian_sid_list) == 0:
            await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
        elif len(Silian_sid_list) > 1:
            Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.disambiguation"))
            for sid in sorted(Silian_sid_list, key=int):
                s = (await Silian_total_list.get()).by_id(sid)
                if s:
                    Silian_msg_chain.append(Plain(f"{s['id']} - {s['title']}{' (DX)' if s['type'] == 'DX' else ''}"))
            Silian_msg_chain.append(
                I18NContext("maimai.message.disambiguation.song.prompt", prefix=Silian_msg.session_info.prefixes[0])
            )
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


@Silian_mai.command("random <diff+level> [<dx_type>] {{I18N:maimai.help.random.filter}}")
async def _(Silian_msg: Bot.MessageSession, Silian_dx_type: str = None):
    Silian_condit = Silian_msg.parsed_msg["<diff+level>"]
    Silian_level = ""
    Silian_diff = ""
    try:
        if Silian_dx_type in ["dx", "DX"]:
            Silian_dx_type_lst = ["DX"]
        elif Silian_dx_type in ["sd", "SD", "标准", "標準"]:
            Silian_dx_type_lst = ["SD"]
        else:
            Silian_dx_type_lst = ["SD", "DX"]

        for Silian_char in Silian_condit:
            if is_int(Silian_char) or Silian_char == "+":
                Silian_level += Silian_char
            else:
                Silian_diff += Silian_char

        if Silian_level == "":
            if Silian_diff == "*":
                Silian_music_data = (await Silian_total_list.get()).filter(dxtype=Silian_dx_type_lst)
            else:
                raise ValueError
        else:
            if Silian_diff == "":
                Silian_music_data = (await Silian_total_list.get()).filter(level=Silian_level, dxtype=Silian_dx_type_lst)
            else:
                Silian_music_data = (await Silian_total_list.get()).filter(level=Silian_level, diff=[get_diff(Silian_diff)], dxtype=Silian_dx_type_lst)

        if len(Silian_music_data) == 0:
            await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
        else:
            music = Silian_music_data.random()
            Silian_diffs = MessageChain.assign(Plain(f"{'/'.join(str(ds) for ds in music.ds)}"))
            await Silian_msg.finish(await get_info(music, Silian_diffs))
    except (ValueError, TypeError):
        await Silian_msg.finish(I18NContext("maimai.message.random.failed"))


@Silian_mai.command("random {{I18N:maimai.help.random}}")
async def _(Silian_msg: Bot.MessageSession):
    music = (await Silian_total_list.get()).random()
    Silian_diffs = MessageChain.assign(Plain(f"{'/'.join(str(ds) for ds in music.ds)}"))
    await Silian_msg.finish(await get_info(music, Silian_diffs))


@Silian_mai.command("scoreline <id_or_alias> <diff> {{I18N:maimai.help.scoreline}}")
async def _(Silian_msg: Bot.MessageSession, Silian_id_or_alias: str, Silian_diff: str):
    if Silian_id_or_alias[:2].lower() == "id":
        Silian_sid = Silian_id_or_alias[2:]
    else:
        Silian_sid_list = await search_by_alias(Silian_id_or_alias)
        if len(Silian_sid_list) == 0:
            await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
        elif len(Silian_sid_list) > 1:
            Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.disambiguation"))
            for Silian_sid in sorted(Silian_sid_list, key=int):
                s = (await Silian_total_list.get()).by_id(Silian_sid)
                if s:
                    Silian_msg_chain.append(Plain(f"{s['id']} - {s['title']}{' (DX)' if s['type'] == 'DX' else ''}"))
            Silian_msg_chain.append(
                I18NContext("maimai.message.disambiguation.scoreline.prompt", prefix=Silian_msg.session_info.prefixes[0])
            )
            await Silian_msg.finish(Silian_msg_chain)
        else:
            Silian_sid = str(Silian_sid_list[0])

    music = (await Silian_total_list.get()).by_id(Silian_sid)
    if not music:
        await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))

    try:
        diff_index = get_diff(Silian_diff)
        Silian_chart = music["charts"][diff_index]
    except IndexError:
        await Silian_msg.finish(I18NContext("maimai.message.chart_not_found"))

    try:
        Silian_tap = int(Silian_chart["notes"][0])
        Silian_slide = int(Silian_chart["notes"][2])
        Silian_hold = int(Silian_chart["notes"][1])
        Silian_touch = int(Silian_chart["notes"][3]) if len(Silian_chart["notes"]) == 5 else 0
        Silian_brk = int(Silian_chart["notes"][-1])

        Silian_total_score = Silian_tap * 500 + Silian_slide * 1500 + Silian_hold * 1000 + Silian_touch * 500 + Silian_brk * 2500  # 基础分
        Silian_bonus_score = Silian_total_score * 0.01 / Silian_brk  # 奖励分
        break_2550_reduce = Silian_bonus_score * 0.25  # 一个 BREAK 2550 减少 25% 奖励分
        break_2000_reduce = Silian_bonus_score * 0.6 + 500  # 一个 BREAK 2000 减少 500 基础分和 60% 奖励分
        Silian_b2t_2550_great = f"{(break_2550_reduce / 100):.3f}"  # 一个 TAP GREAT 减少 100 分
        Silian_b2t_2000_great = f"{(break_2000_reduce / 100):.3f}"  # 一个 TAP GREAT 减少 100 分

        Silian_msg_chain = MessageChain.assign(
            [
                Plain(
                    f"{music['id']} - {music['title']}{' (DX)' if music['type'] == 'DX' else ''} [{diff_list[diff_index]}]"
                ),
                BImage(draw_scoreline_table(Silian_tap, Silian_hold, Silian_slide, Silian_touch, Silian_brk, "101-")),
                I18NContext("maimai.message.scoreline", b2t_2550_great=Silian_b2t_2550_great, b2t_2000_great=Silian_b2t_2000_great),
            ]
        )
        await Silian_msg.finish(Silian_msg_chain)
    except ValueError:
        await Silian_msg.finish(I18NContext("maimai.message.scoreline.failed", prefix=Silian_msg.session_info.prefixes[0]))


@Silian_mai.command("calc <base> <score> {{I18N:maimai.help.calc}}")
async def _(Silian_msg: Bot.MessageSession, Silian_base: float, Silian_score: float):
    await Silian_msg.finish(Plain(compute_rating(Silian_base, Silian_score)))


@Silian_mai.command("bind <username> {{I18N:maimai.help.bind.lx}}")
async def _(Silian_msg: Bot.MessageSession, Silian_username: str):
    if await get_record(Silian_msg, {"username": Silian_username}, use_cache=False):
        await DivingProberBindInfo.set_bind_info(sender_id=Silian_msg.session_info.sender_id, username=Silian_username)
        await Silian_msg.finish(str(I18NContext("maimai.message.bind.success")) + Silian_username)


@Silian_mai.command("unbind {{I18N:maimai.help.unbind}}")
async def _(Silian_msg: Bot.MessageSession):
    await DivingProberBindInfo.remove_bind_info(sender_id=Silian_msg.session_info.sender_id)
    await Silian_msg.finish(I18NContext("maimai.message.unbind.success"))


@Silian_mai.command("b50 {{I18N:maimai.help.b50}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_payload = await get_diving_prober_bind_info(Silian_msg, b50=True)
    Silian_img = await generate_b50(Silian_msg, Silian_payload)
    if Silian_img:
        await Silian_msg.finish(BImage(Silian_img))


@Silian_mai.command("score <id_or_alias> {{I18N:maimai.help.score}}")
async def _(Silian_msg: Bot.MessageSession, Silian_id_or_alias: str):
    await query_song_score(Silian_msg, Silian_id_or_alias)


async def query_song_score(msg, query):
    if query[:2].lower() == "id":
        Silian_sid = query[2:]
    else:
        Silian_sid_list = await search_by_alias(query)

        if len(Silian_sid_list) == 0:
            await msg.finish(I18NContext("maimai.message.music_not_found"))
        elif len(Silian_sid_list) > 1:
            Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.disambiguation"))
            for Silian_sid in sorted(Silian_sid_list, key=int):
                s = (await Silian_total_list.get()).by_id(Silian_sid)
                if s:
                    Silian_msg_chain.append(Plain(f"{s['id']} - {s['title']}{' (DX)' if s['type'] == 'DX' else ''}"))
            Silian_msg_chain.append(
                I18NContext("maimai.message.disambiguation.score.prompt", prefix=msg.session_info.prefixes[0])
            )
            await msg.finish(Silian_msg_chain)
        else:
            Silian_sid = str(Silian_sid_list[0])

    Silian_music = (await Silian_total_list.get()).by_id(Silian_sid)
    if not Silian_music:
        await msg.finish(I18NContext("maimai.message.music_not_found"))

    Silian_payload = await get_diving_prober_bind_info(msg)
    Silian_output = await get_player_score(msg, Silian_payload, Silian_sid)
    await msg.finish(await get_info(Silian_music, Silian_output))


@Silian_mai.command("plate <plate> [-l] {{I18N:maimai.help.plate}}", options_desc={"-l": "{I18N:maimai.help.option.l}"})
async def _(Silian_msg: Bot.MessageSession, Silian_plate: str):
    Silian_get_list = Silian_msg.parsed_msg.get("-l", False)
    await query_plate(Silian_msg, Silian_plate, Silian_get_list)


async def query_plate(msg, plate, get_list=False):
    Silian_payload = await get_diving_prober_bind_info(msg)

    if plate in ["真将", "真將"] or (plate[1] == "者" and plate[0] not in ["覇", "霸"]):
        await msg.finish(I18NContext("maimai.message.plate.plate_not_found"))

    if get_list:
        Silian_img = await generate_plate(msg, Silian_payload, plate)
        if Silian_img:
            await msg.finish(BImage(Silian_img))
    else:
        Silian_output, Silian_get_img = await get_plate_process(msg, Silian_payload, plate)

        if Silian_get_img:
            Silian_imgs = await msgchain2image(Silian_output, msg)
            if Silian_imgs:
                await msg.finish(Silian_imgs)
            else:
                await msg.finish(Silian_output)
        else:
            await msg.finish(Silian_output)


@Silian_mai.command(
    "process <level> <goal> [-l] {{I18N:maimai.help.process}}", options_desc={"-l": "{I18N:maimai.help.option.l}"}
)
async def _(Silian_msg: Bot.MessageSession, Silian_level: str, Silian_goal: str):
    Silian_get_list = Silian_msg.parsed_msg.get("-l", False)
    await query_process(Silian_msg, Silian_level, Silian_goal, Silian_get_list)


async def query_process(msg, level, goal, get_list=False):
    Silian_payload = await get_diving_prober_bind_info(msg)

    if level not in level_list:
        await msg.finish(I18NContext("maimai.message.level_invalid"))
    if goal.upper() not in goal_list:
        await msg.finish(I18NContext("maimai.message.goal_invalid"))

    if get_list:
        Silian_img = await generate_process(msg, Silian_payload, level, goal)
        if Silian_img:
            await msg.finish(BImage(Silian_img))
    else:
        Silian_output, Silian_get_img = await get_level_process(msg, Silian_payload, level, goal)

        if Silian_get_img:
            Silian_imgs = await msgchain2image(Silian_output, msg)
            if Silian_imgs:
                await msg.finish(Silian_imgs)
            else:
                await msg.finish(Silian_output)
        else:
            await msg.finish(Silian_output)


@Silian_mai.command("rank {{I18N:maimai.help.rank}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_payload = await get_diving_prober_bind_info(Silian_msg)
    await get_rank(Silian_msg, Silian_payload)


@Silian_mai.command(
    "scorelist <level> [-p <page>] {{I18N:maimai.help.scorelist}}", options_desc={"-p": "{I18N:maimai.help.option.p}"}
)
async def _(Silian_msg: Bot.MessageSession, Silian_level: str):
    Silian_get_page = Silian_msg.parsed_msg.get("-p", False)
    Silian_page = Silian_get_page["<page>"] if Silian_get_page and is_int(Silian_get_page["<page>"]) else 1

    Silian_payload = await get_diving_prober_bind_info(Silian_msg)
    Silian_output, Silian_get_img = await get_score_list(Silian_msg, Silian_payload, Silian_level, Silian_page)

    if Silian_get_img:
        Silian_imgs = await msgchain2image(Silian_output, Silian_msg)
        if Silian_imgs:
            await Silian_msg.finish(Silian_imgs)
        else:
            await Silian_msg.finish(Silian_output)
    else:
        await Silian_msg.finish(Silian_output)


@Silian_mai.command("update [--no-cover]", required_superuser=True)
async def _(Silian_msg: Bot.MessageSession):
    if Silian_msg.parsed_msg.get("--no-cover", False):
        Silian_actions = await update_alias() and await Silian_total_list.update()
    else:
        Silian_actions = await update_alias() and await update_cover() and await Silian_total_list.update()
    if Silian_actions:
        await Silian_msg.finish(I18NContext("message.success"))
    else:
        await Silian_msg.finish(I18NContext("message.failed"))


@Silian_mai.schedule(CronTrigger.from_crontab("0 0 * * *"))
async def _():
    Logger.info("Updating Maimai alias...")
    await update_alias()
