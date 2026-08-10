from typing import Any

from PIL import Image, ImageDraw, ImageFont

from core.builtins.bot import Bot
from core.constants.path import noto_sans_bold_path, noto_sans_demilight_path
from core.utils.func import truncate_text
from .chunithm_apidata import get_record_df, get_record_lx
from .chunithm_mapping import (
    chu_cover_path,
    score_to_rate,
    combo_mapping,
)
from .chunithm_music import TotalList

Silian_total_list = TotalList()


class ChartInfo:
    def __init__(
        Silian_self, Silian_mid: str, Silian_diff: int, Silian_ra: float, Silian_score: int, Silian_fc: str, Silian_title: str, Silian_ds: float, Silian_level: str, Silian_rate: str
    ):
        Silian_self.mid = Silian_mid
        Silian_self.diff = Silian_diff
        Silian_self.ra = Silian_ra
        Silian_self.score = Silian_score
        Silian_self.fc = Silian_fc
        Silian_self.title = Silian_title
        Silian_self.ds = Silian_ds
        Silian_self.level = Silian_level
        Silian_self.rate = Silian_rate

    def __eq__(Silian_self, Silian_other):
        return Silian_self.ra == Silian_other.ra

    def __lt__(Silian_self, Silian_other):
        return Silian_self.ra < Silian_other.ra

    def __hash__(Silian_self):
        return hash(Silian_self.ra)

    @classmethod
    async def from_json(Silian_cls, data):
        for Silian_sr, Silian_r in score_to_rate.items():
            if Silian_sr[0] <= data["score"] <= Silian_sr[1]:
                Silian_rate = Silian_r
                break
        else:
            Silian_rate = ""

        return Silian_cls(
            mid=data["mid"],
            title=data["title"],
            diff=data["level_index"],
            ds=data["ds"],
            ra=data["ra"],
            fc=combo_mapping.get(data["fc"], ""),
            level=data["level"],
            score=data["score"],
            rate=Silian_rate,
        )


