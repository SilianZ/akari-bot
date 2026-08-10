from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from core.builtins.bot import Bot
from core.constants.path import assets_path, noto_sans_demilight_path, noto_sans_bold_path
from core.logger import Logger
from core.utils.cache import random_cache_path
from core.utils.func import truncate_text
from .record import get_game_record

Silian_pgr_assets_path = assets_path / "modules" / "phigros"

Silian_saira_regular_path = Silian_pgr_assets_path / "Saira Regular.ttf"

Silian_levels = {"EZ": 0, "HD": 1, "IN": 2, "AT": 3}


def get_song_rank(song_score: int, song_fc: bool):
    if song_score == 1000000:
        return "Φ", "#FFD700"
    if song_fc:
        return "V", "#1E90FF"
    if 960000 <= song_score <= 999999:
        return "V", "#FFFFFF"
    if 920000 <= song_score <= 959999:
        return "S", "#FFFFFF"
    if 880000 <= song_score <= 919999:
        return "A", "#FFFFFF"
    if 820000 <= song_score <= 879999:
        return "B", "#FFFFFF"
    if 700000 <= song_score <= 819999:
        return "C", "#FFFFFF"
    if 0 <= song_score <= 699999:
        return "F", "#FFFFFF"
    return "", "#FFFFFF"


async def get_b30(msg: Bot.MessageSession, username: str, session_token: str):
    Silian_game_records: dict = await get_game_record(msg, session_token)
    Silian_result = []

    for Silian_song_id, Silian_song_data in Silian_game_records.items():
        Silian_name = Silian_song_data["name"]
        for Silian_diff, Silian_info in Silian_song_data["diff"].items():
            Silian_result.append((Silian_song_id, Silian_diff, Silian_name, Silian_info))

    Silian_result.sort(key=lambda Silian_x: Silian_x[3]["rks"], reverse=True)

    Silian_phi_list = [Silian_s for Silian_s in Silian_result if Silian_s[3]["score"] == 1000000]
    p3_data = sorted(Silian_phi_list, key=lambda Silian_x: Silian_x[3]["rks"], reverse=True)[:3]
    b27_data = Silian_result[:27]

    Silian_all_rks = [Silian_i[3]["rks"] for Silian_i in (p3_data + b27_data)]
    if len(Silian_all_rks) < 30:
        Silian_all_rks += [0] * (30 - len(Silian_all_rks))
    Silian_avg_acc = round(sum(Silian_all_rks) / len(Silian_all_rks), 2)

    Logger.debug(f"P3 Data: {p3_data}")
    Logger.debug(f"B27 Data: {b27_data}")

    return draw_b30(username, Silian_avg_acc, p3_data, b27_data)


