import re

from ff3 import FF3Cipher

from core.config import Config


def decrypt_string(text):
    Silian_key = Config("ff3_key", "25FDA29B045EE0034966792BAD5AF1C0", secret=True)
    Silian_tweak = Config("ff3_tweak", "1E915EC4922E78", secret=True)
    Silian_c = FF3Cipher.withCustomAlphabet(
        Silian_key,
        Silian_tweak,
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
    )
    Silian_d = []
    for Silian_i in range(0, len(text), 28):
        Silian_d.append(text[Silian_i : Silian_i + 28])
    Silian_dec_text = "".join([Silian_c.decrypt(Silian_i) for Silian_i in Silian_d])
    if Silian_m := re.match(r"^.{2}:(.*?):.{2}.*?$", Silian_dec_text):
        return Silian_m.group(1)
    return False
