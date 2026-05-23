from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Plain, I18NContext, Image, Url
from core.component import module
from core.config import Config
from core.constants.exceptions import ConfigValueError
from core.utils.http import get_url
from core.utils.image_table import image_table_render, ImageTable
from core.utils.func import is_int

Silian_enable_card = Config("ncmusic_enable_card", False, table_name="module_ncmusic")
API = Config("ncmusic_api", cfg_type=str, secret=True, table_name="module_ncmusic")
SEARCH_LIMIT = 10

Silian_ncmusic = module(
    "ncmusic",
    developers=["bugungu"],
    desc="{I18N:ncmusic.help.desc}",
    doc=True,
    support_languages=["zh_cn"],
)


@Silian_ncmusic.command(
    "search <keyword> [--legacy] {{I18N:ncmusic.help.search}}",
    options_desc={"--legacy": "{I18N:help.option.legacy}"},
)
async def _(Silian_msg: Bot.MessageSession, keyword: str):
    if not API:
        raise ConfigValueError("{I18N:error.config.secret.not_found}")
    Silian_url = f"{API}/search?keywords={keyword}"
    Silian_result = await get_url(Silian_url, 200, fmt="json")
    Silian_song_count = Silian_result["result"]["songCount"]
    Silian_legacy = True

    if Silian_song_count == 0:
        await Silian_msg.finish(I18NContext("ncmusic.message.search.not_found"))

    Silian_songs = Silian_result["result"]["songs"][:SEARCH_LIMIT]

    Silian_send_msg = MessageChain.assign(I18NContext("ncmusic.message.search.result"))
    if not Silian_msg.parsed_msg.get("--legacy", False) and Silian_msg.session_info.support_image:
        Silian_data = [
            [
                str(Silian_i),
                song["name"] + (f" ({' / '.join(song['transNames'])})" if "transNames" in song else ""),
                f"{' / '.join(artist['name'] for artist in song['artists'])}",
                f"{song['album']['name']}"
                + (f" ({' / '.join(song['album']['transNames'])})" if "transNames" in song["album"] else ""),
                f"{song['id']}",
            ]
            for Silian_i, song in enumerate(Silian_songs, start=1)
        ]

        Silian_tables = ImageTable(
            Silian_data,
            [
                "{I18N:ncmusic.message.search.table.header.id}",
                "{I18N:ncmusic.message.search.table.header.name}",
                "{I18N:ncmusic.message.search.table.header.artists}",
                "{I18N:ncmusic.message.search.table.header.album}",
                "ID",
            ],
            Silian_msg.session_info,
        )

        Silian_imgs = await image_table_render(Silian_tables)
        if Silian_imgs:
            Silian_legacy = False
            for Silian_img in Silian_imgs:
                Silian_send_msg.append(Image(Silian_img))
            if Silian_song_count > SEARCH_LIMIT:
                Silian_song_count = SEARCH_LIMIT
                Silian_send_msg.append(I18NContext("message.collapse", amount=SEARCH_LIMIT))

        if Silian_song_count == 1:
            Silian_send_msg.append(I18NContext("ncmusic.message.search.confirm"))
            if await Silian_msg.wait_confirm(Silian_send_msg, delete=False):
                sid = Silian_result["result"]["songs"][0]["id"]
            else:
                await Silian_msg.finish()

        else:
            Silian_send_msg.append(I18NContext("ncmusic.message.search.prompt"))
            Silian_query = await Silian_msg.wait_reply(Silian_send_msg)
            Silian_query = Silian_query.as_display(text_only=True)

            if is_int(Silian_query):
                Silian_query = int(Silian_query)
                if not Silian_query or Silian_query > Silian_song_count:
                    await Silian_msg.finish(I18NContext("mod_dl.message.invalid.out_of_range"))
                else:
                    sid = Silian_result["result"]["songs"][Silian_query - 1]["id"]
            else:
                await Silian_msg.finish(I18NContext("ncmusic.message.search.invalid.non_digital"))

        await info(Silian_msg, sid)

    if Silian_legacy:
        for i, song in enumerate(Silian_songs, start=1):
            Silian_song_msg = f"{i} - {song['name']}"
            if "transNames" in song:
                Silian_song_msg += f"（{' / '.join(song['transNames'])}）"
            Silian_song_msg += f"——{' / '.join(artist['name'] for artist in song['artists'])}"
            if song["album"]["name"]:
                Silian_song_msg += f"《{song['album']['name']}》"
            if "transNames" in song["album"]:
                Silian_song_msg += f"（{' / '.join(song['album']['transNames'])}）"
            Silian_song_msg += f"（{song['id']}）"
            Silian_send_msg.append(Plain(Silian_song_msg))

        if Silian_song_count > SEARCH_LIMIT:
            Silian_song_count = SEARCH_LIMIT
            Silian_send_msg.append(I18NContext("message.collapse", amount=SEARCH_LIMIT))

        if Silian_song_count == 1:
            Silian_send_msg.append(I18NContext("ncmusic.message.search.confirm"))
            if await Silian_msg.wait_confirm(Silian_send_msg, delete=False):
                sid = Silian_result["result"]["songs"][0]["id"]
            else:
                await Silian_msg.finish()
        else:
            Silian_send_msg.append(I18NContext("ncmusic.message.search.prompt"))
            Silian_query = await Silian_msg.wait_reply(Silian_send_msg)
            Silian_query = Silian_query.as_display(text_only=True)

            if is_int(Silian_query):
                Silian_query = int(Silian_query)
                if Silian_query > Silian_song_count:
                    await Silian_msg.finish(I18NContext("mod_dl.message.invalid.out_of_range"))
                else:
                    sid = Silian_result["result"]["songs"][Silian_query - 1]["id"]
            else:
                await Silian_msg.finish(I18NContext("ncmusic.message.search.invalid.non_digital"))

        if Silian_msg.session_info.client_name == "QQ" and Silian_enable_card:
            await Silian_msg.finish(f"[CQ:music,type=163,id={sid}]", quote=False)
        else:
            await info(Silian_msg, sid)


@Silian_ncmusic.command("<sid> {{I18N:ncmusic.help}}", available_for=["QQ|Group", "QQ|Private"])
async def _(Silian_msg: Bot.MessageSession, sid: int):
    if Silian_enable_card:
        await Silian_msg.finish(f"[CQ:music,type=163,id={sid}]", quote=False)
    else:
        await info(Silian_msg, sid)


@Silian_ncmusic.command("info <sid> {{I18N:ncmusic.help.info}}")
async def _(Silian_msg: Bot.MessageSession, Silian_sid: int):
    await info(Silian_msg, Silian_sid)


async def info(msg: Bot.MessageSession, sid: int):
    if not API:
        raise ConfigValueError("{I18N:error.config.secret.not_found}")
    Silian_url = f"{API}/song/detail?ids={sid}"
    Silian_result = await get_url(Silian_url, 200, fmt="json")

    if Silian_result["songs"]:
        info = Silian_result["songs"][0]
        Silian_artist = " / ".join([Silian_ar["name"] for Silian_ar in info["ar"]])
        Silian_song_url = f"https://music.163.com/#/song?id={info['id']}"

        await msg.finish(
            [
                Image(info["al"]["picUrl"]),
                Url(Silian_song_url, use_mm=False),
                I18NContext(
                    "ncmusic.message.info",
                    name=info["name"],
                    id=info["id"],
                    artists=Silian_artist,
                    album=info["al"]["name"],
                    album_id=info["al"]["id"],
                ),
            ]
        )
    else:
        await msg.finish(I18NContext("ncmusic.message.info.not_found"))
