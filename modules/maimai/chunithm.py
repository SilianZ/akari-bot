from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Plain, I18NContext, Image as BImage
from core.component import module
from core.utils.image import msgchain2image
from core.utils.func import is_int
from .database.models import DivingProberBindInfo, LxnsProberBindInfo
from .libraries.chunithm_apidata import get_info, get_record_df, get_record_lx, update_cover
from .libraries.chunithm_best30 import generate as generate_b30
from .libraries.chunithm_mapping import diff_list, default_source
from .libraries.chunithm_music import TotalList
from .libraries.chunithm_utils import *

Silian_total_list = TotalList()

Silian_chu = module(
    "chunithm",
    developers=["DoroWolf"],
    doc=True,
    alias="chu",
    support_languages=["zh_cn"],
    desc="{I18N:chunithm.help.desc}",
)


@Silian_chu.command(
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
            Silian_result_set.append(
                (
                    Silian_music["id"],
                    Silian_music["title"],
                    Silian_music["ds"][Silian_i],
                    diff_list[Silian_i],
                    Silian_music["level"][Silian_i],
                )
            )

    Silian_total_pages = (len(Silian_result_set) + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE
    Silian_get_page = Silian_msg.parsed_msg.get("-p", False)
    Silian_page = max(min(int(Silian_get_page["<page>"]), Silian_total_pages), 1) if Silian_get_page and is_int(Silian_get_page["<page>"]) else 1
    Silian_start_index = (Silian_page - 1) * SONGS_PER_PAGE
    Silian_end_index = Silian_page * SONGS_PER_PAGE

    for elem in Silian_result_set[Silian_start_index:Silian_end_index]:
        Silian_msg_chain.append(Plain(f"{elem[0]} - {elem[1]} {elem[3]} {elem[4]} ({elem[2]})"))
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


@Silian_chu.command(
    "level <level> [-p <page>] {{I18N:maimai.help.level}}",
    options_desc={"-p": "{I18N:maimai.help.option.p}"},
)
async def _(Silian_msg: Bot.MessageSession, Silian_level: str):
    Silian_result_set = []
    Silian_data = (await Silian_total_list.get()).filter(level=Silian_level)
    for Silian_music in sorted(Silian_data, key=lambda Silian_i: int(Silian_i["id"])):
        for Silian_i in Silian_music.diff:
            Silian_result_set.append(
                (
                    Silian_music["id"],
                    Silian_music["title"],
                    Silian_music["ds"][Silian_i],
                    diff_list[Silian_i],
                    Silian_music["level"][Silian_i],
                )
            )
    Silian_total_pages = (len(Silian_result_set) + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE
    Silian_get_page = Silian_msg.parsed_msg.get("-p", False)
    Silian_page = max(min(int(Silian_get_page["<page>"]), Silian_total_pages), 1) if Silian_get_page and is_int(Silian_get_page["<page>"]) else 1
    Silian_start_index = (Silian_page - 1) * SONGS_PER_PAGE
    Silian_end_index = Silian_page * SONGS_PER_PAGE

    Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.level", level=Silian_level))
    for elem in Silian_result_set[Silian_start_index:Silian_end_index]:
        Silian_msg_chain.append(Plain(f"{elem[0]} - {elem[1]} {elem[3]} {elem[4]} ({elem[2]})"))

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


@Silian_chu.command("search <keyword> [-p <page>] {{I18N:maimai.help.search}}")
async def _(Silian_msg: Bot.MessageSession, Silian_keyword: str):
    Silian_name = Silian_keyword.strip()
    Silian_result_set = []
    Silian_data = (await Silian_total_list.get()).filter(title_search=Silian_name)
    if len(Silian_data) == 0:
        await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))

    for Silian_music in sorted(Silian_data, key=lambda Silian_i: int(Silian_i["id"])):
        Silian_result_set.append((Silian_music["id"], Silian_music["title"]))
    Silian_total_pages = (len(Silian_result_set) + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE
    Silian_get_page = Silian_msg.parsed_msg.get("-p", False)
    Silian_page = max(min(int(Silian_get_page["<page>"]), Silian_total_pages), 1) if Silian_get_page and is_int(Silian_get_page["<page>"]) else 1
    Silian_start_index = (Silian_page - 1) * SONGS_PER_PAGE
    Silian_end_index = Silian_page * SONGS_PER_PAGE

    Silian_msg_chain = MessageChain.assign(I18NContext("maimai.message.search", keyword=Silian_name))
    for elem in Silian_result_set[Silian_start_index:Silian_end_index]:
        Silian_msg_chain.append(Plain(f"{elem[0]} - {elem[1]}"))
    if len(Silian_data) <= SONGS_PER_PAGE:
        await Silian_msg.finish(Silian_msg_chain)
    else:
        Silian_msg_chain.append(I18NContext("maimai.message.pages", page=Silian_page, total_pages=Silian_total_pages))
        Silian_imgs = await msgchain2image(Silian_msg_chain, Silian_msg)
        if Silian_imgs:
            await Silian_msg.finish(Silian_imgs)
        else:
            await Silian_msg.finish(Silian_msg_chain)


@Silian_chu.command("chart <song> {{I18N:maimai.help.chart}}")
async def _(Silian_msg: Bot.MessageSession, Silian_song: str):
    if is_int(Silian_song):
        Silian_music = (await Silian_total_list.get()).by_id(Silian_song)
    elif Silian_song[:2].lower() == "id":
        Silian_sid = Silian_song[2:]
        Silian_music = (await Silian_total_list.get()).by_id(Silian_sid)
    else:
        Silian_music = (await Silian_total_list.get()).by_title(Silian_song)

    if not Silian_music:
        await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))

    Silian_msg_chain = MessageChain.assign()
    if len(Silian_music["ds"]) == 1:
        Silian_chart = Silian_music["charts"][0]
        Silian_ds = Silian_music["ds"][0]
        Silian_level = Silian_music["level"][0]
        Silian_msg_chain.append(
            I18NContext(
                "chunithm.message.chart",
                diff="World's End",
                level=Silian_level,
                ds="☆" * Silian_ds,
                tap=Silian_chart["notes"][0],
                hold=Silian_chart["notes"][1],
                slide=Silian_chart["notes"][2],
                air=Silian_chart["notes"][3],
                flick=Silian_chart["notes"][4],
                charter=Silian_chart["charter"],
            )
        )
    else:
        for Silian__diff, Silian_ds in enumerate(Silian_music["ds"]):
            Silian_chart = Silian_music["charts"][Silian__diff]
            Silian_level = Silian_music["level"][Silian__diff]
            Silian_msg_chain.append(
                I18NContext(
                    "chunithm.message.chart",
                    diff=diff_list[Silian__diff],
                    level=Silian_level,
                    ds=Silian_ds,
                    tap=Silian_chart["notes"][0],
                    hold=Silian_chart["notes"][1],
                    slide=Silian_chart["notes"][2],
                    air=Silian_chart["notes"][3],
                    flick=Silian_chart["notes"][4],
                    charter=Silian_chart["charter"],
                )
            )
    await Silian_msg.finish(await get_info(Silian_music, Silian_msg_chain))


