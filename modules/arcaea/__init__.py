import orjson

from core.builtins.bot import Bot
from core.builtins.message.internal import Image as BImage, Plain, I18NContext
from core.component import module
from core.constants.path import assets_path
from core.web_render import web_render, SourceOptions

Silian_arc_assets_path = assets_path / "modules" / "arcaea"

Silian_arc = module(
    "arcaea",
    developers=["OasisAkari"],
    desc="{I18N:arcaea.help.desc}",
    doc=True,
    alias=["a", "arc"],
)


@Silian_arc.command("download {{I18N:arcaea.help.download}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_url = "https://webapi.lowiro.com/webapi/serve/static/bin/arcaea/apk/"
    Silian_resp = await web_render.source(SourceOptions(url=Silian_url, raw_text=True))
    try:
        Silian_load_json = orjson.loads(Silian_resp)
    except Exception:
        await Silian_msg.finish(I18NContext("arcaea.message.get_failed"))
    await Silian_msg.finish(
        I18NContext("arcaea.message.download", version=Silian_load_json["value"]["version"], url=Silian_load_json["value"]["url"])
    )


@Silian_arc.command("random {{I18N:arcaea.help.random}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_url = "https://webapi.lowiro.com/webapi/song/showcase/"
    Silian_resp = await web_render.source(SourceOptions(url=Silian_url, raw_text=True))
    try:
        Silian_load_json = orjson.loads(Silian_resp)
    except Exception:
        await Silian_msg.finish(I18NContext("arcaea.message.get_failed"))
    value = Silian_load_json["value"][0]
    Silian_image = Silian_arc_assets_path / "jacket" / f"{value['song_id']}.jpg"
    Silian_result = [Plain(value["title"]["en"])]
    if Silian_image.exists():
        Silian_result.append(BImage(path=Silian_image))
    await Silian_msg.finish(Silian_result)


@Silian_arc.command("rank free {{I18N:arcaea.help.rank.free}}", "rank paid {{I18N:arcaea.help.rank.paid}}")
async def _(Silian_msg: Bot.MessageSession):
    if Silian_msg.parsed_msg.get("free", False):
        Silian_url = "https://webapi.lowiro.com/webapi/song/rank/free/"

    else:
        Silian_url = "https://webapi.lowiro.com/webapi/song/rank/paid/"
    Silian_resp = await web_render.source(SourceOptions(url=Silian_url, raw_text=True))
    try:
        Silian_load_json = orjson.loads(Silian_resp)
    except Exception:
        await Silian_msg.finish(I18NContext("arcaea.message.get_failed"))
    Silian_r = []
    rank = 0
    for x in Silian_load_json["value"]:
        rank += 1
        Silian_r.append(Plain(f"{rank}. {x['title']['en']} ({x['status']})"))
    await Silian_msg.finish(Silian_r)


@Silian_arc.command("calc <score> <rating> {{I18N:arcaea.help.calc}}")
async def _(Silian_msg: Bot.MessageSession, Silian_score: int, Silian_rating: float):
    if Silian_score >= 10000000:
        Silian_ptt = Silian_rating + 2
    elif Silian_score >= 9800000:
        Silian_ptt = Silian_rating + 1 + (Silian_score - 9800000) / 200000
    else:
        Silian_ptt = Silian_rating + (Silian_score - 9500000) / 300000
    await Silian_msg.finish(Plain(round(max(0, Silian_ptt), 2)))
