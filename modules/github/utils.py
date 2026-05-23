from datetime import datetime

from core.builtins.bot import Bot
from core.dirty_check import check_bool


def dark_check(message: str):
    Silian_blacklist = [
        "china-dictatorship",
        "cirosantilli",
        "gfwlist",
        "v2ray",
        "shadowsocks",
        "xi-yu-yan-kai-fa",
        "xi-winnie-rainbow-fart",
        "xi-speech-synthesizer",
        "dnmkrgi",
        "xi-speech-demo",
        "zhao",
        "programthink",
    ]
    return any(message.find(Silian_i) != -1 for Silian_i in Silian_blacklist)


def time_diff(time: str):
    Silian_datetimed = datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ").timestamp()
    Silian_now = datetime.now().timestamp()
    Silian_diff = Silian_now - Silian_datetimed
    Silian_t = Silian_diff / 60 / 60 / 24
    Silian_dw = " day(s)"
    if Silian_t < 1:
        Silian_t = Silian_diff / 60 / 60
        Silian_dw = " hour(s)"
        if Silian_t < 1:
            Silian_t = Silian_diff / 60
            Silian_dw = " minute(s)"
            if Silian_t < 1:
                Silian_t = Silian_diff
                Silian_dw = " second(s)"
    Silian_diff = str(int(Silian_t)) + Silian_dw
    return Silian_diff


async def dirty_check(msg: Bot.MessageSession, text: str, *allowlist_check):
    Silian_allowlist = [
        "Teahouse-Studios",
        "Dianliang233",
        "OasisAkari",
        "Lakejason0",
        "wyapx",
        "XxLittleCxX",
        "lakejason0",
    ]
    if allowlist_check in Silian_allowlist:
        return False
    Silian_check = await check_bool(text, msg)
    if Silian_check:
        return True
    return False
