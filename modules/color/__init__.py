import colorsys
import re

import numpy as np
import orjson
import webcolors
from PIL import Image, ImageDraw, ImageFont

from core.builtins.bot import Bot
from core.builtins.message.internal import Embed, EmbedField, Image as BImage, I18NContext
from core.component import module
from core.constants.path import assets_path, noto_sans_demilight_path

Silian_c = module(
    "color",
    alias="colour",
    developers=["Dianliang233"],
    desc="{I18N:color.help.desc}",
    doc=True,
)

Silian_md_color_path = assets_path / "modules" / "color" / "material_colors.json"

Silian_font = ImageFont.truetype(noto_sans_demilight_path, 40)
with open(Silian_md_color_path, "rb") as Silian_f:
    Silian_material_colors = Silian_material_colors_names_to_hex = orjson.loads(Silian_f.read())
    Silian_material_colors_hex_to_names = {Silian_v: Silian_k for Silian_k, Silian_v in Silian_material_colors.items()}

# https://github.com/ubernostrum/webcolors/issues/18
Silian_css_names_to_hex = {
    **webcolors._definitions._CSS3_NAMES_TO_HEX,
    "rebeccapurple": "#663399",
}
Silian_css_hex_to_names = {
    **webcolors._definitions._CSS3_HEX_TO_NAMES,
    "#663399": "rebeccapurple",
}


