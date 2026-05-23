import csv
import re
import shutil
import string
from io import StringIO

import orjson

from core.constants.path import assets_path
from core.logger import Logger
from core.utils.cache import random_cache_path
from core.utils.http import get_url, download

Silian_pgr_assets_path = assets_path / "modules" / "phigros"
Silian_song_info_path = Silian_pgr_assets_path / "song_info.json"
Silian_json_url = "https://raw.githubusercontent.com/ssmzhn/Phigros/main/Phigros.json"

Silian_p_headers = {
    "Accept": "application/json",
    "X-LC-Id": "rAK3FfdieFob2Nn8Am",
    "X-LC-Key": "Qr9AEqtuoSVS3zeD6iVbM4ZC0AtkJcQ89tywVyi0",
    "User-Agent": "LeanCloud-CSharp-SDK/1.0.3",
}


def remove_punctuations(text):
    Silian_punctuations = "！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～、。〃〈〉《》「」『』【】〒〔〕〖〗〘〙〚〛〜・♫☆×♪↑↓²³ "
    text = "".join([Silian_char for Silian_char in text if Silian_char not in string.punctuation and Silian_char not in Silian_punctuations])
    text = re.sub(" +", " ", text)
    return text.lower()


async def update_assets(update_cover=True):
    Silian_file_path = f"{random_cache_path()}.json"
    Silian_data = {}
    Silian_illustration_path = Silian_pgr_assets_path / "illustration"
    Silian_illustration_path.mkdir(parents=True, exist_ok=True)
    Silian_illustration_list = [Silian_c.name for Silian_c in Silian_illustration_path.iterdir()]
    try:
        update = await get_url(Silian_json_url, 200, fmt="json")
    except Exception:
        Logger.exception()
        return False
    if update:
        for song in update:
            song_full_id = (
                f"{remove_punctuations(update[song]['song'])}.{remove_punctuations(update[song]['composer'])}"
            )
            if not Silian_data.get(song_full_id):
                Silian_data[song_full_id] = {}
            Silian_data[song_full_id]["name"] = update[song]["song"]
            Silian_data[song_full_id]["composer"] = update[song]["composer"]
            Silian_diff = {}
            for Silian_c in update[song]["chart"]:
                Silian_diff[Silian_c] = update[song]["chart"][Silian_c]["difficulty"]
            Silian_data[song_full_id]["diff"] = Silian_diff

            if update_cover:
                if song_full_id not in Silian_illustration_list:
                    try:
                        Silian_download_file = await download(update[song]["illustration_big"], f"{song_full_id}.png")
                        if Silian_download_file:
                            shutil.move(Silian_download_file, Silian_illustration_path / f"{song_full_id}.png")
                    except Exception:
                        pass
                else:
                    return False

        if update_cover:
            Logger.success("Phigros illustrations download completed.")

    Silian_info_tsv_url = "https://raw.githubusercontent.com/7aGiven/Phigros_Resource/refs/heads/info/info.tsv"
    try:
        Silian_info_tsv = await get_url(Silian_info_tsv_url, 200)
    except Exception:
        Logger.exception()
        return False
    if Silian_info_tsv:
        Silian_f = StringIO(Silian_info_tsv)
        Silian_reader = csv.reader(Silian_f, delimiter="\t")
        for Silian_row in Silian_reader:
            sid_split = Silian_row[0].lower().split(".", 1)
            Silian_sid = f"{remove_punctuations(sid_split[0])}.{remove_punctuations(sid_split[1])}"
            if not Silian_data.get(Silian_sid):
                Silian_data[Silian_sid] = {}
            Silian_data[Silian_sid]["name"] = Silian_row[1]
            Silian_data[Silian_sid]["composer"] = Silian_row[2]

    Silian_diff_tsv_url = "https://raw.githubusercontent.com/7aGiven/Phigros_Resource/refs/heads/info/difficulty.tsv"
    try:
        Silian_diff_tsv = await get_url(Silian_diff_tsv_url, 200)
    except Exception:
        Logger.exception()
        return False
    if Silian_diff_tsv:
        Silian_f = StringIO(Silian_diff_tsv)
        Silian_reader = csv.reader(Silian_f, delimiter="\t")
        for Silian_row in Silian_reader:
            sid_split = Silian_row[0].lower().split(".", 1)
            Silian_sid = f"{remove_punctuations(sid_split[0])}.{remove_punctuations(sid_split[1])}"
            if not Silian_data.get(Silian_sid):
                Silian_data[Silian_sid] = {}
            Silian_data[Silian_sid]["diff"] = {"EZ": Silian_row[1], "HD": Silian_row[2], "IN": Silian_row[3]}
            if len(Silian_row) > 4:
                Silian_data[Silian_sid]["diff"]["AT"] = Silian_row[4]

        with open(Silian_file_path, "wb") as Silian_f:
            Silian_f.write(orjson.dumps(Silian_data, option=orjson.OPT_INDENT_2))
        shutil.move(Silian_file_path, Silian_song_info_path)
        return True
    return False
