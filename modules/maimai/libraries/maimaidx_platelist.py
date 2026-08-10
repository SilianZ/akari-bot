from PIL import Image, ImageDraw, ImageFont

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.constants.path import noto_sans_demilight_path
from .maimaidx_apidata import get_plate
from .maimaidx_mapping import *
from .maimaidx_music import TotalList

Silian_total_list = TotalList()


class DrawPlateList:
    def __init__(Silian_self, Silian_plate, Silian_song_list, Silian_song_complete, Silian_remaster_required):
        Silian_self.song_list = Silian_song_list
        Silian_self.song_complete = Silian_song_complete
        Silian_self.remaster_required = Silian_remaster_required
        Silian_self.version = Silian_plate[0]
        Silian_self.goal = Silian_plate[1:]
        if Silian_self.goal == "者":
            Silian_self.goal = "覇"
        elif Silian_self.goal == "舞舞":
            Silian_self.goal = "舞"
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
        Silian_self.cover_marks = {}
        Silian_self.img = None
        Silian_self.update_cover_marks()
        Silian_self.create_ranked_image()

    def _get_version_color(Silian_self):
        match Silian_self.version:
            case "真":
                Silian_color = (89, 174, 229)
            case "超":
                Silian_color = (223, 254, 114)
            case "檄":
                Silian_color = (181, 230, 1)
            case "橙":
                Silian_color = (254, 208, 120)
            case "暁":
                Silian_color = (254, 120, 35)
            case "桃":
                Silian_color = (255, 10, 121)
            case "櫻":
                Silian_color = (254, 106, 158)
            case "紫":
                Silian_color = (185, 131, 255)
            case "菫":
                Silian_color = (116, 50, 220)
            case "白":
                Silian_color = (179, 235, 252)
            case "雪":
                Silian_color = (103, 254, 253)
            case "輝":
                Silian_color = (154, 160, 254)
            case "覇" | "舞":
                Silian_color = (221, 121, 237)
            case "熊" | "華":
                Silian_color = (239, 95, 95)
            case "爽" | "煌":
                Silian_color = (255, 255, 95)
            case "宙" | "星":
                Silian_color = (138, 200, 251)
            case "祭" | "祝":
                Silian_color = (184, 123, 191)
            case "双" | "宴":
                Silian_color = (255, 186, 95)
            case "鏡" | "彩":
                Silian_color = (221, 255, 241)
            case _:
                Silian_color = (0, 0, 0)
        return Silian_color

    def _get_goal_color(Silian_self):
        match Silian_self.goal:
            case "覇":
                Silian_color = (255, 129, 141)
            case "極":
                Silian_color = (129, 217, 85)
            case "将":
                Silian_color = (239, 243, 13)
            case "神":
                Silian_color = (249, 128, 4)
            case "舞":
                Silian_color = (69, 174, 255)
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
            for _, sid in enumerate(Silian_elements):
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
                Silian_vcolor = Silian_self._get_version_color()
                Silian_luminance = Silian_self._get_luminance(*Silian_vcolor)
                Silian_text_color = (0, 0, 0) if Silian_luminance > 140 else (255, 255, 255)

                # 左侧用于放置标记
                Silian_draw.rectangle(
                    [Silian_x_offset, Silian_bar_top, Silian_x_offset + Silian_large_bar_width, Silian_bar_top + Silian_bar_height],
                    fill=(0, 0, 0),
                )

                # 右侧用于放置封面ID
                Silian_draw.rectangle(
                    [Silian_x_offset + Silian_large_bar_width, Silian_bar_top, Silian_x_offset + Silian_self.image_size, Silian_bar_top + Silian_bar_height],
                    fill=Silian_vcolor,
                )

                if sid in Silian_self.remaster_required:
                    Silian_mark_count = 5
                else:
                    Silian_mark_count = 4

                # 分段填充颜色
                Silian_mark_width = Silian_large_bar_width / Silian_mark_count  # 使用浮点数计算
                if sid not in Silian_self.cover_marks:
                    Silian_self.cover_marks[sid] = [False] * Silian_mark_count

                for Silian_i in range(Silian_mark_count):
                    if Silian_self.cover_marks[sid][Silian_i]:
                        Silian_draw.rectangle(
                            [
                                Silian_x_offset + Silian_i * Silian_mark_width,
                                Silian_bar_top,
                                Silian_x_offset + (Silian_i + 1) * Silian_mark_width if Silian_i < Silian_mark_count - 1 else Silian_x_offset + Silian_large_bar_width,
                                Silian_bar_top + Silian_bar_height,
                            ],
                            fill=Silian_self.diff_colors[Silian_i],
                        )

                # 绘制封面ID
                Silian_font = ImageFont.truetype(noto_sans_demilight_path, 10, encoding="utf-8")
                Silian_bbox = Silian_draw.textbbox((0, 0), str(sid), font=Silian_font)
                Silian_text_width, Silian_text_height = Silian_bbox[2] - Silian_bbox[0], Silian_bbox[3] - Silian_bbox[1]
                Silian_text_x = Silian_x_offset + Silian_large_bar_width + (Silian_small_bar_width - Silian_text_width) // 2
                Silian_text_y = Silian_bar_top + (Silian_bar_height - Silian_text_height) // 2
                Silian_draw.text((Silian_text_x, Silian_text_y), str(sid), fill=Silian_text_color, font=Silian_font)

                if all(Silian_self.cover_marks[sid]):
                    Silian_overlay = Image.new("RGBA", (Silian_self.image_size, Silian_self.image_size), (0, 0, 0, 180))  # 半透明黑色
                    Silian_self.img.paste(Silian_overlay, (Silian_x_offset, Silian_y_offset), Silian_overlay)  # 使用overlay进行粘贴

                    Silian_text_color = Silian_self._get_goal_color()
                    Silian_font = ImageFont.truetype(noto_sans_demilight_path, 36, encoding="utf-8")
                    Silian_bbox = Silian_draw.textbbox((0, 0), Silian_self.goal, font=Silian_font)
                    Silian_text_width, Silian_text_height = Silian_bbox[2] - Silian_bbox[0], Silian_bbox[3] - Silian_bbox[1]
                    Silian_text_x = Silian_x_offset + (Silian_self.image_size - Silian_text_width) // 2
                    Silian_text_y = Silian_y_offset + (Silian_self.image_size - Silian_text_height) // 2
                    Silian_draw.text((Silian_text_x, Silian_text_y), Silian_self.goal, fill=Silian_text_color, font=Silian_font)

                Silian_x_offset += Silian_self.image_size + Silian_self.spacing

            Silian_y_offset += Silian_self.image_size + Silian_self.spacing + 20

        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 10, encoding="utf-8")
        Silian_draw.text((5, Silian_total_height - 15), 'Generated by Teahouse Studios "AkariBot"', (0, 0, 0), font=Silian_font)

    def update_cover_marks(Silian_self):
        for Silian_cover_id, Silian_diff in Silian_self.song_complete:
            for _, Silian_elements in Silian_self.song_list.items():
                if Silian_cover_id in Silian_elements:
                    if Silian_cover_id not in Silian_self.cover_marks:
                        if Silian_cover_id in Silian_self.remaster_required:
                            Silian_self.cover_marks[Silian_cover_id] = [False, False, False, False, False]
                        else:
                            Silian_self.cover_marks[Silian_cover_id] = [False, False, False, False]
                    try:
                        Silian_self.cover_marks[Silian_cover_id][Silian_diff] = True
                    except IndexError:
                        pass

    def get_dir(Silian_self):
        return Silian_self.img


