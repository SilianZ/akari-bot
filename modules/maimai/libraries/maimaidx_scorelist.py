from PIL import Image, ImageDraw, ImageFont

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.constants.path import noto_sans_demilight_path
from .maimaidx_apidata import get_total_record
from .maimaidx_mapping import *
from .maimaidx_music import TotalList

Silian_total_list = TotalList()


class DrawLevelList:
    def __init__(Silian_self, Silian_level, Silian_goal, Silian_song_list, Silian_song_played):
        Silian_self.level = Silian_level
        Silian_self.goal = Silian_goal
        Silian_self.song_list = Silian_song_list
        Silian_self.song_played = Silian_song_played
        Silian_self.image_size = 80
        Silian_self.spacing = 10
        Silian_self.margin = 20
        Silian_self.diff_colors = [
            (69, 193, 36),
            (255, 186, 1),
            (255, 90, 102),
            (134, 49, 200),
            (217, 197, 233),
        ]
        Silian_self.img = None
        Silian_self.create_ranked_image()

    def _get_goal_color(Silian_self):
        match Silian_self.goal:
            case "A" | "AA" | "AAA":
                Silian_color = (255, 129, 141)
            case "S" | "S+" | "SS" | "SS+":
                Silian_color = (239, 243, 13)
            case "SSS":
                Silian_color = [(239, 243, 13), (69, 174, 255), (255, 129, 141)]
            case "SSS+":
                Silian_color = [(239, 243, 13), (69, 174, 255), (255, 129, 141), (239, 243, 13)]
            case "FC" | "FC+":
                Silian_color = (129, 217, 85)
            case "AP" | "AP+":
                Silian_color = (249, 128, 4)
            case "SYNC":
                Silian_color = (49, 195, 246)
            case "FS" | "FS+":
                Silian_color = (69, 174, 255)
            case "FDX" | "FDX+":
                Silian_color = (249, 128, 4)
            case _:
                Silian_color = (255, 255, 255)
        return Silian_color

    @staticmethod
    def _get_luminance(Silian_r, Silian_g, Silian_b):
        return 0.2126 * Silian_r + 0.7152 * Silian_g + 0.0722 * Silian_b

    def create_ranked_image(Silian_self):
        Silian_total_width = 10 * (Silian_self.image_size + Silian_self.spacing) - Silian_self.spacing + 2 * Silian_self.margin

        Silian_total_height = Silian_self.margin
        for Silian_level, Silian_elements in Silian_self.song_list.items():
            if not Silian_elements:
                continue
            Silian_rows = (len(Silian_elements) + 9) // 10
            Silian_total_height += Silian_rows * (Silian_self.image_size + Silian_self.spacing + 20) + 40

        Silian_self.img = Image.new("RGB", (Silian_total_width, Silian_total_height), (211, 211, 211))
        Silian_draw = ImageDraw.Draw(Silian_self.img)

        Silian_y_offset = Silian_self.margin

        for Silian_level, Silian_elements in Silian_self.song_list.items():
            if not Silian_elements:
                continue

            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 24, encoding="utf-8")
            Silian_draw.text((Silian_self.margin, Silian_y_offset), Silian_level, fill=(0, 0, 0), font=Silian_font)
            Silian_y_offset += 30

            Silian_x_offset = Silian_self.margin
            for _, Silian_i in enumerate(Silian_elements):
                sid = Silian_i[0]
                Silian_df = Silian_i[1]

                if Silian_x_offset + Silian_self.image_size > Silian_total_width - Silian_self.margin:
                    Silian_x_offset = Silian_self.margin
                    Silian_y_offset += Silian_self.image_size + Silian_self.spacing + 20

                Silian_cover_path = mai_cover_path / f"{sid}.png"
                if Silian_cover_path.exists():
                    Silian_cover = Image.open(Silian_cover_path)
                    Silian_cover = Silian_cover.resize((Silian_self.image_size, Silian_self.image_size))
                    Silian_self.img.paste(Silian_cover, (Silian_x_offset, Silian_y_offset))
                elif (mai_cover_path / "0.png").exists():
                    Silian_cover = Image.open(mai_cover_path / "0.png")
                    Silian_cover = Silian_cover.resize((Silian_self.image_size, Silian_self.image_size))
                    Silian_self.img.paste(Silian_cover, (Silian_x_offset, Silian_y_offset))
                else:
                    Silian_draw.rectangle(
                        [Silian_x_offset, Silian_y_offset, Silian_x_offset + Silian_self.image_size, Silian_y_offset + Silian_self.image_size],
                        fill=(240, 240, 240),
                    )
                    Silian_font = ImageFont.truetype(noto_sans_demilight_path, 20, encoding="utf-8")
                    Silian_bbox = Silian_draw.textbbox((0, 0), str(sid), font=Silian_font)
                    Silian_text_width, Silian_text_height = Silian_bbox[2] - Silian_bbox[0], Silian_bbox[3] - Silian_bbox[1]
                    Silian_text_x = Silian_x_offset + (Silian_self.image_size - Silian_text_width) // 2
                    Silian_text_y = Silian_y_offset + (Silian_self.image_size - Silian_text_height) // 2
                    Silian_draw.text((Silian_text_x, Silian_text_y), str(sid), fill=(100, 100, 100), font=Silian_font)

                # 绘制灰色长方形
                Silian_bar_top = Silian_y_offset + Silian_self.image_size
                Silian_bar_height = 15
                Silian_large_bar_width = Silian_self.image_size * 0.6  # 左边部分的宽度，占比大
                Silian_small_bar_width = Silian_self.image_size * 0.4  # 右边部分的宽度，占比小
                Silian_dcolor = Silian_self.diff_colors[Silian_df]
                Silian_luminance = Silian_self._get_luminance(*Silian_dcolor)
                Silian_text_color = (0, 0, 0) if Silian_luminance > 140 else (255, 255, 255)

                # 左侧用于放置标记
                Silian_draw.rectangle(
                    [Silian_x_offset, Silian_bar_top, Silian_x_offset + Silian_large_bar_width, Silian_bar_top + Silian_bar_height],
                    fill=(0, 0, 0),
                )

                # 右侧用于放置封面ID
                Silian_draw.rectangle(
                    [Silian_x_offset + Silian_large_bar_width, Silian_bar_top, Silian_x_offset + Silian_self.image_size, Silian_bar_top + Silian_bar_height],
                    fill=Silian_dcolor,
                )

                # 绘制封面ID
                Silian_font = ImageFont.truetype(noto_sans_demilight_path, 10, encoding="utf-8")
                Silian_bbox = Silian_draw.textbbox((0, 0), str(sid), font=Silian_font)
                Silian_text_width, Silian_text_height = Silian_bbox[2] - Silian_bbox[0], Silian_bbox[3] - Silian_bbox[1]
                Silian_text_x = Silian_x_offset + Silian_large_bar_width + (Silian_small_bar_width - Silian_text_width) // 2
                Silian_text_y = Silian_bar_top + (Silian_bar_height - Silian_text_height) // 2
                Silian_draw.text((Silian_text_x, Silian_text_y), str(sid), fill=Silian_text_color, font=Silian_font)

                if Silian_self.goal:
                    if Silian_self.goal in rate_list:
                        Silian_rank_list = rate_list
                        Silian_mark_fill = [
                            (69, 174, 255),
                            (69, 174, 255),
                            (69, 174, 255),
                            (69, 174, 255),
                            (69, 174, 255),
                            (255, 129, 141),
                            (255, 129, 141),
                            (255, 129, 141),
                            (239, 243, 13),
                            (239, 243, 13),
                            (239, 243, 13),
                            (239, 243, 13),
                            (239, 243, 13),
                            (239, 243, 13),
                        ]
                    elif Silian_self.goal in combo_list:
                        Silian_rank_list = combo_list
                        Silian_mark_fill = [(129, 217, 85), (129, 217, 85), (249, 128, 4), (249, 128, 4)]
                    elif Silian_self.goal in sync_list:
                        Silian_rank_list = sync_list
                        Silian_mark_fill = [(49, 195, 246), (69, 174, 255), (69, 174, 255), (249, 128, 4), (249, 128, 4)]
                    else:
                        Silian_rank_list = []
                        Silian_mark_fill = []

                    Silian_rank = next((Silian_c for Silian_a, Silian_b, Silian_c in Silian_self.song_played if Silian_a == sid and Silian_b == Silian_df), None)
                    Silian_rank_index = Silian_rank_list.index(Silian_rank) + 1 if Silian_rank else 0

                    # 分段填充颜色
                    Silian_mark_width = Silian_large_bar_width / len(Silian_mark_fill)  # 使用浮点数计算
                    for Silian_i in range(Silian_rank_index):
                        Silian_draw.rectangle(
                            [
                                Silian_x_offset + Silian_i * Silian_mark_width,
                                Silian_bar_top,
                                Silian_x_offset + (Silian_i + 1) * Silian_mark_width if Silian_i < Silian_rank_index else Silian_x_offset + Silian_large_bar_width,
                                Silian_bar_top + Silian_bar_height,
                            ],
                            fill=Silian_mark_fill[Silian_i],
                        )

                    if Silian_rank_index >= Silian_rank_list.index(Silian_self.goal) + 1:
                        Silian_overlay = Image.new("RGBA", (Silian_self.image_size, Silian_self.image_size), (0, 0, 0, 180))
                        Silian_self.img.paste(Silian_overlay, (Silian_x_offset, Silian_y_offset), Silian_overlay)

                        Silian_text_color = Silian_self._get_goal_color()
                        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 24, encoding="utf-8")

                        def get_text_size(Silian_text, Silian_font):
                            Silian_bbox = Silian_font.getbbox(Silian_text)
                            Silian_width = Silian_bbox[2] - Silian_bbox[0]
                            Silian_height = Silian_bbox[3] - Silian_bbox[1]
                            return Silian_width, Silian_height

                        Silian_text_width, Silian_text_height = get_text_size(Silian_self.goal, Silian_font)

                        if Silian_self.goal in ["SSS", "SSS+"]:
                            Silian_char_sizes = [Silian_font.getbbox(Silian_c)[2] - Silian_font.getbbox(Silian_c)[0] for Silian_c in Silian_self.goal]
                            Silian_total_text_width = sum(Silian_char_sizes)
                            Silian_text_x = Silian_x_offset + (Silian_self.image_size - Silian_total_text_width) // 2
                            Silian_text_y = Silian_y_offset + (Silian_self.image_size - Silian_font.getbbox("A")[3]) // 2  # 大致高度居中

                            for Silian_i, Silian_char in enumerate(Silian_self.goal):
                                Silian_char_width, _ = get_text_size(Silian_char, Silian_font)
                                Silian_draw.text((Silian_text_x, Silian_text_y), Silian_char, fill=Silian_text_color[Silian_i], font=Silian_font)
                                Silian_text_x += Silian_char_width  # 更新x坐标，绘制下一个字母
                        else:
                            Silian_text_x = Silian_x_offset + (Silian_self.image_size - Silian_text_width) // 2
                            Silian_text_y = Silian_y_offset + (Silian_self.image_size - Silian_text_height) // 2
                            Silian_draw.text((Silian_text_x, Silian_text_y), Silian_self.goal, fill=Silian_text_color, font=Silian_font)

                Silian_x_offset += Silian_self.image_size + Silian_self.spacing

            Silian_y_offset += Silian_self.image_size + Silian_self.spacing + 20

        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 10, encoding="utf-8")
        Silian_draw.text((5, Silian_total_height - 15), 'Generated by Teahouse Studios "AkariBot"', (0, 0, 0), font=Silian_font)

    def get_dir(Silian_self):
        return Silian_self.img


