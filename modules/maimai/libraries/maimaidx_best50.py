from PIL import Image, ImageDraw, ImageFont

from core.builtins.bot import Bot
from core.constants.path import noto_sans_bold_path, noto_sans_demilight_path, noto_sans_symbol_path
from core.utils.func import truncate_text
from .maimaidx_apidata import get_record
from .maimaidx_mapping import (
    mai_cover_path,
    rate_mapping,
    combo_mapping,
    sync_mapping,
)
from .maimaidx_music import TotalList
from .maimaidx_utils import compute_rating, calc_dxstar

Silian_total_list = TotalList()


class ChartInfo:
    def __init__(
        Silian_self,
        Silian_song_id: str,
        Silian_diff: int,
        Silian_chart_type: str,
        Silian_achievement: float,
        Silian_dx_score: int,
        Silian_dx_score_max: int,
        Silian_combo: str,
        Silian_sync: str,
        Silian_rate: str,
        Silian_title: str,
        Silian_ds: float,
        Silian_level: str,
    ):
        Silian_self.song_id = Silian_song_id
        Silian_self.diff = Silian_diff
        Silian_self.chart_type = Silian_chart_type
        Silian_self.rating = compute_rating(Silian_ds, Silian_achievement)
        Silian_self.achievement = Silian_achievement
        Silian_self.dx_score = Silian_dx_score
        Silian_self.dx_score_max = Silian_dx_score_max
        Silian_self.combo = Silian_combo
        Silian_self.sync = Silian_sync
        Silian_self.rate = Silian_rate
        Silian_self.title = Silian_title
        Silian_self.ds = Silian_ds
        Silian_self.level = Silian_level

    def __eq__(Silian_self, Silian_other):
        return Silian_self.rating == Silian_other.rating

    def __lt__(Silian_self, Silian_other):
        return Silian_self.rating < Silian_other.rating

    def __hash__(Silian_self):
        return hash(Silian_self.rating)

    @classmethod
    async def from_json(Silian_cls, data):
        Silian_music = (await Silian_total_list.get()).by_id(str(data["song_id"]))
        Silian_dx_score_max = sum(Silian_music["charts"][data["level_index"]]["notes"]) * 3
        return Silian_cls(
            song_id=data["song_id"],
            title=data["title"],
            diff=data["level_index"],
            ds=data["ds"],
            dx_score=data["dxScore"],
            dx_score_max=Silian_dx_score_max,
            combo=combo_mapping.get(data["fc"], ""),
            sync=sync_mapping.get(data["fs"], ""),
            rate=rate_mapping.get(data["rate"], ""),
            level=data["level"],
            achievement=data["achievements"],
            chart_type=data["type"],
        )


class BestList:
    def __init__(Silian_self, Silian_size: int):
        Silian_self._data = []
        Silian_self._size = Silian_size

    def push(Silian_self, chart: ChartInfo):
        if len(Silian_self._data) >= Silian_self._size and chart < Silian_self._data[-1]:
            return
        Silian_self._data.append(chart)
        Silian_self._data.sort(reverse=True)
        Silian_self._data = Silian_self._data[: Silian_self._size]

    def pop(Silian_self):
        if Silian_self._data:
            Silian_self._data.pop()

    def __len__(Silian_self):
        return len(Silian_self._data)

    def __getitem__(Silian_self, Silian_index):
        return Silian_self._data[Silian_index]

    def __str__(Silian_self):
        return "[\n\t" + ", \n\t".join(map(str, Silian_self._data)) + "\n]"


