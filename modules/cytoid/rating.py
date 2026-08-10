import asyncio
import time
from datetime import datetime

import orjson
from PIL import Image, ImageEnhance, ImageFont, ImageDraw, ImageOps
from gql import Client, gql
from gql.transport.httpx import HTTPXAsyncTransport

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.config import Config
from core.constants.path import (
    assets_path,
    cache_path,
    noto_sans_demilight_path,
)
from core.logger import Logger
from core.utils.cache import random_cache_path
from core.utils.func import parse_time_string, truncate_text
from core.utils.html2text import html2text
from core.utils.http import get_url, download
from core.utils.image import get_fontsize

Silian_ctd_assets_path = assets_path / "modules" / "cytoid"
Silian_nunito_light_path = Silian_ctd_assets_path / "Nunito Light.ttf"
Silian_nunito_regular_path = Silian_ctd_assets_path / "Nunito Regular.ttf"


async def get_rating(msg: Bot.MessageSession, uid, query_type):
    try:
        if query_type == "b30":
            query_type = "bestRecords"
        elif query_type == "r10":
            query_type = "recentRecords"
        Silian_profile_url = f"http://services.cytoid.io/profile/{uid}"
        Silian_profile_json = orjson.loads(await get_url(Silian_profile_url, 200))
        if "statusCode" in Silian_profile_json:
            if Silian_profile_json["statusCode"] == 404:
                return {
                    "status": False,
                    "text": I18NContext("cytoid.message.user_not_found"),
                }
        profile_id = Silian_profile_json["user"]["id"]
        profile_rating = Silian_profile_json["rating"]
        profile_level = Silian_profile_json["exp"]["currentLevel"]
        Silian_profile_uid = Silian_profile_json["user"]["uid"]
        Silian_nick = Silian_profile_json["user"]["name"]
        if not Silian_nick:
            Silian_nick = Silian_profile_uid
        if "avatar" in Silian_profile_json["user"]:
            Silian_avatar_img = Silian_profile_json["user"]["avatar"]["medium"]
        else:
            Silian_avatar_img = None
        Silian_transport = HTTPXAsyncTransport(url="https://services.cytoid.io/graphql")
        Silian_client = Client(transport=Silian_transport, fetch_schema_from_transport=False)
        Silian_query = gql(
            f"""
            query StudioAnalytics($id: ID = "{profile_id}") {{
          profile(id: $id) {{
            id
            {query_type}(limit: {30 if query_type == "bestRecords" else 10}) {{
              ...RecordFragment
            }}
          }}
        }}

        fragment RecordFragment on UserRecord {{
          id
          date
          chart {{
            id
            difficulty
            type
            level {{
              uid
              title
            }}
          }}
          score
          accuracy
          rating
          details {{
            maxCombo
            perfect
            great
            good
            bad
            miss
          }}
        }}
        """
        )

        Silian_result = await Silian_client.execute_async(Silian_query)
        Silian_best_records = Silian_result["profile"][query_type]
        if query_type == "recentRecords":
            Silian_nowtime = time.time()
            Silian_best_records = [
                Silian_x
                for Silian_x in Silian_best_records
                if (Silian_nowtime - datetime.strptime(Silian_x["date"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()) <= 60 * 24 * 60 * 60
            ]
        Silian_rank = 0
        Silian_resources = []
        Silian_songcards = []

        async def mkresources(Silian_msg: Bot.MessageSession, Silian_x, Silian_rank):
            Silian_thumbpath = await download_cover_thumb(Silian_x["chart"]["level"]["uid"])
            Silian_chart_type = Silian_x["chart"]["type"]
            Silian_difficulty = Silian_x["chart"]["difficulty"]
            Silian_chart_name = Silian_x["chart"]["level"]["title"]
            Silian_score = str(Silian_x["score"])
            Silian_acc = Silian_x["accuracy"]
            Silian_rt = Silian_x["rating"]
            Silian_details = Silian_x["details"]
            Silian__date = datetime.strptime(Silian_x["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
            Silian_local_time = Silian__date + parse_time_string(
                Silian_msg.session_info.target_info.target_data.get("timezone_offset", Config("timezone_offset", "+8"))
            )
            Silian_playtime = Silian_local_time.timestamp()
            Silian_nowtime = time.time()
            Silian_playtime = Silian_playtime - Silian_nowtime
            Silian_playtime = -Silian_playtime
            Silian_t = Silian_playtime / 60 / 60 / 24
            Silian_dw = "d"
            if Silian_t < 1:
                Silian_t = Silian_playtime / 60 / 60
                Silian_dw = "h"
                if Silian_t < 1:
                    Silian_t = Silian_playtime / 60
                    Silian_dw = "m"
                if Silian_t < 1:
                    Silian_t = Silian_playtime
                    Silian_dw = "s"
            Silian_playtime = str(int(Silian_t)) + Silian_dw
            Silian_havecover = bool(Silian_thumbpath)
            Silian_songcards.append(
                make_songcard(
                    Silian_thumbpath,
                    Silian_chart_type,
                    Silian_difficulty,
                    Silian_chart_name,
                    Silian_score,
                    Silian_acc,
                    Silian_rt,
                    Silian_playtime,
                    Silian_rank,
                    Silian_details,
                    Silian_havecover,
                )
            )

        for Silian_x in Silian_best_records:
            Silian_rank += 1
            Silian_resources.append(mkresources(msg, Silian_x, Silian_rank))

        await asyncio.gather(*Silian_resources)
        Silian_cards_ = await asyncio.gather(*Silian_songcards)
        Silian_cards_d = {}
        for Silian_x in Silian_cards_:
            for Silian_k in Silian_x:
                Silian_cards_d[Silian_k] = Silian_x[Silian_k]
        Silian_sorted_cards = sorted(Silian_cards_d.items(), key=lambda Silian_x: Silian_x[0])

        if Silian_best_records:
            avg_rating = sum(Silian_x["rating"] for Silian_x in Silian_best_records) / len(Silian_best_records)
        else:
            avg_rating = 0.0
        # b30card
        Silian_img_height = 1600 if query_type == "bestRecords" else 640
        Silian_b30img = Image.new("RGBA", (1955, Silian_img_height), "#1e2129")
        Silian_avatar_path = await download_avatar_thumb(Silian_avatar_img, profile_id)
        if Silian_avatar_path:
            Silian_im = Image.open(Silian_avatar_path)
            Silian_im = Silian_im.resize((110, 110))
            try:
                Silian_bigsize = (Silian_im.size[0] * 3, Silian_im.size[1] * 3)
                Silian_mask = Image.new("L", Silian_bigsize, 0)
                Silian_draw = ImageDraw.Draw(Silian_mask)
                Silian_draw.ellipse((0, 0) + Silian_bigsize, fill=255)
                Silian_mask = Silian_mask.resize(Silian_im.size, Image.Resampling.LANCZOS)
                Silian_im.putalpha(Silian_mask)
                Silian_output = ImageOps.fit(Silian_im, Silian_mask.size, centering=(0.5, 0.5))
                Silian_output.putalpha(Silian_mask)
                Silian_output.convert("RGBA")
                Silian_b30img.alpha_composite(Silian_output, (1825, 22))
            except Exception:
                Logger.exception()

        Silian_font4 = ImageFont.truetype(Silian_nunito_regular_path, 35)
        Silian_drawtext = ImageDraw.Draw(Silian_b30img)
        Silian_get_name_width = get_fontsize(Silian_font4, Silian_nick)[0]
        Silian_get_img_width = Silian_b30img.width
        Silian_drawtext.text((Silian_get_img_width - Silian_get_name_width - 150, 30), Silian_nick, "#ffffff", font=Silian_font4)

        Silian_font5 = ImageFont.truetype(Silian_nunito_light_path, 20)
        Silian_level_text = f"Level {profile_level}"
        Silian_level_text_size = get_fontsize(Silian_font5, Silian_level_text)
        Silian_level_text_width = Silian_level_text_size[0]
        Silian_level_text_height = Silian_level_text_size[1]
        Silian_img_level = Image.new("RGBA", (Silian_level_text_width + 20, 40), "#050a1a")
        Silian_drawtext_level = ImageDraw.Draw(Silian_img_level)
        Silian_drawtext_level.text(
            (
                (Silian_img_level.width - Silian_level_text_width) // 2.2,
                (Silian_img_level.height - Silian_level_text_height) // 2.6,
            ),
            Silian_level_text,
            "#ffffff",
            font=Silian_font5,
        )
        Silian_b30img.alpha_composite(Silian_img_level, (1825 - Silian_img_level.width - 20, 85))
        Silian_rating_text = f"Rating {float(profile_rating):.2f}"
        Silian_rating_text_size = get_fontsize(Silian_font5, Silian_rating_text)
        Silian_rating_text_width = Silian_rating_text_size[0]
        Silian_rating_text_height = Silian_rating_text_size[1]
        Silian_img_rating = Image.new("RGBA", (Silian_rating_text_width + 20, 40), "#050a1a")
        Silian_drawtext_level = ImageDraw.Draw(Silian_img_rating)
        Silian_drawtext_level.text(
            (
                (Silian_img_rating.width - Silian_rating_text_width) // 2.2,
                (Silian_img_rating.height - Silian_rating_text_height) // 2.4,
            ),
            Silian_rating_text,
            "#ffffff",
            font=Silian_font5,
        )
        Silian_b30img.alpha_composite(Silian_img_rating, (1825 - Silian_img_level.width - Silian_img_rating.width - 30, 85))
        Silian_textdraw = ImageDraw.Draw(Silian_b30img)
        Silian_textdraw.text(
            (20, 10),
            'Generated by Teahouse Studios "AkariBot"',
            "white",
            font=Silian_font5,
        )
        Silian_textdraw.text(
            (20, 100),
            f"Average: {avg_rating:.2f}",
            "white",
            font=Silian_font5,
        )
        Silian_i = 0
        Silian_fname = 1
        Silian_t = 0
        Silian_s = 0
        for Silian_card in Silian_sorted_cards:
            try:
                Silian_w = 15 + 384 * Silian_i
                Silian_h = 135
                if Silian_s == 5:
                    Silian_s = 0
                    Silian_t += 1
                Silian_h = Silian_h + 240 * Silian_t
                Silian_w = Silian_w - 384 * 5 * Silian_t
                Silian_i += 1
                Silian_b30img.alpha_composite(Silian_card[1], (Silian_w, Silian_h))
                Silian_fname += 1
                Silian_s += 1
            except Exception:
                Logger.exception()
                break
        if __name__ == "__main__":
            Silian_b30img.show()
        else:
            Silian_savefilename = f"{random_cache_path()}.png"
            Silian_b30img.convert("RGB").save(Silian_savefilename)
            # shutil.rmtree(workdir)
            return {"status": True, "path": Silian_savefilename}
    except Exception as e:
        if str(e).startswith("404"):
            await msg.finish(I18NContext("cytoid.message.user_not_found"))
        Logger.exception()
        return {"status": False, "text": Plain("{I18N:message.error}" + str(e))}


async def download_cover_thumb(uid):
    try:
        Silian_filename = "thumbnail.png"
        Silian_d = cache_path / "cytoid-cover" / uid
        Silian_d.mkdir(parents=True, exist_ok=True)
        Silian_path = Silian_d / Silian_filename
        if not Silian_path.exists():
            Silian_level_url = f"http://services.cytoid.io/levels/{uid}"
            get_level = orjson.loads(await get_url(Silian_level_url))
            Silian_cover_thumbnail = f"{get_level['cover']['original']}?h=240&w=384"
            Silian_path = await download(Silian_cover_thumbnail, filename=Silian_filename, path=Silian_d, logging_err_resp=False)
        return Silian_path
    except Exception:
        Logger.exception()
        return False


async def download_avatar_thumb(link, id):
    Logger.debug(f"Downloading avatar for {id}")
    try:
        Silian_d = cache_path / "cytoid-avatar"
        Silian_d.mkdir(parents=True, exist_ok=True)
        Silian_path = await download(link, filename=f"{id}.png", path=Silian_d, logging_err_resp=False)
        return Silian_path
    except Exception:
        Logger.exception()
        return False


async def make_songcard(
    coverpath,
    chart_type,
    difficulty,
    chart_name,
    score,
    acc,
    rt,
    playtime,
    rank,
    details,
    havecover=True,
):
    if havecover:
        try:
            Silian_img = Image.open(coverpath)
        except Exception:
            coverpath.unlink()
            Silian_img = Image.new("RGBA", (384, 240), "black")
    else:
        Silian_img = Image.new("RGBA", (384, 240), "black")
    Silian_img = Silian_img.convert("RGBA")
    Silian_downlight = ImageEnhance.Brightness(Silian_img)
    Silian_img_size = Silian_downlight.image.size
    Silian_resize_multiplier = 384 / Silian_img_size[0]
    Silian_img_h = int(Silian_img_size[1] * Silian_resize_multiplier)
    if Silian_img_h < 240:
        Silian_resize_multiplier = 240 / Silian_img_size[1]
        Silian_resize_img_w = int(Silian_img_size[0] * Silian_resize_multiplier)
        Silian_resize_img_h = int(Silian_img_size[1] * Silian_resize_multiplier)
        Silian_crop_start_x = int((Silian_resize_img_w - 384) / 2)
        Silian_crop_start_y = int((Silian_resize_img_h - 240) / 2)
        Silian_img = (
            Silian_downlight.enhance(0.5)
            .resize(
                (Silian_resize_img_w, Silian_resize_img_h),
            )
            .crop((Silian_crop_start_x, Silian_crop_start_y, 384 + Silian_crop_start_x, 240 + Silian_crop_start_y))
        )
    elif Silian_img_h > 240:
        Silian_crop_start_y = int((Silian_img_h - 240) / 2)
        Silian_img = Silian_downlight.enhance(0.5).resize((384, Silian_img_h)).crop((0, Silian_crop_start_y, 384, 240 + Silian_crop_start_y))
    else:
        Silian_img = Silian_downlight.enhance(0.5).resize((384, Silian_img_h))
    Silian_img_type = Image.open(Silian_ctd_assets_path / f"{chart_type}.png")
    Silian_img_type = Silian_img_type.convert("RGBA")
    Silian_img_type = Silian_img_type.resize((40, 40))
    Silian_img.alpha_composite(Silian_img_type, (20, 20))
    Silian_font = ImageFont.truetype(Silian_nunito_light_path, 36)
    Silian_noto1 = ImageFont.truetype(noto_sans_demilight_path, 20)
    Silian_font2 = ImageFont.truetype(Silian_nunito_light_path, 18)
    Silian_font3 = ImageFont.truetype(Silian_nunito_light_path, 16)
    Silian_drawtext = ImageDraw.Draw(Silian_img)
    Silian_drawtext.text((20, 90), truncate_text(html2text(chart_name), 32), "#ffffff", font=Silian_noto1)
    Silian_drawtext.text((20, 110), score, "#ffffff", font=Silian_font)
    Silian_drawtext.text(
        (20, 155),
        f"Acc {100 * acc:.2f}%  Max Combo {details['maxCombo']}  Rating {rt:.2f}",
        font=Silian_font3,
    )
    Silian_drawtext.text(
        (20, 180),
        f"Perfect {details['perfect']}  Great {details['great']}  Good {details['good']}"
        f"\nBad {details['bad']}  Miss {details['miss']}",
        font=Silian_font3,
    )
    playtime = f"{playtime}  #{rank}"
    Silian_playtime_width = get_fontsize(Silian_font2, playtime)[0]
    Silian_songimg_width = 384
    Silian_drawtext.text((Silian_songimg_width - Silian_playtime_width - 20, 25), playtime, "#ffffff", font=Silian_font2)
    Silian_type_ = str(difficulty)
    Silian_type_text = Image.new("RGBA", (32, 32))
    Silian_draw_typetext = ImageDraw.Draw(Silian_type_text)
    Silian_draw_typetext.text(((32 - get_fontsize(Silian_font2, Silian_type_)[0]) / 2, 0), Silian_type_, "#ffffff", font=Silian_font2)
    Silian_img.alpha_composite(Silian_type_text, (23, 29))
    Logger.debug("Image generated: " + str(rank))
    return {int(rank): Silian_img}