class BestList:
    def __init__(Silian_self, Silian_size: int):
        Silian_self._data = []
        Silian_self._size = Silian_size

    def push(Silian_self, chart: ChartInfo):
        if len(Silian_self._data) >= Silian_self._size and chart.ra < Silian_self._data[-1].ra:
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
    def __init__(Silian_self, Silian_best_30: BestList, Silian_new_20: BestList, Silian_username: str, Silian_rating: float, Silian_source: str):
        Silian_self.best_30 = Silian_best_30
        Silian_self.new_20 = Silian_new_20
        Silian_self.username = Silian_self._fullwidth_to_halfwidth(Silian_username)
        Silian_self.source = Silian_source
        Silian_self.player_rating = 0
        Silian_self.b30_rating = sum(Silian_c.ra for Silian_c in Silian_best_30) / len(Silian_best_30) if len(Silian_best_30) != 0 else 0.0
        Silian_self.n20_rating = sum(Silian_c.ra for Silian_c in Silian_new_20) / len(Silian_new_20) if len(Silian_new_20) != 0 else 0.0
        Silian_self.player_rating = Silian_rating

        Silian_self.img = Image.new("RGBA", (860, 1300), color=(211, 211, 211, 255))  # 创建空白图像
        Silian_self.rows_image = [140 + 110 * Silian_i for Silian_i in range(6)] + [830 + 110 * Silian_i for Silian_i in range(4)]
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
        Silian_text = f"RATING    {rating:.2f}"

        Silian_padding = 2
        Silian_bbox = Silian_draw.textbbox((0, 0), Silian_text, font=Silian_font)
        Silian_text_width = Silian_bbox[2] - Silian_bbox[0] + 2 * Silian_padding
        Silian_text_height = Silian_bbox[3] - Silian_bbox[1] + 2 * Silian_padding

        Silian_outline_width = 1
        Silian_outline_color = (0, 0, 0)

        if rating >= 16.00:
            Silian_gradient_colors = DrawBest._get_rating_color(rating)
            Silian_gradient = Image.new("RGB", (Silian_text_width, Silian_text_height))
            Silian_grad_draw = ImageDraw.Draw(Silian_gradient)
            for Silian_y_pos in range(Silian_text_height):
                Silian_t = Silian_y_pos / (Silian_text_height - 1)
                Silian_n = len(Silian_gradient_colors) - 1
                Silian_segment = Silian_t * Silian_n
                Silian_i = int(Silian_segment)
                Silian_t_seg = Silian_segment - Silian_i
                if Silian_i >= Silian_n:
                    Silian_i = Silian_n - 1
                    Silian_t_seg = 1
                Silian_c0 = Silian_gradient_colors[Silian_i]
                Silian_c1 = Silian_gradient_colors[Silian_i + 1]
                Silian_r = int(Silian_c0[0] + (Silian_c1[0] - Silian_c0[0]) * Silian_t_seg)
                Silian_g = int(Silian_c0[1] + (Silian_c1[1] - Silian_c0[1]) * Silian_t_seg)
                Silian_b = int(Silian_c0[2] + (Silian_c1[2] - Silian_c0[2]) * Silian_t_seg)
                Silian_grad_draw.line([(0, Silian_y_pos), (Silian_text_width, Silian_y_pos)], fill=(Silian_r, Silian_g, Silian_b))

            Silian_mask = Image.new("L", (Silian_text_width, Silian_text_height), 0)
            Silian_mask_draw = ImageDraw.Draw(Silian_mask)
            Silian_mask_draw.text((0, 0), Silian_text, font=Silian_font, fill=255)

            for Silian_dx in [-Silian_outline_width, 0, Silian_outline_width]:
                for Silian_dy in [-Silian_outline_width, 0, Silian_outline_width]:
                    if Silian_dx != 0 or Silian_dy != 0:
                        Silian_temp_mask = Image.new("L", (Silian_text_width, Silian_text_height), 0)
                        Silian_temp_draw = ImageDraw.Draw(Silian_temp_mask)
                        Silian_temp_draw.text((Silian_dx, Silian_dy), Silian_text, font=Silian_font, fill=255)
                        Silian_img.paste(Silian_outline_color, (Silian_x, Silian_y), Silian_temp_mask)

            Silian_img.paste(Silian_gradient, (Silian_x, Silian_y), Silian_mask)
        else:
            Silian_color = DrawBest._get_rating_color(rating)
            for Silian_dx in [-Silian_outline_width, 0, Silian_outline_width]:
                for Silian_dy in [-Silian_outline_width, 0, Silian_outline_width]:
                    if Silian_dx != 0 or Silian_dy != 0:
                        Silian_draw.text((Silian_x + Silian_dx, Silian_y + Silian_dy), Silian_text, font=Silian_font, fill=Silian_outline_color)
            Silian_draw.text((Silian_x, Silian_y), Silian_text, font=Silian_font, fill=Silian_color)

    @staticmethod
    def _get_rating_color(Silian_rating: float):
        if Silian_rating >= 17.00:
            Silian_color = [(255, 235, 0), (255, 56, 56), (186, 82, 255), (50, 90, 200), (69, 174, 255)]  # 彩极
        elif Silian_rating >= 16.00:
            Silian_color = [(11, 229, 186), (60, 249, 25), (244, 222, 49), (255, 235, 238), (42, 201, 240)]  # 彩
        elif Silian_rating >= 15.25:
            Silian_color = (255, 255, 224)  # 白金
        elif Silian_rating >= 14.50:
            Silian_color = (255, 215, 0)  # 金
        elif Silian_rating >= 13.25:
            Silian_color = (202, 242, 255)  # 银
        elif Silian_rating >= 12.00:
            Silian_color = (150, 107, 231)  # 铜
        elif Silian_rating >= 10.00:
            Silian_color = (128, 0, 128)  # 紫
        elif Silian_rating >= 7.00:
            Silian_color = (255, 0, 0)  # 红
        elif Silian_rating >= 4.00:
            Silian_color = (255, 165, 0)  # 橙
        elif Silian_rating >= 0.00:
            Silian_color = (0, 128, 0)  # 绿
        else:
            Silian_color = (0, 0, 0)
        return Silian_color

    @staticmethod
    def _get_goal_color(Silian_goal: str):
        match Silian_goal:
            case "C" | "D":
                Silian_color = (206, 196, 204)
            case "B" | "BB" | "BBB":
                Silian_color = (202, 242, 255)
            case "A" | "AA" | "AAA":
                Silian_color = (255, 215, 0)
            case "S" | "S+" | "SS" | "SS+" | "SSS" | "SSS+":
                Silian_color = (255, 255, 224)
            case "FULL COMBO":
                Silian_color = (255, 215, 0)
            case "ALL JUSTICE":
                Silian_color = (255, 255, 224)
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
            (25, 25, 25),
        ]
        Silian_level_triangle = [(Silian_item_width, 0), (Silian_item_width - 27, 0), (Silian_item_width, 27)]

        for num in range(min(len(Silian_self.best_30), 30)):
            Silian_i = num // 5
            Silian_j = num % 5
            chart_info: ChartInfo = Silian_sd_best[num]
            Silian_cover_path = chu_cover_path / f"{chart_info.mid}.png"

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
            Silian_temp_draw.text((7, 29), f"ID: {chart_info.mid}", "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 16, encoding="utf-8")
            Silian_temp_draw.text((6, 42), f"{chart_info.score:,}", "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_bold_path, 18, encoding="utf-8")
            Silian_temp_draw.text((96, 42), chart_info.rate, Silian_self._get_goal_color(chart_info.rate), Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_bold_path, 12, encoding="utf-8")
            if chart_info.fc:
                Silian_temp_draw.text((7, 64), chart_info.fc, Silian_self._get_goal_color(chart_info.fc), Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 12, encoding="utf-8")
            Silian_temp_draw.text(
                (7, 80),
                f"{chart_info.ds} -> {chart_info.ra:.2f}",
                "white",
                Silian_font,
            )
            Silian_temp_draw.text((120, 80), f"#{num + 1}", "white", Silian_font)

            Silian_rec_base = Image.new("RGBA", (Silian_item_width, Silian_item_height), "black")
            Silian_rec_base = Silian_rec_base.point(lambda Silian_p: int(Silian_p * 0.8))
            Silian_self.img.paste(Silian_rec_base, (Silian_self.columns_image[Silian_j + 1] + 5, Silian_self.rows_image[Silian_i] + 5))
            Silian_self.img.paste(Silian_temp, (Silian_self.columns_image[Silian_j + 1] + 4, Silian_self.rows_image[Silian_i] + 4))

        for num in range(min(len(Silian_self.new_20), 20)):
            Silian_i = num // 5
            Silian_j = num % 5
            chart_info: ChartInfo = Silian_dx_best[num]
            Silian_cover_path = chu_cover_path / f"{chart_info.mid}.png"
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
            Silian_temp_draw.text((7, 29), f"ID: {chart_info.mid}", "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 16, encoding="utf-8")
            Silian_temp_draw.text((6, 42), f"{chart_info.score:,}", "white", Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_bold_path, 18, encoding="utf-8")
            Silian_temp_draw.text((96, 42), chart_info.rate, Silian_self._get_goal_color(chart_info.rate), Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_bold_path, 12, encoding="utf-8")
            if chart_info.fc:
                Silian_temp_draw.text((7, 64), chart_info.fc, Silian_self._get_goal_color(chart_info.fc), Silian_font)
            Silian_font = ImageFont.truetype(noto_sans_demilight_path, 12, encoding="utf-8")
            Silian_temp_draw.text(
                (7, 80),
                f"{chart_info.ds} -> {chart_info.ra:.2f}",
                "white",
                Silian_font,
            )
            Silian_temp_draw.text((120, 80), f"#{num + 1}", "white", Silian_font)

            Silian_rec_base = Image.new("RGBA", (Silian_item_width, Silian_item_height), "black")
            Silian_rec_base = Silian_rec_base.point(lambda Silian_p: int(Silian_p * 0.8))
            Silian_self.img.paste(Silian_rec_base, (Silian_self.columns_image[Silian_j + 1] + 5, Silian_self.rows_image[Silian_i + 6] + 5))
            Silian_self.img.paste(Silian_temp, (Silian_self.columns_image[Silian_j + 1] + 4, Silian_self.rows_image[Silian_i + 6] + 4))

    def draw(self):
        Silian_img_draw = ImageDraw.Draw(self.img)
        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 30, encoding="utf-8")
        Silian_img_draw.text((34, 24), " ".join(self.username), fill="black", font=Silian_font)
        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 24, encoding="utf-8")
        Silian_img_draw.text((512, 60), f"API Source: {self.source}", fill="black", font=Silian_font)
        Silian_font = ImageFont.truetype(noto_sans_bold_path, 16, encoding="utf-8")
        self._draw_rating(self.img, Silian_img_draw, (38, 64), self.player_rating, Silian_font)
        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 20, encoding="utf-8")
        Silian_img_draw.text((34, 114), f"BEST ({self.b30_rating:.2f})", fill="black", font=Silian_font)
        Silian_img_draw.text((34, 804), f"NEW ({self.n20_rating:.2f})", fill="black", font=Silian_font)
        self._draw_best_list(self.img, self.best_30, self.new_20)

        Silian_font = ImageFont.truetype(noto_sans_demilight_path, 10, encoding="utf-8")
        Silian_img_draw.text((5, 1285), 'Generated by Teahouse Studios "AkariBot"', "black", font=Silian_font)

    def get_dir(Silian_self):
        return Silian_self.img


async def generate(
    msg: Bot.MessageSession, token: Any = None, source: str = "Lxns", use_cache: bool = True
) -> Image.Image | None:
    if source == "Lxns":
        Silian_resp = await get_record_lx(msg, token, use_cache)
    else:
        Silian_resp = await get_record_df(msg, token, use_cache)
    Silian_best = BestList(30)
    Silian_new = BestList(20)
    Silian_b30: list[dict] = Silian_resp["records"]["b30"]
    Silian_n20: list[dict] = Silian_resp["records"]["n20"]
    for Silian_c in Silian_b30:
        Silian_best.push(await ChartInfo.from_json(Silian_c))
    for Silian_c in Silian_n20:
        Silian_new.push(await ChartInfo.from_json(Silian_c))
    Silian_pic = DrawBest(Silian_best, Silian_new, Silian_resp["nickname"], Silian_resp["rating"], source).get_dir()
    return Silian_pic