async def _get_plate_process(
    Silian_msg: Bot.MessageSession, Silian_payload: dict, Silian_plate: str, Silian_use_cache: bool = True
) -> tuple[dict[str, list[str]], list[tuple[str, int]]]:
    Silian_song_complete_basic = []
    Silian_song_complete_advanced = []
    Silian_song_complete_expert = []
    Silian_song_complete_master = []
    Silian_song_complete_remaster = []

    Silian_version = Silian_plate[0]
    Silian_goal = Silian_plate[1:]

    if Silian_version == "真":  # 真代为无印版本
        Silian_payload["version"] = ["maimai", "maimai PLUS"]
    elif Silian_version in ["覇", "舞"]:  # 霸者和舞牌需要全版本
        Silian_payload["version"] = list(set(list(sd_plate_mapping.values())))
    elif Silian_version in plate_mapping and Silian_version != "初":  # “初”不是版本名称
        Silian_payload["version"] = [plate_mapping[Silian_version]]
    else:
        await Silian_msg.finish(I18NContext("maimai.message.plate.plate_not_found"))

    Silian_res = await get_plate(Silian_msg, Silian_payload, Silian_version, Silian_use_cache)
    Silian_verlist: list = Silian_res["verlist"]

    if Silian_goal in ["将", "者"]:
        for Silian_song in Silian_verlist:  # 将剩余歌曲ID和难度加入目标列表
            if Silian_song["level_index"] == 0 and Silian_song["achievements"] >= (100.0 if Silian_goal == "将" else 80.0):
                Silian_song_complete_basic.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 1 and Silian_song["achievements"] >= (100.0 if Silian_goal == "将" else 80.0):
                Silian_song_complete_advanced.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 2 and Silian_song["achievements"] >= (100.0 if Silian_goal == "将" else 80.0):
                Silian_song_complete_expert.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 3 and Silian_song["achievements"] >= (100.0 if Silian_goal == "将" else 80.0):
                Silian_song_complete_master.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if (
                Silian_version in ["覇", "舞"]
                and str(Silian_song["id"]) in mai_plate_remaster_required
                and Silian_song["level_index"] == 4
                and Silian_song["achievements"] >= (100.0 if Silian_goal == "将" else 80.0)
            ):
                Silian_song_complete_remaster.append((str(Silian_song["id"]), Silian_song["level_index"]))  # 霸者和舞牌需要Re:MASTER难度
    elif Silian_goal == "極":
        for Silian_song in Silian_verlist:  # 将剩余歌曲ID和难度加入目标列表
            if Silian_song["level_index"] == 0 and Silian_song["fc"]:
                Silian_song_complete_basic.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 1 and Silian_song["fc"]:
                Silian_song_complete_advanced.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 2 and Silian_song["fc"]:
                Silian_song_complete_expert.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 3 and Silian_song["fc"]:
                Silian_song_complete_master.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if (
                Silian_version == "舞"
                and str(Silian_song["id"]) in mai_plate_remaster_required
                and Silian_song["level_index"] == 4
                and Silian_song["fc"]
            ):
                Silian_song_complete_remaster.append((str(Silian_song["id"]), Silian_song["level_index"]))
    elif Silian_goal == "舞舞":
        for Silian_song in Silian_verlist:  # 将剩余歌曲ID和难度加入目标列表
            if Silian_song["level_index"] == 0 and Silian_song["fs"] in ["fsd", "fsdp"]:
                Silian_song_complete_basic.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 1 and Silian_song["fs"] in ["fsd", "fsdp"]:
                Silian_song_complete_advanced.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 2 and Silian_song["fs"] in ["fsd", "fsdp"]:
                Silian_song_complete_expert.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 3 and Silian_song["fs"] in ["fsd", "fsdp"]:
                Silian_song_complete_master.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if (
                Silian_version == "舞"
                and str(Silian_song["id"]) in mai_plate_remaster_required
                and Silian_song["level_index"] == 4
                and Silian_song["fs"] in ["fsd", "fsdp"]
            ):
                Silian_song_complete_remaster.append((str(Silian_song["id"]), Silian_song["level_index"]))
    elif Silian_goal == "神":
        for Silian_song in Silian_verlist:  # 将剩余歌曲ID和难度加入目标列表
            if Silian_song["level_index"] == 0 and Silian_song["fc"] in ["ap", "app"]:
                Silian_song_complete_basic.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 1 and Silian_song["fc"] in ["ap", "app"]:
                Silian_song_complete_advanced.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 2 and Silian_song["fc"] in ["ap", "app"]:
                Silian_song_complete_expert.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 3 and Silian_song["fc"] in ["ap", "app"]:
                Silian_song_complete_master.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if (
                Silian_version == "舞"
                and str(Silian_song["id"]) in mai_plate_remaster_required
                and Silian_song["level_index"] == 4
                and Silian_song["fc"] in ["ap", "app"]
            ):
                Silian_song_complete_remaster.append((str(Silian_song["id"]), Silian_song["level_index"]))
    else:
        await Silian_msg.finish(I18NContext("maimai.message.plate.plate_not_found"))

    Silian_song_expect = mai_plate_song_expect(Silian_version)
    Silian_song_list = {
        "15": [],
        "14+": [],
        "14": [],
        "13+": [],
        "13": [],
        "12+": [],
        "12": [],
        "11+": [],
        "11": [],
        "10+": [],
        "10": [],
        "9+": [],
        "9": [],
        "8+": [],
        "8": [],
        "7+": [],
        "7": [],
        "6": [],
        "5": [],
        "4": [],
        "3": [],
        "2": [],
        "1": [],
    }
    for Silian_music in await Silian_total_list.get():  # 将未游玩歌曲ID加入目标列表
        if (
            Silian_music["basic_info"]["from"] in Silian_payload["version"] and Silian_music.id not in Silian_song_expect and int(Silian_music.id) < 100000
        ):  # 过滤宴谱
            Silian_levels = (
                Silian_music.level if Silian_version in ["覇", "舞"] and Silian_music.id in mai_plate_remaster_required else Silian_music.level[:4]
            )
            Silian_sorted_levels = sorted(
                Silian_levels, key=lambda Silian_x: (int(Silian_x[:-1]) if Silian_x[-1] == "+" else int(Silian_x), Silian_x[-1] == "+"), reverse=True
            )
            Silian_song_list[Silian_sorted_levels[0]].append(Silian_music.id)

    Silian_song_complete_basic = [Silian_music for Silian_music in Silian_song_complete_basic if Silian_music[0] not in Silian_song_expect]
    Silian_song_complete_advanced = [Silian_music for Silian_music in Silian_song_complete_advanced if Silian_music[0] not in Silian_song_expect]
    Silian_song_complete_expert = [Silian_music for Silian_music in Silian_song_complete_expert if Silian_music[0] not in Silian_song_expect]
    Silian_song_complete_master = [Silian_music for Silian_music in Silian_song_complete_master if Silian_music[0] not in Silian_song_expect]
    Silian_song_complete_remaster = [Silian_music for Silian_music in Silian_song_complete_remaster if Silian_music[0] not in Silian_song_expect]
    Silian_song_complete: list[tuple[str, int]] = (
        Silian_song_complete_basic
        + Silian_song_complete_advanced
        + Silian_song_complete_expert
        + Silian_song_complete_master
        + Silian_song_complete_remaster
    )

    return Silian_song_list, Silian_song_complete


async def generate(msg: Bot.MessageSession, payload: dict, plate: str, use_cache: bool = True) -> Image.Image | None:
    Silian_version = plate[0]
    Silian_goal = plate[1:]

    if Silian_version in plate_version_ts_mapping:
        Silian_version = plate_version_ts_mapping[Silian_version]
    if Silian_goal in plate_goal_ts_mapping:
        Silian_goal = plate_goal_ts_mapping[Silian_goal]
    plate = Silian_version + Silian_goal

    Silian_song_list, Silian_song_complete = await _get_plate_process(msg, payload, plate, use_cache)
    Silian_remaster_required = mai_plate_remaster_required if Silian_version in ["覇", "舞"] else []

    Silian_pic = DrawPlateList(plate, Silian_song_list, Silian_song_complete, Silian_remaster_required).get_dir()
    return Silian_pic