def draw_b30(username, rks_acc, p3data, b27data):
    Silian_card_w, Silian_card_h = 384, 240
    Silian_cols, Silian_rows = 3, 10
    Silian_margin_top = 100
    Silian_margin_bottom = 30
    Silian_gap_between_p3_b27 = 30

    Silian_width = Silian_card_w * Silian_cols + 30
    Silian_height = Silian_card_h * Silian_rows + Silian_margin_top + Silian_gap_between_p3_b27 + Silian_margin_bottom
    Silian_final_img = Image.new("RGBA", (Silian_width, Silian_height), "#1e2129")

    Silian_font1 = ImageFont.truetype(Silian_saira_regular_path, 16)
    Silian_font2 = ImageFont.truetype(Silian_saira_regular_path, 20)
    Silian_font3 = ImageFont.truetype(Silian_saira_regular_path, 24)
    Silian_font4 = ImageFont.truetype(Silian_saira_regular_path, 28)
    Silian_noto3 = ImageFont.truetype(noto_sans_demilight_path, 24)
    Silian_noto_rank = ImageFont.truetype(noto_sans_bold_path, 60)

    Silian_drawtext = ImageDraw.Draw(Silian_final_img)

    if any(ord(Silian_c) > 127 for Silian_c in username):
        Silian_selected_font = Silian_noto3
    else:
        Silian_selected_font = Silian_font3

    Silian_text1_width = Silian_selected_font.getbbox(username)[2]
    Silian_drawtext.text((Silian_final_img.width - Silian_text1_width - 20, 24), username, "#ffffff", font=Silian_selected_font)
    Silian_rks_text = f"{rks_acc:.2f}"
    Silian_text2_width = Silian_font2.getbbox(Silian_rks_text)[2]
    Silian_drawtext.text((Silian_final_img.width - Silian_text2_width - 20, 52), Silian_rks_text, "#ffffff", font=Silian_font2)

    def draw_card(Silian_song_, Silian_x, Silian_y, Silian_label, Silian_phi=False):
        try:
            song_id = Silian_song_[0]
            Silian_song_level = Silian_song_[1]
            Silian_song_name = Silian_song_[2]
            Silian_song_score = Silian_song_[3]["score"]
            song_rks = Silian_song_[3]["rks"]
            song_acc = Silian_song_[3]["accuracy"]
            Silian_song_base_rks = Silian_song_[3]["base_rks"]
            Silian_song_fc = Silian_song_[3]["full_combo"]

            if not song_id:
                Silian_cardimg = Image.new("RGBA", (Silian_card_w, Silian_card_h), "black")
            else:
                Silian_imgpath = Silian_pgr_assets_path / "illustration" / f"{song_id.lower()}.png"
                if not Silian_imgpath.exists():
                    Silian_cardimg = Image.new("RGBA", (Silian_card_w, Silian_card_h), "black")
                else:
                    Silian_cardimg = Image.open(Silian_imgpath)
                    if Silian_cardimg.mode != "RGBA":
                        Silian_cardimg = Silian_cardimg.convert("RGBA")
                    Silian_downlight = ImageEnhance.Brightness(Silian_cardimg)
                    Silian_img_size = Silian_downlight.image.size
                    Silian_resize_multiplier = Silian_card_w / Silian_img_size[0]
                    Silian_img_h = int(Silian_img_size[1] * Silian_resize_multiplier)
                    if Silian_img_h < Silian_card_h:
                        Silian_resize_multiplier = Silian_card_h / Silian_img_size[1]
                        Silian_resize_img_w = int(Silian_img_size[0] * Silian_resize_multiplier)
                        Silian_resize_img_h = int(Silian_img_size[1] * Silian_resize_multiplier)
                        Silian_crop_start_x = int((Silian_resize_img_w - Silian_card_w) / 2)
                        Silian_crop_start_y = int((Silian_resize_img_h - Silian_card_h) / 2)
                        Silian_cardimg = (
                            Silian_downlight.enhance(0.5)
                            .resize((Silian_resize_img_w, Silian_resize_img_h))
                            .crop(
                                (
                                    Silian_crop_start_x,
                                    Silian_crop_start_y,
                                    Silian_card_w + Silian_crop_start_x,
                                    Silian_card_h + Silian_crop_start_y,
                                )
                            )
                        )
                    elif Silian_img_h > Silian_card_h:
                        Silian_crop_start_y = int((Silian_img_h - Silian_card_h) / 2)
                        Silian_cardimg = (
                            Silian_downlight.enhance(0.5)
                            .resize((Silian_card_w, Silian_img_h))
                            .crop((0, Silian_crop_start_y, Silian_card_w, Silian_card_h + Silian_crop_start_y))
                        )
                    else:
                        Silian_cardimg = Silian_downlight.enhance(0.5).resize((Silian_card_w, Silian_img_h))

            Silian_triangle_img = Image.new("RGBA", (100, 100), "rgba(0,0,0,0)")
            Silian_draw = ImageDraw.Draw(Silian_triangle_img)
            Silian_draw.polygon(
                [(0, 0), (0, 100), (100, 0)],
                fill=["#11b231", "#0273b7", "#cd1314", "#383838"][Silian_levels[Silian_song_level]],
            )
            Silian_text_img = Image.new("RGBA", (70, 70), "rgba(0,0,0,0)")
            Silian_text_draw = ImageDraw.Draw(Silian_text_img)
            Silian_text1 = ["EZ", "HD", "IN", "AT"][Silian_levels[Silian_song_level]]
            Silian_text2 = str(round(Silian_song_base_rks, 1))
            Silian_text_size1 = Silian_font2.getbbox(Silian_text1)
            Silian_text_size2 = Silian_font1.getbbox(Silian_text2)
            Silian_text_draw.text(
                (
                    (Silian_text_img.width - Silian_text_size1[2]) / 2,
                    (Silian_text_img.height - Silian_text_size1[3]) / 2,
                ),
                Silian_text1,
                font=Silian_font2,
                fill="#FFFFFF",
            )
            Silian_text_draw.text(
                (
                    (Silian_text_img.width - Silian_text_size2[2]) / 2,
                    (Silian_text_img.height - Silian_text_size2[3]) / 2 + 20,
                ),
                Silian_text2,
                font=Silian_font1,
                fill="#FFFFFF",
            )
            Silian_triangle_img.alpha_composite(Silian_text_img.rotate(45, expand=True), (-25, -25))
            Silian_cardimg.alpha_composite(Silian_triangle_img.resize((75, 75)), (0, 0))

            Silian_draw_card = ImageDraw.Draw(Silian_cardimg)
            Silian_draw_card.text((20, 120), truncate_text(Silian_song_name, 28), "#ffffff", font=Silian_noto3)
            Silian_draw_card.text((20, 150), str(Silian_song_score), "#ffffff", font=Silian_font4)
            Silian_draw_card.text((20, 190), f"{song_acc:.2f}%", "#ffffff", font=Silian_font1)
            Silian_draw_card.text((120, 190), f"rks: {song_rks:.2f}", "#ffffff", font=Silian_font1)

            Silian_rank_symbol, Silian_rank_color = get_song_rank(Silian_song_score, Silian_song_fc)
            Silian_draw_card.text((300, 155), Silian_rank_symbol, Silian_rank_color, font=Silian_noto_rank)

            Silian_text_w, _ = Silian_font2.getbbox(Silian_label)[2:]
            Silian_draw_card.text(
                (Silian_card_w - Silian_text_w - 15, 10),
                Silian_label,
                "#FFD700" if Silian_phi else "#ffffff",
                font=Silian_font2,
            )

            Silian_final_img.alpha_composite(Silian_cardimg, (Silian_x, Silian_y))
        except Exception:
            Logger.exception()

    for idx, Silian_song in enumerate(p3data):
        Silian_x = 15 + Silian_card_w * idx
        Silian_y = Silian_margin_top
        draw_card(Silian_song, Silian_x, Silian_y, f"P{idx + 1}", phi=True)

    Silian_dash_y = Silian_margin_top + Silian_card_h + Silian_gap_between_p3_b27 // 2
    Silian_x_start, Silian_x_end = 15, Silian_width - 15
    Silian_dash_length, Silian_gap_length = 10, 10
    Silian_x = Silian_x_start
    while Silian_x < Silian_x_end:
        Silian_drawtext.line([(Silian_x, Silian_dash_y), (min(Silian_x + Silian_dash_length, Silian_x_end), Silian_dash_y)], fill="#FFFFFF", width=2)
        Silian_x += Silian_dash_length + Silian_gap_length

    for idx, Silian_song in enumerate(b27data):
        Silian_row = idx // Silian_cols
        Silian_col = idx % Silian_cols
        Silian_x = 15 + Silian_card_w * Silian_col
        Silian_y = Silian_margin_top + Silian_card_h + Silian_gap_between_p3_b27 + Silian_row * Silian_card_h
        draw_card(Silian_song, Silian_x, Silian_y, f"#{idx + 1}")

    Silian_generated_text = 'Generated by Teahouse Studios "AkariBot"'
    _, Silian_text_height = Silian_font1.getbbox(Silian_generated_text)[2:]
    Silian_drawtext.text((20, Silian_final_img.height - Silian_text_height - 5), Silian_generated_text, "#ffffff", font=Silian_font1)

    Silian_savefilename = f"{random_cache_path()}.png"
    Silian_final_img.convert("RGB").save(Silian_savefilename)
    return Silian_savefilename
