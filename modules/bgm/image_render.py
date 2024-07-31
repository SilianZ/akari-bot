from core.utils.image_table import image_table_render, ImageTable
from typing import List, Union
import re
from tabulate import tabulate
from html import unescape
from config import CFG
from core.logger import Logger
import aiohttp
import ujson as json
from core.utils.cache import random_cache_path
from core.utils.http import download_to_cache

web_render = CFG.get_url('web_render')
web_render_local = CFG.get_url('web_render_local')

async def image_table_render(table: Union[ImageTable, List[ImageTable]], save_source=True, use_local=True):
    if not web_render_local:
        if not web_render:
            Logger.warn('[Webrender] Webrender is not configured.')
            return False
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
                    cs.append(c)
                d.append(cs)
            w = len(tbl.headers) * 10000
            if w > max_width:
                max_width = w
            tblst.append(re.sub(r'<table>|</table>', '', tabulate(d, tbl.headers, tablefmt='html')))
        tblst = unescape('<table>' + '\n'.join(tblst) + '</table>')
        css =  """
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
              text-align: center;
            }</style>"""
        html = {'content': tblst + css, 'width': w, 'mw': False}
        if save_source:
            fname = random_cache_path() + '.html'
            with open(fname, 'w', encoding='utf-8') as fi:
                fi.write(tblst + css)

        try:
            pic = await download_to_cache(
                web_render_local if use_local else web_render,
                method='POST',
                post_data=json.dumps(html),
                timeout=360,
                request_private_ip=True,
                headers={
                    'Content-Type': 'application/json',
                }
            )
        except aiohttp.ClientConnectorError:
            if use_local:
                pic = await download_to_cache(
                    web_render,
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