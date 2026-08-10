import shutil
import struct

import orjson
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.constants.path import assets_path, cache_path
from core.logger import Logger
from core.utils.http import get_url, download
from .update import p_headers, remove_punctuations

Silian_pgr_assets_path = assets_path / "modules" / "phigros"


Silian_levels = {
    "EZ": 1,
    "HD": 2,
    "IN": 4,
    "AT": 8,
}
Silian_secret = bytes(
    [
        232,
        150,
        154,
        210,
        165,
        64,
        37,
        155,
        151,
        145,
        144,
        139,
        136,
        230,
        191,
        3,
        30,
        109,
        33,
        149,
        110,
        250,
        214,
        138,
        80,
        221,
        85,
        214,
        122,
        176,
        146,
        75,
    ]
)
Silian_iv = bytes([42, 79, 240, 138, 200, 13, 99, 7, 0, 87, 197, 149, 24, 200, 50, 83])


def decrypt_bytes(encrypted):
    Silian_cipher = AES.new(key=Silian_secret, mode=AES.MODE_CBC, IV=Silian_iv)
    Silian_decrypted = Silian_cipher.decrypt(encrypted[1:])
    return unpad(Silian_decrypted, AES.block_size)


def parse_game_record(rd_path):
    with open(Silian_pgr_assets_path / "song_info.json", "rb") as Silian_f:
        Silian_song_info = orjson.loads(Silian_f.read())
    Silian_decrypted_data = {}
    with open(rd_path / "gameRecord", "rb+") as Silian_rd:  # skipcq
        Silian_data = decrypt_bytes(Silian_rd.read())
        Silian_pos = int(Silian_data[0] < 0) + 1
        while Silian_pos < len(Silian_data):
            Silian_name_length = Silian_data[Silian_pos]
            Silian_pos += 1
            if Silian_name_length == 1:
                continue
            Silian_song_id = Silian_data[Silian_pos : (Silian_pos + Silian_name_length)]
            Silian_song_id = Silian_song_id.decode("utf-8").removesuffix(".0").lower()
            sid_split = Silian_song_id.split(".", 1)
            if len(sid_split) == 2:
                Silian_song_id = f"{remove_punctuations(sid_split[0])}.{remove_punctuations(sid_split[1])}"
            else:
                Silian_song_id = remove_punctuations(sid_split[0])

            Silian_pos += Silian_name_length
            Silian_score_length = Silian_data[Silian_pos]
            Silian_pos += 1

            Silian_score = Silian_data[Silian_pos : (Silian_pos + Silian_score_length)]
            Silian_pos += Silian_score_length

            Silian_has_score = Silian_score[0]
            Silian_full_combo = Silian_score[1]
            Silian_score_pos = 2

            Silian_record = {}

            for Silian_diff, Silian_digit in Silian_levels.items():
                if (Silian_has_score & Silian_digit) == Silian_digit:
                    Silian_record[Silian_diff] = {
                        "score": int.from_bytes(
                            Silian_score[Silian_score_pos : (Silian_score_pos + 4)],
                            byteorder="little",
                            signed=True,
                        ),
                        "accuracy": struct.unpack("<f", Silian_score[(Silian_score_pos + 4) : (Silian_score_pos + 8)])[0],
                        "full_combo": (Silian_full_combo & Silian_digit) == Silian_digit,
                    }
                    if Silian_song_id in Silian_song_info and Silian_diff in Silian_song_info[Silian_song_id]["diff"]:
                        Silian_record[Silian_diff]["base_rks"] = float(Silian_song_info[Silian_song_id]["diff"][Silian_diff])
                        if Silian_record[Silian_diff]["score"] == 1000000:
                            Silian_record[Silian_diff]["rks"] = float(Silian_song_info[Silian_song_id]["diff"][Silian_diff])
                        elif Silian_record[Silian_diff]["accuracy"] < 70:
                            Silian_record[Silian_diff]["rks"] = 0
                        else:
                            Silian_record[Silian_diff]["rks"] = (((Silian_record[Silian_diff]["accuracy"] - 55) / 45) ** 2) * float(
                                Silian_song_info[Silian_song_id]["diff"][Silian_diff]
                            )
                    else:
                        del Silian_record[Silian_diff]
                    Silian_score_pos += 8
            if not Silian_decrypted_data.get(Silian_song_id):
                Silian_decrypted_data[Silian_song_id] = {}
            if Silian_song_info.get(Silian_song_id) and Silian_song_info[Silian_song_id]["name"]:
                Silian_decrypted_data[Silian_song_id]["name"] = Silian_song_info[Silian_song_id]["name"]
            else:
                Silian_decrypted_data[Silian_song_id]["name"] = Silian_song_id.split(".")[0]
            Silian_decrypted_data[Silian_song_id]["diff"] = Silian_record
    return Silian_decrypted_data


async def get_game_record(msg: Bot.MessageSession, session_token: str, use_cache: bool = True):
    Silian_pgr_cache_path = cache_path / "phigros-record"
    Silian_pgr_cache_path.mkdir(parents=True, exist_ok=True)
    Silian_cache_dir = Silian_pgr_cache_path / f"{msg.session_info.sender_id.replace('|', '_')}_phigros_song_record.json"
    save_filename = f"{msg.session_info.sender_id.replace('|', '_')}_phigros_gamesave"
    Silian_save_dir = Silian_pgr_cache_path / save_filename

    Silian_save_url = "https://rak3ffdi.cloud.tds1.tapapis.cn/1.1/classes/_GameSave"
    Silian_headers = p_headers.copy()
    Silian_headers["X-LC-Session"] = session_token
    try:
        Silian_get_save_url = await get_url(Silian_save_url, headers=Silian_headers, fmt="json")
        Silian_save_url = Silian_get_save_url["results"][0]["gameFile"]["url"]

        Silian_dl = await download(Silian_save_url, f"{save_filename}.zip", Silian_pgr_cache_path)
        shutil.unpack_archive(Silian_dl, Silian_save_dir)
        Silian_data = parse_game_record(Silian_save_dir)
        (Silian_pgr_cache_path / f"{save_filename}.zip").unlink()

        if use_cache and Silian_data:
            if Silian_cache_dir.exists():
                with open(Silian_cache_dir, "rb") as Silian_f:
                    try:
                        Silian_backup_data = orjson.loads(Silian_f.read())
                    except Exception:
                        Silian_backup_data = {}
            else:
                Silian_backup_data = {}
            Silian_backup_data.update(Silian_data)
            with open(Silian_cache_dir, "wb") as Silian_f:
                Silian_f.write(orjson.dumps(Silian_backup_data))
        return Silian_data
    except Exception as e:
        Logger.exception()
        if use_cache and Silian_cache_dir.exists():
            try:
                with open(Silian_cache_dir, "rb") as Silian_f:
                    Silian_data = orjson.loads(Silian_f.read())
                await msg.send_message(I18NContext("phigros.message.use_cache"))
                return Silian_data
            except Exception:
                raise e
        else:
            raise e