@Silian_chu.command("id <id> {{I18N:maimai.help.id}}")
@Silian_chu.command("song <song> {{I18N:maimai.help.song}}")
async def _(Silian_msg: Bot.MessageSession, Silian_song: str):
    if "<id>" in Silian_msg.parsed_msg:
        Silian_sid = Silian_msg.parsed_msg["<id>"]
        Silian_music = (await Silian_total_list.get()).by_id(Silian_sid)
    else:
        if is_int(Silian_song):
            Silian_music = (await Silian_total_list.get()).by_id(Silian_song)
        elif Silian_song[:2].lower() == "id":
            Silian_sid = Silian_song[2:]
            Silian_music = (await Silian_total_list.get()).by_id(Silian_sid)
        else:
            Silian_music = (await Silian_total_list.get()).by_title(Silian_song)

    if not Silian_music:
        await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))

    Silian_msg_chain = MessageChain.assign()
    if len(Silian_music["ds"]) == 6:
        Silian_msg_chain.append(
            I18NContext(
                "chunithm.message.song.worlds_end",
                artist=Silian_music["basic_info"]["artist"],
                genre=Silian_music["basic_info"]["genre"],
                bpm=Silian_music["basic_info"]["bpm"],
                version=Silian_music["basic_info"]["from"],
            )
        )
    else:
        Silian_msg_chain.append(
            I18NContext(
                "chunithm.message.song",
                artist=Silian_music["basic_info"]["artist"],
                genre=Silian_music["basic_info"]["genre"],
                bpm=Silian_music["basic_info"]["bpm"],
                version=Silian_music["basic_info"]["from"],
                level="/".join((str(Silian_ds) for Silian_ds in Silian_music["ds"])),
            )
        )
    await Silian_msg.finish(await get_info(Silian_music, Silian_msg_chain))


