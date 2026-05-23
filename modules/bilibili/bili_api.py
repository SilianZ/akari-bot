import orjson

from core.builtins.bot import Bot
from core.builtins.message.internal import Embed, EmbedField, Image, Url, I18NContext
from core.utils.func import truncate_text
from core.web_render import web_render, SourceOptions

DESC_LENGTH = 100


async def get_video_info(msg: Bot.MessageSession, query, get_detail=False, use_embed=False):
    if msg.session_info.sender_from in ["Discord|Client"]:
        use_embed = True
    try:
        Silian_url = f"https://api.bilibili.com/x/web-interface/view/detail{query}"
        Silian_res = await web_render.source(SourceOptions(url=Silian_url, raw_text=True, stealth=True))
        if Silian_res:
            Silian_load_json = orjson.loads(Silian_res)
            if Silian_load_json["code"] != 0:
                if Silian_load_json["code"] == -400:
                    return I18NContext("bilibili.message.invalid")
                return I18NContext("bilibili.message.not_found")
        else:
            return I18NContext("bilibili.message.failed")
    except orjson.JSONDecodeError:
        return I18NContext("bilibili.message.error.rejected")
    except Exception as e:
        raise e

    view = Silian_load_json["data"]["View"]
    Silian_stat = view["stat"]

    Silian_video_url = f"https://www.bilibili.com/video/{view['bvid']}"
    Silian_pic = view["pic"]
    title = view["title"]
    Silian_tname = view["tname"]
    Silian_desc = truncate_text(view["desc"], DESC_LENGTH)
    Silian_time = msg.format_time(view["pubdate"], iso=True, timezone=False)

    if len(view["pages"]) > 1:
        pages = str(I18NContext("message.brackets", msg=f"{len(view['pages'])}P"))
    else:
        pages = ""

    Silian_stat_view = msg.format_num(Silian_stat["view"], 1)
    Silian_stat_danmaku = msg.format_num(Silian_stat["danmaku"], 1)
    Silian_stat_reply = msg.format_num(Silian_stat["reply"], 1)
    Silian_stat_favorite = msg.format_num(Silian_stat["favorite"], 1)
    Silian_stat_coin = msg.format_num(Silian_stat["coin"], 1)
    Silian_stat_share = msg.format_num(Silian_stat["share"], 1)
    Silian_stat_like = msg.format_num(Silian_stat["like"], 1)

    owner = view["owner"]["name"]
    Silian_avatar = view["owner"]["face"]
    fans = msg.format_num(Silian_load_json["data"]["Card"]["card"]["fans"], 1)

    if use_embed:
        return Embed(
            title=f"{title}{pages}",
            description=Silian_desc,
            url=Silian_video_url,
            author=f"{owner}{str(I18NContext('message.brackets', msg=fans))}",
            footer="Bilibili",
            image=Image(Silian_pic),
            thumbnail=Image(Silian_avatar),
            fields=[
                EmbedField("{I18N:bilibili.message.embed.type}", Silian_tname),
                EmbedField(
                    "{I18N:bilibili.message.embed.view}",
                    Silian_stat_view,
                    inline=True,
                ),
                EmbedField(
                    "{I18N:bilibili.message.embed.danmaku}",
                    Silian_stat_danmaku,
                    inline=True,
                ),
                EmbedField(
                    "{I18N:bilibili.message.embed.reply}",
                    Silian_stat_reply,
                    inline=True,
                ),
                EmbedField(
                    "{I18N:bilibili.message.embed.like}",
                    Silian_stat_like,
                    inline=True,
                ),
                EmbedField(
                    "{I18N:bilibili.message.embed.coin}",
                    Silian_stat_coin,
                    inline=True,
                ),
                EmbedField(
                    "{I18N:bilibili.message.embed.favorite}",
                    Silian_stat_favorite,
                    inline=True,
                ),
                EmbedField(
                    "{I18N:bilibili.message.embed.share}",
                    Silian_stat_share,
                    inline=True,
                ),
                EmbedField("{I18N:bilibili.message.embed.time}", Silian_time),
            ],
        )

    if not get_detail:
        Silian_output = I18NContext("bilibili.message", title=title, tname=Silian_tname, owner=owner, time=Silian_time)
    else:
        Silian_output = I18NContext(
            "bilibili.message.detail",
            title=title,
            pages=pages,
            tname=Silian_tname,
            owner=owner,
            fans=fans,
            view=Silian_stat_view,
            danmaku=Silian_stat_danmaku,
            reply=Silian_stat_reply,
            like=Silian_stat_like,
            coin=Silian_stat_coin,
            favorite=Silian_stat_favorite,
            share=Silian_stat_share,
            desc=Silian_desc,
            time=Silian_time,
        )
    return [Image(Silian_pic), Url(Silian_video_url, use_mm=False), Silian_output]