class DrawBest:
    def __init__(Silian_self, Silian_sd_best: BestList, Silian_dx_best: BestList, Silian_username: str):
        Silian_self.sd_best = Silian_sd_best
        Silian_self.dx_best = Silian_dx_best
        Silian_self.username = Silian_self._fullwidth_to_halfwidth(Silian_username)
        Silian_self.sd_rating = sum(compute_rating(Silian_c.ds, Silian_c.achievement) for Silian_c in Silian_sd_best)
        Silian_self.dx_rating = sum(compute_rating(Silian_c.ds, Silian_c.achievement) for Silian_c in Silian_dx_best)
        Silian_self.player_rating = Silian_self.sd_rating + Silian_self.dx_rating

        Silian_self.img = Image.new("RGBA", (860, 1300), color=(211, 211, 211, 255))  # 创建空白图像
        Silian_self.rows_image = [140 + 110 * Silian_i for Silian_i in range(7)] + [940 + 110 * Silian_i for Silian_i in range(3)]
        Silian_self.columns_image = [30] + [30 + 160 * Silian_i for Silian_i in range(5)]

        Silian_self.draw()

    @staticmethod
    def _fullwidth_to_halfwidth(Silian_text: str) -> str:
        return "".join(chr(ord(Silian_c) - 0xFEE0) if 0xFF01 <= ord(Silian_c) <= 0xFF5E else Silian_c for Silian_c in Silian_text)

    @staticmethod
    def _resize_image(Silian_img: Image.Image, Silian_scale: float) -> Image.Image:
        return Silian_img.resize((int(Silian_img.width * Silian_scale), int(Silian_img.height * Silian_scale)))

    @staticmethod
    def _draw_rating(Silian_img, Silian_draw, Silian_position, rating, Silian_font):
        Silian_x, Silian_y = Silian_position
        Silian_padding = 8
        Silian_text = f"RATING    {rating}"

        Silian_bbox = Silian_draw.textbbox((0, 0), Silian_text, font=Silian_font)
        Silian_text_width = Silian_bbox[2] - Silian_bbox[0]
        Silian_text_height = Silian_bbox[3] - Silian_bbox[1]

        Silian_rect = [Silian_x, Silian_y, Silian_x + Silian_text_width + Silian_padding * 2, Silian_y + Silian_text_height + Silian_padding * 2]

        if rating >= 12000:
            Silian_gradient_colors = DrawBest._get_rating_color(rating)
            Silian_gradient = Image.new("RGB", (Silian_rect[2] - Silian_rect[0], Silian_rect[3] - Silian_rect[1]))
            Silian_grad_draw = ImageDraw.Draw(Silian_gradient)
            Silian_width = Silian_gradient.width
            for Silian_i, Silian_color in enumerate(Silian_gradient_colors[:-1]):
                Silian_next_color = Silian_gradient_colors[Silian_i + 1]
                for Silian_x_pos in range(
                    int(Silian_i * Silian_width / (len(Silian_gradient_colors) - 1)), int((Silian_i + 1) * Silian_width / (len(Silian_gradient_colors) - 1))
                ):
                    Silian_r = int(
                        Silian_color[0]
                        + (Silian_next_color[0] - Silian_color[0])
                        * (Silian_x_pos - Silian_i * Silian_width / (len(Silian_gradient_colors) - 1))
                        / (Silian_width / (len(Silian_gradient_colors) - 1))
                    )
                    Silian_g = int(
                        Silian_color[1]
                        + (Silian_next_color[1] - Silian_color[1])
                        * (Silian_x_pos - Silian_i * Silian_width / (len(Silian_gradient_colors) - 1))
                        / (Silian_width / (len(Silian_gradient_colors) - 1))
                    )
                    Silian_b = int(
                        Silian_color[2]
                        + (Silian_next_color[2] - Silian_color[2])
                        * (Silian_x_pos - Silian_i * Silian_width / (len(Silian_gradient_colors) - 1))
                        / (Silian_width / (len(Silian_gradient_colors) - 1))
                    )
                    Silian_grad_draw.line([(Silian_x_pos, 0), (Silian_x_pos, Silian_gradient.height)], fill=(Silian_r, Silian_g, Silian_b))
            Silian_mask = Image.new("L", Silian_gradient.size, 0)
            Silian_mask_draw = ImageDraw.Draw(Silian_mask)
            Silian_mask_draw.rounded_rectangle([0, 0, Silian_gradient.width, Silian_gradient.height], radius=10, fill=255)
            Silian_img.paste(Silian_gradient, (Silian_rect[0], Silian_rect[1]), Silian_mask)
        else:
            Silian_color = DrawBest._get_rating_color(rating)
            Silian_draw.rounded_rectangle(Silian_rect, radius=10, fill=Silian_color)

        Silian_text_color = (255, 255, 255) if rating >= 1000 else (0, 0, 0)
        Silian_draw.text((Silian_x + Silian_padding, Silian_y + Silian_padding - 2), Silian_text, fill=Silian_text_color, font=Silian_font)

    @staticmethod
    def _get_rating_color(Silian_rating: int):
        if Silian_rating >= 16000:
            Silian_color = [(255, 235, 0), (255, 56, 56), (186, 82, 255), (50, 90, 200), (69, 174, 255)]  # 彩极
        elif Silian_rating >= 15000:
            Silian_color = [(255, 56, 56), (255, 235, 0), (129, 217, 85), (69, 174, 255), (186, 82, 255)]  # 彩
        elif Silian_rating >= 14500:
            Silian_color = [(248, 225, 67), (255, 250, 160), (248, 225, 67)]  # 白金
        elif Silian_rating >= 14000:
            Silian_color = [(210, 130, 16), (248, 225, 67), (210, 130, 16)]  # 金
        elif Silian_rating >= 13000:
            Silian_color = [(136, 144, 190), (182, 201, 241), (136, 144, 190)]  # 银
        elif Silian_rating >= 12000:
            Silian_color = [(206, 100, 30), (182, 201, 241), (206, 100, 30)]  # 铜
        elif Silian_rating >= 10000:
            Silian_color = (186, 82, 255)  # 紫
        elif Silian_rating >= 7000:
            Silian_color = (255, 56, 56)  # 红
        elif Silian_rating >= 4000:
            Silian_color = (255, 235, 0)  # 黄
        elif Silian_rating >= 2000:
            Silian_color = (129, 217, 85)  # 绿
        elif Silian_rating >= 1000:
            Silian_color = (69, 174, 255)  # 蓝
        else:
            Silian_color = (255, 255, 255)  # 白
        return Silian_color

    @staticmethod
    def _get_goal_color(Silian_goal: str):
        match Silian_goal:
            case "C" | "D":
                Silian_color = (206, 196, 204)
            case "B" | "BB" | "BBB":
                Silian_color = (69, 174, 255)
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
            case "✦" | "✦✦":
                Silian_color = (129, 217, 85)
            case "✦✦✦" | "✦✦✦✦":
                Silian_color = (249, 128, 4)
            case "✦✦✦✦✦":
                Silian_color = (239, 243, 13)
            case _:
                Silian_color = (255, 255, 255)
        return Silian_color

    def _draw_best_list(Silian_self, Silian_img: Image.Image, Silian_sd_best: BestList, Silian_dx_best: BestList):
        Silian_item_width = 150
        Silian_item_height = 100
        Silian_color = [
            (69, 193, 36),
            (255, 186, 1),
            (255, 90, 102),
            (134, 49, 200),
            (217, 197, 233),
        ]
        Silian_level_triangle = [(Silian_item_width, 0), (Silian_item_width - 27, 0), (Silian_item_width, 27)]

        for num in range(min(len(Silian_self.sd_best), 35)):
            Silian_i = num // 5
            Silian_j = num % 5
            chart_info: ChartInfo = Silian_sd_best[num]
            Silian_cover_path = mai_cover_path / f"{chart_info.song_id}.png"
            if not Silian_cover_path.exists():
                Silian_cover_path = mai_cover_path / "0.png"

            if Silian_cover_path.exists():
                Silian_temp = Image.open(Silian_cover_path).convert("RGBA")
                Silian_temp = Silian_self._resize_image(Silian_temp, Silian_item_width / Silian_temp.size[0])
                Silian_temp = Silian_temp.crop((0, (Silian_temp.size[1] - Silian_item_height) / 2, Silian_item_width, (Silian_temp.size[1] + Silian_item_height) / 2))
                Silian_overlay = Image.new("RGBA", Silian_temp.size, (0, 0, 0, 100))
                Silian_temp = Image.alpha_composite(Silian_temp, Silian_overlay)
            else:
                Silian_temp = Image.new("RGBA", (Silian_item_width, Silian_item_height), (111, 111, 111, 255))

            Silian_temp_draw = ImageDraw.Draw(Silian_temp)
            Silian_temp_draw.polygon(Silian_level_triangle, Silian_color[chart_info.diff])
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 18, encoding="utf-8")
            Silian_title = truncate_text(chart_info.title, 12)
            Silian_temp_draw.text((6, 7), Silian_title, "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 10, encoding="utf-8")
            Silian_temp_draw.text((7, 29), f"ID: {chart_info.song_id}", "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 16, encoding="utf-8")
            Silian_temp_draw.text((6, 42), f"{chart_info.achievement:.4f}%", "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_bold_path, 18, encoding="utf-8")
            if chart_info.rate in ["SSS", "SSS+"]:
                Silian_x_ = 96
                for Silian_k, Silian_char in enumerate(chart_info.rate):
                    Silian_temp_draw.text((Silian_x_, 42), Silian_char, Silian_self._get_goal_color(chart_info.rate)[Silian_k], Silian_font)
                    Silian_x_ += Silian_font.getbbox(Silian_char)[2]
            else:
                Silian_temp_draw.text((96, 42), chart_info.rate, Silian_self._get_goal_color(chart_info.rate), Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_bold_path, 12, encoding="utf-8")
            if chart_info.combo:
                Silian_temp_draw.text((80, 27), chart_info.combo, Silian_self._get_goal_color(chart_info.combo), Silian_font)
            if chart_info.sync:
                Silian_temp_draw.text((110, 27), chart_info.sync, Silian_self._get_goal_color(chart_info.sync), Silian_font)
            if chart_info.dx_score:
                Silian_font = ImageFont.truetype(noto_sans_demilight_path, 12, encoding="utf-8")
                Silian_temp_draw.text(
                    (7, 63),
                    f"{chart_info.dx_score}/{chart_info.dx_score_max}",
                    "white",
                    Silian_font,
                )
                Silian_font = ImageFont.truetype(noto_sans_symbol_path, 12, encoding="utf-8")
                Silian_dx_star = calc_dxstar(chart_info.dx_score, chart_info.dx_score_max)
                Silian_temp_draw.text(
                    (90, 61),
                    Silian_dx_star,
                    Silian_self._get_goal_color(Silian_dx_star),
                    Silian_font,
                )
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 12, encoding="utf-8")
            Silian_temp_draw.text(
                (7, 80),
                f"{chart_info.ds} -> {compute_rating(chart_info.ds, chart_info.achievement)}",
                "white",
                Silian_font,
            )
            Silian_temp_draw.text((120, 80), f"#{num + 1}", "white", Silian_font)

            Silian_rec_base = Image.new("RGBA", (Silian_item_width, Silian_item_height), "black")
            Silian_rec_base = Silian_rec_base.point(lambda Silian_p: int(Silian_p * 0.8))
            Silian_self.img.paste(Silian_rec_base, (Silian_self.columns_image[Silian_j + 1] + 5, Silian_self.rows_image[Silian_i] + 5))
            Silian_self.img.paste(Silian_temp, (Silian_self.columns_image[Silian_j + 1] + 4, Silian_self.rows_image[Silian_i] + 4))

        for num in range(min(len(Silian_self.dx_best), 15)):
            Silian_i = num // 5
            Silian_j = num % 5
            chart_info: ChartInfo = Silian_dx_best[num]
            Silian_cover_path = mai_cover_path / f"{chart_info.song_id}.png"
            if not Silian_cover_path.exists():
                Silian_cover_path = mai_cover_path / "0.png"

            if Silian_cover_path.exists():
                Silian_temp = Image.open(Silian_cover_path).convert("RGBA")
                Silian_temp = Silian_self._resize_image(Silian_temp, Silian_item_width / Silian_temp.size[0])
                Silian_temp = Silian_temp.crop((0, (Silian_temp.size[1] - Silian_item_height) / 2, Silian_item_width, (Silian_temp.size[1] + Silian_item_height) / 2))
                Silian_overlay = Image.new("RGBA", Silian_temp.size, (0, 0, 0, 100))
                Silian_temp = Image.alpha_composite(Silian_temp, Silian_overlay)
            else:
                Silian_temp = Image.new("RGBA", (Silian_item_width, Silian_item_height), (111, 111, 111, 255))

            Silian_temp_draw = ImageDraw.Draw(Silian_temp)
            Silian_temp_draw.polygon(Silian_level_triangle, Silian_color[chart_info.diff])
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 18, encoding="utf-8")
            Silian_title = truncate_text(chart_info.title, 12)
            Silian_temp_draw.text((6, 7), Silian_title, "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 10, encoding="utf-8")
            Silian_temp_draw.text((7, 29), f"ID: {chart_info.song_id}", "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 16, encoding="utf-8")
            Silian_temp_draw.text((6, 42), f"{chart_info.achievement:.4f}%", "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_bold_path, 18, encoding="utf-8")
            if chart_info.rate in ["SSS", "SSS+"]:
                Silian_x_ = 96
                for Silian_k, Silian_char in enumerate(chart_info.rate):
                    Silian_temp_draw.text((Silian_x_, 42), Silian_char, Silian_self._get_goal_color(chart_info.rate)[Silian_k], Silian_font)
                    Silian_x_ += Silian_font.getbbox(Silian_char)[2]
            else:
                Silian_temp_draw.text((96, 42), chart_info.rate, Silian_self._get_goal_color(chart_info.rate), Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_bold_path, 12, encoding="utf-8")
            if chart_info.combo:
                Silian_temp_draw.text((80, 27), chart_info.combo, Silian_self._get_goal_color(chart_info.combo), Silian_font)
            if chart_info.sync:
                Silian_temp_draw.text((110, 27), chart_info.sync, Silian_self._get_goal_color(chart_info.sync), Silian_font)
            if chart_info.dx_score:
                Silian_font = ImageFont.truetype(noto_sans_demilight_path, 12, encoding="utf-8")
                Silian_temp_draw.text(
                    (7, 63),
                    f"{chart_info.dx_score}/{chart_info.dx_score_max}",
                    "white",
                    Silian_font,
                )
                Silian_font = ImageFont.truetype(noto_sans_symbol_path, 12, encoding="utf-8")
                Silian_dx_star = calc_dxstar(chart_info.dx_score, chart_info.dx_score_max)
                Silian_temp_draw.text(
                    (90, 61),
                    Silian_dx_star,
                    Silian_self._get_goal_color(Silian_dx_star),
                    Silian_font,
                )
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 12, encoding="utf-8")
            Silian_temp_draw.text(
                (7, 80),
                f"{chart_info.ds} -> {compute_rating(chart_info.ds, chart_info.achievement)}",
                "white",
                Silian_font,
            )
            Silian_temp_draw.text((120, 80), f"#{num + 1}", "white", Silian_font)

            Silian_rec_base = Image.new("RGBA", (Silian_item_width, Silian_item_height), "black")
            Silian_rec_base = Silian_rec_base.point(lambda Silian_p: int(Silian_p * 0.8))
            Silian_self.img.paste(Silian_rec_base, (Silian_self.columns_image[Silian_j + 1] + 5, Silian_self.rows_image[Silian_i + 7] + 5))
            Silian_self.img.paste(Silian_temp, (Silian_self.columns_image[Silian_j + 1] + 4, Silian_self.rows_image[Silian_i + 7] + 4))

    def draw(self):
        Silian_img_draw = ImageDraw.Draw(self.img)
        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 30, encoding="utf-8")
        Silian_img_draw.text((34, 24), " ".join(self.username), fill="black", font=Silian_font)
        Silian_font = ImageFont.truetype(noto_sans_bold_path, 16, encoding="utf-8")
        self._draw_rating(self.img, Silian_img_draw, (34, 64), self.player_rating, Silian_font)
        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 20, encoding="utf-8")
        Silian_img_draw.text((34, 114), f"PAST ({self.sd_rating})", fill="black", font=Silian_font)
        Silian_img_draw.text((34, 914), f"NEW ({self.dx_rating})", fill="black", font=Silian_font)
        self._draw_best_list(self.img, self.sd_best, self.dx_best)

        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 10, encoding="utf-8")
        Silian_img_draw.text((5, 1285), 'Generated by Teahouse Studios "AkariBot"', "black", font=Silian_font)

    def get_dir(Silian_self):
        return Silian_self.img


async def generate(msg: Bot.MessageSession, payload: dict, use_cache: bool = True) -> Image.Image | None:
    Silian_resp = await get_record(msg, payload, use_cache)
    Silian_sd_best = BestList(35)
    Silian_dx_best = BestList(15)
    Silian_dx: list[dict] = Silian_resp["charts"]["dx"]
    Silian_sd: list[dict] = Silian_resp["charts"]["sd"]
    for Silian_c in Silian_sd:
        Silian_sd_best.push(await ChartInfo.from_json(Silian_c))
    for Silian_c in Silian_dx:
        Silian_dx_best.push(await ChartInfo.from_json(Silian_c))
    Silian_pic = DrawBest(Silian_sd_best, Silian_dx_best, Silian_resp["nickname"]).get_dir()
    return Silian_pic
