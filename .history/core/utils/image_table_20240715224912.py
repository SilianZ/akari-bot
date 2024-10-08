import re
from html import escape
from typing import List, Union

import aiohttp
import ujson as json
from tabulate import tabulate

from core.builtins.utils import shuffle_joke
from core.logger import Logger
from .cache import random_cache_path
from .http import download
from .web_render import WebRender, webrender


class ImageTable:
    def __init__(self, data, headers):
        self.data = data
        self.headers = headers


async def image_table_render(table: Union[ImageTable, List[ImageTable]], save_source=True, use_local=True):
    if not WebRender.status:
        return False
    elif not WebRender.local:
        use_local = False
    pic = False

    try:
        tblst = []
        if isinstance(table, ImageTable):
            table = [table]
        max_width = 500
        for tbl in table:
            d = []
            for row in tbl.data:
                cs = []
                for c in row:
                    c = shuffle_joke(c)
                    cs.append(re.sub(r'\n', '<br>', escape(c)))
                d.append(cs)
            headers = [shuffle_joke(header) for header in tbl.headers]
            w = len(headers) * 500
            if w > max_width:
                max_width = w
            tblst.append(re.sub(r'<table>|</table>', '', tabulate(d, headers, tablefmt='unsafehtml')))
        tblst = '<table>' + '\n'.join(tblst) + '</table>'
        css = """
        <style>table {
                border-collapse: collapse;
              }
              table, th, td {
                border: 1px solid rgba(0,0,0,0.05);
                font-size: 2rem;
                font-family: Consolas, Microsoft Yahei;
                font-weight: 500;
              }
              th, td {
              padding: 30px;
              text-align: left;
            }</style>"""
        html = {'content': tblst + css, 'width': w, 'mw': False}
        if save_source:
            fname = random_cache_path() + '.html'
            with open(fname, 'w', encoding='utf-8') as fi:
                fi.write(tblst + css)

        try:
            pic = await download(
                webrender(use_local=use_local),
                method='POST',
                post_data=json.dumps(html),
                request_private_ip=True,
                timeout=90,
                headers={
                    'Content-Type': 'application/json',
                }
            )
        except aiohttp.ClientConnectorError:
            if use_local:
                pic = await download(
                    webrender(use_local=False),
                    method='POST',
                    post_data=json.dumps(html),
                    request_private_ip=True,
                    headers={
                        'Content-Type': 'application/json',
                    }
                )
    except Exception:
        Logger.exception("Error at image_table_render.")

    return pic


__all__ = ['ImageTable', 'image_table_render']