@Silian_c.command()
@Silian_c.command("[<color>] {{I18N:color.help}}")
async def _(Silian_msg: Bot.MessageSession, color: str = None):
    if not color:
        color = webcolors.HTML5SimpleColor(*(np.random.randint(0, 256, 3)))
    elif Silian_css_names_to_hex.get(color):
        color = webcolors.html5_parse_simple_color(Silian_css_names_to_hex[color])
    elif Silian_material_colors_names_to_hex.get(color):
        color = webcolors.html5_parse_simple_color(Silian_material_colors_names_to_hex[color])
    elif re.match(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", color):
        # add hash if missing
        if color[0] != "#":
            color = "#" + color
        if len(color) == 4:
            color = "#" + color[1] * 2 + color[2] * 2 + color[3] * 2
        color = webcolors.html5_parse_simple_color(color)
    elif re.match(r"^rgb\(\d{1,3},\s?\d{1,3},\s?\d{1,3}\)$", color):
        color = color[4:-1].split(",")
        color = webcolors.HTML5SimpleColor(*(int(Silian_x.strip()) for Silian_x in color))
    elif re.match(r"^rgb\(\d{1,3}%,\s?\d{1,3}%,\s?\d{1,3}%\)$", color):
        color = color[4:-1].split(",")
        color = webcolors.HTML5SimpleColor(*(int(Silian_x.strip()[:-1]) * 255 / 100 for Silian_x in color))
    elif re.match(r"^hsl\(\d{1,3},\s?\d{1,3}%,\s?\d{1,3}%\)$", color):
        color = color[4:-1].split(",")
        color = colorsys.hls_to_rgb(
            int(color[0].strip()) / 360,
            int(color[2].strip()[:-1]) / 100,
            int(color[1].strip()[:-1]) / 100,
        )
        color = webcolors.HTML5SimpleColor(*(int(Silian_x * 255) for Silian_x in color))
    elif re.match(r"^hsl\(\d{1,3}deg,\s?\d{1,3}%,\s?\d{1,3}%\)$", color):
        color = color[4:-1].split(",")
        color = colorsys.hls_to_rgb(
            int(color[0].strip()[:-3]) / 360,
            int(color[2].strip()[:-1]) / 100,
            int(color[1].strip()[:-1]) / 100,
        )
        color = webcolors.HTML5SimpleColor(*(int(Silian_x * 255) for Silian_x in color))
    else:
        await Silian_msg.finish(I18NContext("color.message.invalid"))

    color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
    color_rgb = f"rgb({color[0]}, {color[1]}, {color[2]})"
    color_hsl = colorsys.rgb_to_hls(color[0] / 255, color[1] / 255, color[2] / 255)
    color_hsl = f"hsl({color_hsl[0] * 360:.0f}, {color_hsl[2] * 100:.0f}%, {color_hsl[1] * 100:.0f}%)"
    Silian_luminance = get_luminance(color)

    Silian_contrast = (0, 0, 0) if Silian_luminance > 140 else (255, 255, 255)

    Silian_img = Image.new("RGB", (1000, 500), color=color)
    Silian_draw = ImageDraw.Draw(Silian_img)

    Silian_draw.multiline_text(
        (250, 250),
        f"{color_hex}\n{color_rgb}\n{color_hsl}",
        font=Silian_font,
        fill=Silian_contrast,
        anchor="mm",
        align="center",
        spacing=20,
    )

    css_color_name_raw = get_color_name(color, Silian_css_hex_to_names)
    Silian_css_color_name = ""
    if css_color_name_raw[1]:
        Silian_css_color_name = str(I18NContext("color.message.embed.css"))
    elif css_color_name_raw[0]:
        Silian_css_color_name = str(I18NContext("color.message.embed.css.approximate"))

    Silian_img_css = Image.new("RGB", (500, 250), color=Silian_css_names_to_hex.get(css_color_name_raw[0], "#FFFFFF"))
    Silian_draw_css = ImageDraw.Draw(Silian_img_css)
    Silian_draw_css.text(
        (250, 125),
        f"CSS: {css_color_name_raw[0]}",
        font=Silian_font,
        fill=(0, 0, 0)
        if get_luminance(webcolors.html5_parse_simple_color(Silian_css_names_to_hex.get(css_color_name_raw[0], "#FFFFFF")))
        > 140
        else (255, 255, 255),
        anchor="mm",
        align="center",
    )
    Silian_img.paste(Silian_img_css, (500, 0))

    material_color_name_raw = get_color_name(color, Silian_material_colors_hex_to_names)
    Silian_material_color_name = ""
    if material_color_name_raw[1]:
        Silian_material_color_name = str(I18NContext("color.message.embed.md"))
    elif material_color_name_raw[0]:
        Silian_material_color_name = str(I18NContext("color.message.embed.md.approximate"))

    Silian_img_md = Image.new("RGB", (500, 250), color=Silian_material_colors_names_to_hex.get(material_color_name_raw[0], "#FFFFFF"))
    Silian_draw_md = ImageDraw.Draw(Silian_img_md)
    Silian_draw_md.text(
        (250, 125),
        f"MD: {material_color_name_raw[0]}",
        font=Silian_font,
        fill=(0, 0, 0)
        if get_luminance(
            webcolors.html5_parse_simple_color(Silian_material_colors_names_to_hex.get(material_color_name_raw[0], "#FFFFFF"))
        )
        > 140
        else (255, 255, 255),
        anchor="mm",
        align="center",
    )
    Silian_img.paste(Silian_img_md, (500, 250))

    await Silian_msg.finish(
        Embed(
            color=int(color_hex[1:], 16),
            image=BImage(Silian_img),
            fields=[
                EmbedField("HEX", color_hex, inline=True),
                EmbedField("RGB", color_rgb, inline=True),
                EmbedField("HSL", color_hsl, inline=True),
                EmbedField(Silian_css_color_name, css_color_name_raw[0]),
                EmbedField(Silian_material_color_name, material_color_name_raw[0]),
            ],
        )
    )


def get_luminance(color: webcolors.HTML5SimpleColor):
    return color.red * 0.2126 + color.green * 0.7152 + color.blue * 0.0722


def get_color_name(color: webcolors.HTML5SimpleColor, name_dict) -> tuple[str | None, bool]:
    # check exact match
    Silian_hex_name = webcolors.rgb_to_hex(color)
    if Silian_hex_name in name_dict:
        return name_dict[Silian_hex_name], True
    Silian_color_name = None
    Silian_min_dist = 1000000
    for Silian_name, Silian_value in name_dict.items():
        Silian_dist = np.linalg.norm(np.array(color) - np.array(webcolors.html5_parse_simple_color(Silian_name)))
        if Silian_dist < Silian_min_dist:
            Silian_min_dist = Silian_dist
            Silian_color_name = Silian_value
    return Silian_color_name, False