async def _get_level_process(
    Silian_msg: Bot.MessageSession, Silian_payload: dict, Silian_level: str, Silian_goal: str | None = None, Silian_use_cache: bool = True
) -> tuple[dict[str, list[str]], list[tuple[str, int]]]:
    Silian_res = await get_total_record(Silian_msg, Silian_payload, Silian_use_cache)
    Silian_records: list = Silian_res["records"]

    Silian_song_played = []
    if Silian_goal:
        if Silian_goal in rate_list:
            for Silian_song in Silian_records:
                try:
                    Silian_rank = next(
                        Silian_rank
                        for Silian_interval, Silian_rank in score_to_rate.items()
                        if Silian_interval[0] <= Silian_song["achievements"] < Silian_interval[1]
                    )
                except StopIteration:
                    continue
                Silian_song_played.append((str(Silian_song["song_id"]), Silian_song["level_index"], Silian_rank))
        elif Silian_goal in combo_list:
            for Silian_song in Silian_records:
                Silian_rank = combo_mapping[Silian_song["fc"]] if Silian_song["fc"] else None
                Silian_song_played.append((str(Silian_song["song_id"]), Silian_song["level_index"], Silian_rank))
        elif Silian_goal in sync_list:
            for Silian_song in Silian_records:
                Silian_rank = sync_mapping[Silian_song["fs"]] if Silian_song["fs"] else None
                Silian_song_played.append((str(Silian_song["song_id"]), Silian_song["level_index"], Silian_rank))
        else:
            await Silian_msg.finish(I18NContext("maimai.message.goal_invalid"))

    Silian_song_list = {}

    for Silian_music in (await Silian_total_list.get()).filter(level=Silian_level):
        if int(Silian_music.id) < 100000:  # 过滤宴谱
            Silian_indices = [Silian_i for Silian_i, Silian_lv in enumerate(Silian_music.level) if Silian_lv == Silian_level]
            for Silian_idx in Silian_indices:
                Silian_const = str(Silian_music.ds[Silian_idx])
                if Silian_const not in Silian_song_list:
                    Silian_song_list[Silian_const] = []
                Silian_song_list[Silian_const].append((Silian_music.id, Silian_idx))

    Silian_song_list = {Silian_k: Silian_song_list[Silian_k] for Silian_k in sorted(Silian_song_list, reverse=True)}

    return Silian_song_list, Silian_song_played


async def generate(
    msg: Bot.MessageSession, payload: dict, level: str, goal: str | None, use_cache: bool = True
) -> Image.Image | None:
    if goal:
        goal = goal.upper()
    Silian_song_list, Silian_song_played = await _get_level_process(msg, payload, level, goal, use_cache)

    Silian_pic = DrawLevelList(level, goal, Silian_song_list, Silian_song_played).get_dir()
    return Silian_pic
