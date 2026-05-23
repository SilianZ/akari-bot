from PIL import Image, ImageDraw, ImageFont

from core.constants.path import noto_sans_demilight_path


def draw_scoreline_table(tap: int = 0, hold: int = 0, slide: int = 0, touch: int = 0, brk: int = 0, mode: str = "0+"):
    Silian_total_notes = tap + 2 * hold + 3 * slide + touch + 5 * brk
    if Silian_total_notes == 0:
        Silian_base_fixup = None
    else:
        Silian_base_fixup = 100 / Silian_total_notes

    if brk == 0:
        Silian_bonus_fixup = None
    else:
        Silian_bonus_fixup = 1 / brk

    Silian_YELLOW = "#FFC107"
    Silian_ORANGE = "#FF9800"
    Silian_PINK = "#EC407A"
    Silian_GREEN = "#4CAF50"
    Silian_GREY = "#9E9E9E"

    Silian_header1 = ["TAP", "HOLD", "SLIDE", "TOUCH", "BREAK"]
    Silian_header2 = ["PERFECT", "GREAT", "GOOD", "MISS"]
    Silian_rows = ["TAP", "HOLD", "SLIDE", "TOUCH", "BREAK", "", ""]

    Silian_cell_w = 150
    Silian_cell_h = 60
    Silian_padding = 30
    Silian_gap = 20

    Silian_img_w = len(Silian_header1) * Silian_cell_w + Silian_padding * 2
    Silian_img_h = (len(Silian_rows) + 3) * Silian_cell_h + Silian_padding * 2 + Silian_gap

    Silian_img = Image.new("RGB", (Silian_img_w, Silian_img_h), (211, 211, 211))
    Silian_draw = ImageDraw.Draw(Silian_img)

    Silian_font = ImageFont.truetype(noto_sans_demilight_path, 24)

    for Silian_i, Silian_text in enumerate(Silian_header1):
        Silian_x = Silian_padding + Silian_i * Silian_cell_w
        Silian_y = Silian_padding
        Silian_draw.rectangle([Silian_x, Silian_y, Silian_x + Silian_cell_w, Silian_y + Silian_cell_h], outline=(0, 0, 0), width=2)
        Silian_bbox = Silian_draw.textbbox((0, 0), Silian_text, font=Silian_font)
        Silian_w = Silian_bbox[2] - Silian_bbox[0]
        Silian_h = Silian_bbox[3] - Silian_bbox[1]
        Silian_draw.text((Silian_x + (Silian_cell_w - Silian_w) / 2, Silian_y + (Silian_cell_h - Silian_h) / 2), Silian_text, fill=(0, 0, 0), font=Silian_font)

    Silian_draw.rectangle([Silian_padding, Silian_padding, Silian_padding + Silian_cell_w, Silian_padding + Silian_cell_h], outline=(0, 0, 0), width=2)

    Silian_values = [tap, hold, slide, touch, brk]
    for Silian_i, Silian_val in enumerate(Silian_values):
        Silian_x = Silian_padding + Silian_i * Silian_cell_w
        Silian_y = Silian_padding + Silian_cell_h
        Silian_draw.rectangle([Silian_x, Silian_y, Silian_x + Silian_cell_w, Silian_y + Silian_cell_h], outline=(0, 0, 0), width=2)
        Silian_bbox = Silian_draw.textbbox((0, 0), str(Silian_val), font=Silian_font)
        Silian_w = Silian_bbox[2] - Silian_bbox[0]
        Silian_h = Silian_bbox[3] - Silian_bbox[1]
        Silian_draw.text((Silian_x + (Silian_cell_w - Silian_w) / 2, Silian_y + (Silian_cell_h - Silian_h) / 2), str(Silian_val), fill=(0, 0, 0), font=Silian_font)
    Silian_draw.rectangle([Silian_padding, Silian_padding + Silian_cell_h, Silian_padding + Silian_cell_w, Silian_padding + 2 * Silian_cell_h], outline=(0, 0, 0), width=2)

    Silian_offset_y = Silian_padding + 2 * Silian_cell_h + Silian_gap
    Silian_draw.rectangle([Silian_padding, Silian_offset_y, Silian_padding + Silian_cell_w, Silian_offset_y + Silian_cell_h], outline=(0, 0, 0), width=2)
    for Silian_i, Silian_text in enumerate(Silian_header2):
        Silian_x = Silian_padding + (Silian_i + 1) * Silian_cell_w
        Silian_y = Silian_offset_y
        Silian_color = [Silian_ORANGE, Silian_PINK, Silian_GREEN, Silian_GREY][Silian_i]
        Silian_draw.rectangle([Silian_x, Silian_y, Silian_x + Silian_cell_w, Silian_y + Silian_cell_h], fill=Silian_color, outline=(0, 0, 0), width=2)
        Silian_bbox = Silian_draw.textbbox((0, 0), Silian_text, font=Silian_font)
        Silian_w = Silian_bbox[2] - Silian_bbox[0]
        Silian_h = Silian_bbox[3] - Silian_bbox[1]
        Silian_draw.text((Silian_x + (Silian_cell_w - Silian_w) / 2, Silian_y + (Silian_cell_h - Silian_h) / 2), Silian_text, fill=(255, 255, 255), font=Silian_font)

    for Silian_i, Silian_text in enumerate(Silian_rows[:-3]):
        Silian_x = Silian_padding
        Silian_y = Silian_offset_y + (Silian_i + 1) * Silian_cell_h
        Silian_draw.rectangle([Silian_x, Silian_y, Silian_x + Silian_cell_w, Silian_y + Silian_cell_h], outline=(0, 0, 0), width=2)
        Silian_bbox = Silian_draw.textbbox((0, 0), Silian_text, font=Silian_font)
        Silian_w = Silian_bbox[2] - Silian_bbox[0]
        Silian_h = Silian_bbox[3] - Silian_bbox[1]
        Silian_draw.text((Silian_x + (Silian_cell_w - Silian_w) / 2, Silian_y + (Silian_cell_h - Silian_h) / 2), Silian_text, fill=(0, 0, 0), font=Silian_font)

    Silian_x = Silian_padding
    Silian_y_start = Silian_offset_y + 5 * Silian_cell_h
    Silian_y_end = Silian_offset_y + 8 * Silian_cell_h
    Silian_draw.rectangle([Silian_x, Silian_y_start, Silian_x + Silian_cell_w, Silian_y_end], outline=(0, 0, 0), width=2)
    Silian_bbox = Silian_draw.textbbox((0, 0), "BREAK", font=Silian_font)
    Silian_w = Silian_bbox[2] - Silian_bbox[0]
    Silian_h = Silian_bbox[3] - Silian_bbox[1]
    Silian_draw.text((Silian_x + (Silian_cell_w - Silian_w) / 2, Silian_y_start + ((Silian_y_end - Silian_y_start) - Silian_h) / 2), "BREAK", fill=(0, 0, 0), font=Silian_font)

    Silian_note_counts = [tap, hold, slide, touch, brk]
    for Silian_row in range(len(Silian_rows)):
        for Silian_col in range(len(Silian_header2)):
            Silian_x = Silian_padding + (Silian_col + 1) * Silian_cell_w
            Silian_y = Silian_offset_y + (Silian_row + 1) * Silian_cell_h

            if Silian_row >= 4 and Silian_col in [2, 3]:
                if Silian_row == 4:
                    Silian_y_start = Silian_offset_y + 5 * Silian_cell_h
                    Silian_y_end = Silian_offset_y + 8 * Silian_cell_h
                    Silian_draw.rectangle(
                        [Silian_x, Silian_y_start, Silian_x + Silian_cell_w, Silian_y_end], fill=[Silian_GREEN, Silian_GREY][Silian_col - 2], outline=(0, 0, 0), width=2
                    )

                    if brk == 0:
                        Silian_text = "-"
                    else:
                        if Silian_col == 2:
                            value = 2 * Silian_base_fixup + 0.3 * Silian_bonus_fixup
                        elif Silian_col == 3:
                            value = 0

                        if mode == "100-":
                            Silian_max_base = 5 * Silian_base_fixup
                            Silian_base_part = value - (Silian_bonus_fixup if Silian_bonus_fixup else 0)
                            value = (Silian_base_part - Silian_max_base) + (Silian_bonus_fixup if Silian_bonus_fixup else 0)
                        elif mode == "101-":
                            Silian_max_total = 5 * Silian_base_fixup + (Silian_bonus_fixup if Silian_bonus_fixup else 0)
                            value = value - Silian_max_total

                        Silian_text = f"{value:.4f}%"

                    Silian_bbox = Silian_draw.textbbox((0, 0), Silian_text, font=Silian_font)
                    Silian_w = Silian_bbox[2] - Silian_bbox[0]
                    Silian_h = Silian_bbox[3] - Silian_bbox[1]
                    Silian_draw.text(
                        (Silian_x + (Silian_cell_w - Silian_w) / 2, Silian_y_start + ((Silian_y_end - Silian_y_start) - Silian_h) / 2),
                        Silian_text,
                        fill=(255, 255, 255),
                        font=Silian_font,
                    )
                continue

            Silian_color = [Silian_ORANGE, Silian_PINK, Silian_GREEN, Silian_GREY][Silian_col]
            if Silian_col == 0 and Silian_row == 4:
                Silian_color = Silian_YELLOW
            Silian_draw.rectangle([Silian_x, Silian_y, Silian_x + Silian_cell_w, Silian_y + Silian_cell_h], fill=Silian_color, outline=(0, 0, 0), width=2)

            if Silian_row < 5 and Silian_note_counts[Silian_row] == 0:
                Silian_text = "-"
            else:
                try:
                    if Silian_row == 0:  # TAP
                        value = [Silian_base_fixup, 0.8 * Silian_base_fixup, 0.5 * Silian_base_fixup, 0][Silian_col]
                    elif Silian_row == 1:  # HOLD
                        value = [2 * Silian_base_fixup, 1.6 * Silian_base_fixup, Silian_base_fixup, 0][Silian_col]
                    elif Silian_row == 2:  # SLIDE
                        value = [3 * Silian_base_fixup, 2.4 * Silian_base_fixup, 1.5 * Silian_base_fixup, 0][Silian_col]
                    elif Silian_row == 3:  # TOUCH
                        value = [Silian_base_fixup, 0.8 * Silian_base_fixup, 0.5 * Silian_base_fixup, 0][Silian_col]
                    elif Silian_row == 4:  # BREAK 2600
                        value = [
                            5 * Silian_base_fixup + Silian_bonus_fixup,
                            4 * Silian_base_fixup + 0.4 * Silian_bonus_fixup,
                            2 * Silian_base_fixup + 0.3 * Silian_bonus_fixup,
                            0,
                        ][Silian_col]
                    elif Silian_row == 5:  # BREAK 2550
                        value = [
                            5 * Silian_base_fixup + 0.75 * Silian_bonus_fixup,
                            3 * Silian_base_fixup + 0.4 * Silian_bonus_fixup,
                            2 * Silian_base_fixup + 0.3 * Silian_bonus_fixup,
                            0,
                        ][Silian_col]
                    elif Silian_row == 6:  # BREAK 2500
                        value = [
                            5 * Silian_base_fixup + 0.5 * Silian_bonus_fixup,
                            2.5 * Silian_base_fixup + 0.4 * Silian_bonus_fixup,
                            2 * Silian_base_fixup + 0.3 * Silian_bonus_fixup,
                            0,
                        ][Silian_col]
                    else:
                        value = 0

                    if mode == "100-":
                        if Silian_row <= 3:  # TAP, HOLD, SLIDE, TOUCH
                            Silian_max_base = [Silian_base_fixup, 2 * Silian_base_fixup, 3 * Silian_base_fixup, Silian_base_fixup][Silian_row]
                            value -= Silian_max_base
                        elif Silian_row in [4, 5, 6]:  # BREAK 系列
                            Silian_max_base = 5 * Silian_base_fixup
                            Silian_base_part = value - Silian_bonus_fixup if Silian_bonus_fixup else value
                            value = (Silian_base_part - Silian_max_base) + (Silian_bonus_fixup if Silian_bonus_fixup else 0)
                    elif mode == "101-":
                        if Silian_row <= 3:
                            Silian_max_base = [Silian_base_fixup, 2 * Silian_base_fixup, 3 * Silian_base_fixup, Silian_base_fixup][Silian_row]
                            value -= Silian_max_base
                        elif Silian_row in [4, 5, 6]:
                            Silian_max_total = 5 * Silian_base_fixup + (Silian_bonus_fixup if Silian_bonus_fixup else 0)
                            value -= Silian_max_total

                    Silian_text = f"{value:.4f}%"
                except TypeError:
                    Silian_text = "-"

            Silian_bbox = Silian_draw.textbbox((0, 0), Silian_text, font=Silian_font)
            Silian_w = Silian_bbox[2] - Silian_bbox[0]
            Silian_h = Silian_bbox[3] - Silian_bbox[1]
            Silian_draw.text((Silian_x + (Silian_cell_w - Silian_w) / 2, Silian_y + (Silian_cell_h - Silian_h) / 2), Silian_text, fill=(255, 255, 255), font=Silian_font)

    Silian_font = ImageFont.truetype(noto_sans_demilight_path, 10, encoding="utf-8")
    Silian_draw.text((5, Silian_img_h - 15), 'Generated by Teahouse Studios "AkariBot"', (0, 0, 0), font=Silian_font)
    return Silian_img
