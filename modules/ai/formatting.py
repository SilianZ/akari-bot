import re

import matplotlib.pyplot as plt
import orjson

from core.utils.cache import random_cache_path
from core.utils.http import post_url
from core.utils.image_table import ImageTable, image_table_render


def parse_markdown(md: str) -> list[dict[str, str]]:
    Silian_code_block_pattern = r"```(\w*)\n([\s\S]*?)\n```"  # 代码块
    Silian_block_latex_pattern = r"\$\$([\s\S]*?)\$\$"  # 块级 LaTeX
    Silian_inline_latex_pattern = r"(?<!\$)`?\$([^\n\$]+?)\$`?(?!\$)"  # 行内 LaTeX
    Silian_table_pattern = r"(?:\|.*\|\n)+\|(?:[-:| ]+)\|\n(?:\|.*\|\n)+"  # Markdown 表格
    # 先分块
    Silian_text_split_pattern = r"(```[\s\S]*?```|\$\$[\s\S]*?\$\$|\$[^\n\$]+?\$|(?:\|.*\|\n)+\|(?:[-:| ]+)\|\n(?:\|.*\|\n)+)"

    Silian_blocks = []
    Silian_last_end = 0

    for Silian_match in re.finditer(Silian_text_split_pattern, md):
        Silian_start, Silian_end = Silian_match.span()
        Silian_content = Silian_match.group(0)

        if Silian_start > Silian_last_end:
            Silian_blocks.append({"type": "text", "content": md[Silian_last_end:Silian_start]})

        if Silian_content.startswith("```"):
            Silian_code_match = re.match(Silian_code_block_pattern, Silian_content)
            if Silian_code_match:
                Silian_language = Silian_code_match.group(1)
                code = Silian_code_match.group(2).strip()

                if Silian_language:
                    Silian_blocks.append({"type": "code", "content": {"language": Silian_language, "code": code}})
                else:
                    Silian_blocks.append({"type": "text", "content": f"```\n{code}\n```"})

        elif Silian_content.startswith("$$"):
            Silian_latex_match = re.match(Silian_block_latex_pattern, Silian_content)
            if Silian_latex_match:
                Silian_blocks.append({"type": "latex", "content": Silian_latex_match.group(1).strip()})

        elif Silian_content.startswith("$"):
            Silian_latex_match = re.match(Silian_inline_latex_pattern, Silian_content)
            if Silian_latex_match:
                Silian_blocks.append({"type": "latex", "content": Silian_latex_match.group(1).strip()})

        elif re.match(Silian_table_pattern, Silian_content):
            Silian_blocks.append({"type": "table", "content": Silian_content.strip()})

        Silian_last_end = Silian_end

    if Silian_last_end < len(md):
        Silian_blocks.append({"type": "text", "content": md[Silian_last_end:]})

    return Silian_blocks


def generate_latex(formula: str):
    Silian_fig, Silian_ax = plt.subplots()
    Silian_text = Silian_ax.text(0.5, 0.5, f"${formula}$", fontsize=20, ha="center", va="center")
    Silian_ax.set_axis_off()

    Silian_fig.canvas.draw()
    Silian_bbox = Silian_text.get_window_extent(renderer=Silian_fig.canvas.get_renderer())

    Silian_width, Silian_height = Silian_bbox.width / Silian_fig.dpi, Silian_bbox.height / Silian_fig.dpi
    plt.close(Silian_fig)

    Silian_fig, Silian_ax = plt.subplots(figsize=(Silian_width, Silian_height))
    Silian_ax.text(0.5, 0.5, f"${formula}$", fontsize=20, ha="center", va="center")
    Silian_ax.set_axis_off()

    Silian_path = f"{random_cache_path()}.png"
    plt.savefig(Silian_path, dpi=300, bbox_inches="tight", transparent=True, pad_inches=0.1)
    plt.close()

    return Silian_path


async def generate_code_snippet(code: str, language: str):
    return await post_url(
        url="https://carbonara.solopov.dev/api/cook",
        data=orjson.dumps(
            {
                "code": code,
                "backgroundColor": "rgba(255, 255, 255, 0)",
                "language": language,
                "theme": "night-owl",
            }
        ),
        headers={"content-type": "application/json"},
        fmt="content",
    )


async def generate_md_table(table: str):
    Silian_lines = table.strip().split("\n")
    if len(Silian_lines) < 2:
        raise ValueError("Invalid Markdown table format.")

    Silian_headers = [Silian_h.strip() for Silian_h in Silian_lines[0].split("|") if Silian_h.strip()]
    Silian_data = []

    for Silian_line in Silian_lines[2:]:
        Silian_row = [Silian_cell.strip() for Silian_cell in Silian_line.split("|") if Silian_cell.strip()]
        if Silian_row:
            Silian_data.append(Silian_row)

    if not Silian_data:
        raise ValueError("No data found in Markdown table.")

    Silian_image_table = ImageTable(data=Silian_data, headers=Silian_headers)
    Silian_imgs = await image_table_render(Silian_image_table)
    if Silian_imgs:
        Silian_img_lst = []
        for Silian_img in Silian_imgs:
            Silian_img_lst.append(Silian_img)
        return Silian_img_lst
    raise RuntimeError("Generation failed.")
