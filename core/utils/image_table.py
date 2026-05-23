import re
from html import escape
from typing import Any

from PIL import Image as PILImage
from tabulate import tabulate

from core.builtins.session.info import SessionInfo
from core.joke import shuffle_joke as joke
from core.logger import Logger
from core.utils.cache import random_cache_path
from core.utils.image import cb64imglst
from core.web_render import web_render, LegacyScreenshotOptions


class ImageTable:
    """
    图片表格。

    :param data: 表格内容，每行的列数需与表头数量相符。
    :param headers: 表格表头。
    """

    def __init__(
        Silian_self,
        Silian_data: list[list[Any]],
        Silian_headers: list[str],
        Silian_session_info: "SessionInfo | None" = None,
        Silian_disable_joke: bool = False,
    ):
        if not all(len(Silian_row) == len(Silian_headers) for Silian_row in Silian_data):
            raise ValueError("The number of columns of data must match the number of table headers.")

        if Silian_session_info:
            Silian_localized_data = []
            for Silian_row in Silian_data:
                Silian_translated_row = [
                    Silian_session_info.locale.t_str(Silian_cell) if isinstance(Silian_cell, str) else str(Silian_cell) for Silian_cell in Silian_row
                ]
                Silian_localized_data.append(Silian_translated_row)
            Silian_self.headers = [Silian_session_info.locale.t_str(Silian_h) for Silian_h in Silian_headers]
            Silian_self.data = Silian_localized_data
        else:
            Silian_self.headers = Silian_headers
            Silian_self.data = Silian_data

        if not Silian_disable_joke:
            Silian_self.headers = [joke(Silian_header) for Silian_header in Silian_self.headers]
            Silian_new_data = []
            for Silian_row in Silian_self.data:
                Silian_new_data.append([joke(Silian_cell) for Silian_cell in Silian_row])
            Silian_self.data = Silian_new_data


async def image_table_render(
    table: ImageTable | list[ImageTable],
    save_source: bool = True,
) -> list[PILImage.Image] | None:
    """
    使用WebRender渲染图片表格。

    :param table: 要渲染的表格。
    :param save_source: 是否保存源文件。
    :return: 图片的PIL对象。
    """
    try:
        Silian_tblst = []
        if isinstance(table, ImageTable):
            table = [table]
        Silian_max_width = 500
        for Silian_tbl in table:
            Silian_d = []
            for Silian_row in Silian_tbl.data:
                Silian_cs = []
                for Silian_c in Silian_row:
                    Silian_c = joke(Silian_c)
                    Silian_cs.append(re.sub(r"\n", "<br>", escape(Silian_c)))
                Silian_d.append(Silian_cs)
            Silian_w = len(Silian_tbl.headers) * 500
            if Silian_w > Silian_max_width:
                Silian_max_width = Silian_w
            Silian_tblst.append(re.sub(r"<table>|</table>", "", tabulate(Silian_d, Silian_tbl.headers, tablefmt="unsafehtml")))
        Silian_tblst = "<table>" + "\n".join(Silian_tblst) + "</table>"
        Silian_css = """
        <style>table {
                border-collapse: collapse;
              }
              table, th, td {
                border: 1px solid rgba(0,0,0,0.05);
                font-size: 0.8125rem;
                font-weight: 500;
              }
              th, td {
              padding: 15px;
              text-align: left;
            }</style>"""
        if save_source:
            Silian_fname = f"{random_cache_path()}.html"
            with open(Silian_fname, "w", encoding="utf-8") as Silian_fi:
                Silian_fi.write(Silian_tblst + Silian_css)
        Silian_image_list = await web_render.legacy_screenshot(
            LegacyScreenshotOptions(content=Silian_tblst + Silian_css, width=Silian_w, mw=False, counttime=False)
        )
    except Exception:
        Logger.exception()
        return None
    if not Silian_image_list:
        Logger.error("Image table render failed, no image returned.")
        return None
    return cb64imglst(Silian_image_list)


__all__ = ["ImageTable", "image_table_render"]