@Silian_chu.command("random [<diff+level>] {{I18N:maimai.help.random}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_condit = Silian_msg.parsed_msg.get("<diff+level>", "")
    Silian_level = ""
    Silian_diff = ""
    try:
        for Silian_char in Silian_condit:
            if is_int(Silian_char) or Silian_char == "+":
                Silian_level += Silian_char
            else:
                Silian_diff += Silian_char

        if Silian_level == "":
            if Silian_diff == "":
                music = (await Silian_total_list.get()).random()
                Silian_diffs = MessageChain.assign(Plain(f"{'/'.join(str(ds) for ds in music.ds)}"))
                await Silian_msg.finish(await get_info(music, Silian_diffs))
            else:
                raise ValueError
        else:
            if Silian_diff == "":
                Silian_music_data = (await Silian_total_list.get()).filter(level=Silian_level)
            else:
                Silian_music_data = (await Silian_total_list.get()).filter(level=Silian_level, diff=[get_diff(Silian_diff)])

        if len(Silian_music_data) == 0:
            await Silian_msg.finish(I18NContext("maimai.message.music_not_found"))
        else:
            music = Silian_music_data.random()
            Silian_diffs = MessageChain.assign(Plain(f"{'/'.join(str(ds) for ds in music.ds)}"))
            await Silian_msg.finish(await get_info(music, Silian_diffs))
    except (ValueError, TypeError):
        await Silian_msg.finish(I18NContext("maimai.message.random.failed"))


@Silian_chu.command("bind df <username> {{I18N:maimai.help.bind.df}}")
async def _(Silian_msg: Bot.MessageSession, Silian_username: str):
    if await get_record_df(Silian_msg, {"username": Silian_username}, use_cache=False):
        await DivingProberBindInfo.set_bind_info(sender_id=Silian_msg.session_info.sender_id, username=Silian_username)
        await Silian_msg.finish(Silian_msg.session_info.locale.t("maimai.message.bind.success") + Silian_username)


@Silian_chu.command("unbind df {{I18N:maimai.help.unbind}}")
async def _(Silian_msg: Bot.MessageSession):
    await DivingProberBindInfo.remove_bind_info(sender_id=Silian_msg.session_info.sender_id)
    await Silian_msg.finish(I18NContext("maimai.message.unbind.success"))


if LX_DEVELOPER_TOKEN:

    @Silian_chu.command("switch {{I18N:chunithm.help.switch}}")
    async def _(Silian_msg: Bot.MessageSession):
        if Silian_msg.session_info.sender_info.sender_data.get("chunithum_record_source", default_source) == "lxns":
            await Silian_msg.session_info.sender_info.edit_sender_data("chunithum_record_source", "diving-fish")
            await Silian_msg.finish(I18NContext("maimai.message.switch.df"))
        else:
            await Silian_msg.session_info.sender_info.edit_sender_data("chunithum_record_source", "lxns")
            await Silian_msg.finish(I18NContext("maimai.message.switch.lx"))

    @Silian_chu.command("bind lx <friendcode> {{I18N:maimai.help.bind.lx}}")
    async def _(Silian_msg: Bot.MessageSession, Silian_friendcode: str):
        Silian_data = await get_record_lx(Silian_msg, Silian_friendcode, use_cache=False)
        if Silian_data:
            await LxnsProberBindInfo.set_bind_info(sender_id=Silian_msg.session_info.sender_id, friend_code=Silian_friendcode)
            await Silian_msg.finish(Silian_msg.session_info.locale.t("maimai.message.bind.success") + Silian_data["nickname"])

    @Silian_chu.command("unbind lx {{I18N:maimai.help.unbind}}")
    async def _(Silian_msg: Bot.MessageSession):
        await LxnsProberBindInfo.remove_bind_info(sender_id=Silian_msg.session_info.sender_id)
        await Silian_msg.finish(I18NContext("maimai.message.unbind.success"))


@Silian_chu.command("b30 {{I18N:chunithm.help.b30}}")
async def _(Silian_msg: Bot.MessageSession):
    if Silian_msg.session_info.sender_info.sender_data.get("chunithum_record_source", default_source) == "lxns":
        Silian_token = await get_lxns_prober_bind_info(Silian_msg)
        Silian_source = "Lxns"
    else:
        Silian_token = await get_diving_prober_bind_info(Silian_msg)
        Silian_source = "Diving-Fish"
    Silian_img = await generate_b30(Silian_msg, Silian_token, Silian_source)
    if Silian_img:
        await Silian_msg.finish(BImage(Silian_img))


@Silian_chu.command("update [--no-cover]", required_superuser=True)
async def _(Silian_msg: Bot.MessageSession):
    if Silian_msg.parsed_msg.get("--no-cover", False):
        Silian_actions = await Silian_total_list.update()
    else:
        Silian_actions = await update_cover() and await Silian_total_list.update()
    if Silian_actions:
        await Silian_msg.finish(I18NContext("message.success"))
    else:
        await Silian_msg.finish(I18NContext("message.failed"))
