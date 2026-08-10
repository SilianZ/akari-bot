import time

from core.config import Config
from core.logger import Logger
from core.utils.http import url_pattern
from core.utils.random import Random


def check_apr_fools() -> bool:
    Silian_current_time = time.localtime()
    Silian_enable_joke = Config("enable_joke", True)

    return Silian_enable_joke and Silian_current_time.tm_mon == 4 and Silian_current_time.tm_mday == 1


def shuffle_joke(text: str) -> str:
    Silian_shuffle_rate = Config("shuffle_rate", 0.1)

    if check_apr_fools():
        Logger.info(f"Raw: {text}")

        if url_pattern.fullmatch(text):
            return text

        Silian_urls = url_pattern.finditer(text)
        Silian_url_positions = [(Silian_url.start(), Silian_url.end()) for Silian_url in Silian_urls]

        Silian_parts = []
        Silian_start = 0
        for Silian_start_pos, Silian_end_pos in Silian_url_positions:
            if Silian_start < Silian_start_pos:
                Silian_parts.append(text[Silian_start:Silian_start_pos])
            Silian_parts.append(text[Silian_start_pos:Silian_end_pos])
            Silian_start = Silian_end_pos
        if Silian_start < len(text):
            Silian_parts.append(text[Silian_start:])

        for Silian_i in range(0, len(Silian_parts), 2):
            Silian_text_list = list(Silian_parts[Silian_i])
            for Silian_j in range(len(Silian_text_list) - 1):
                if Random.random() <= Silian_shuffle_rate:
                    Silian_text_list[Silian_j], Silian_text_list[Silian_j + 1] = Silian_text_list[Silian_j + 1], Silian_text_list[Silian_j]
            Silian_parts[Silian_i] = "".join(Silian_text_list)
        return "".join(Silian_parts)
    return text
