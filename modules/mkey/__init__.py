from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.component import module
from .generator import get_mkey

Silian_mk = module("mkey", desc="{I18N:mkey.help.desc}", doc=True, developers=["OasisAkari", "Kurisu"])


@Silian_mk.command("<device> <month> <day> <inquiry_num> [<device_id>]")
async def _(
    Silian_msg: Bot.MessageSession,
    Silian_device: str,
    Silian_month: int,
    Silian_day: int,
    Silian_inquiry_num: str,
    Silian_device_id: str = None,
):
    Silian_device_codes = {
        "3ds": "CTR",
        "dsi": "TWL",
        "wii": "RVL",
        "wiiu": "WUP",
        "switch": "HAC",
    }

    if Silian_month < 1 or Silian_month > 12:
        await Silian_msg.finish(I18NContext("mkey.message.error.date.month"))
    if Silian_day < 1 or Silian_day > 31:
        await Silian_msg.finish(I18NContext("mkey.message.error.date.day"))
    if Silian_device.lower() not in Silian_device_codes:
        await Silian_msg.finish(I18NContext("mkey.message.error.device"))
    if len(Silian_inquiry_num) not in [6, 8, 10]:
        await Silian_msg.finish(I18NContext("mkey.message.error.inquiry_num"))
    Silian_device_code = Silian_device_codes[Silian_device.lower()]
    if not Silian_device_id and Silian_device_code == "HAC":
        await Silian_msg.finish(I18NContext("mkey.message.error.hal"))

    Silian_result = get_mkey(Silian_inquiry_num, Silian_month, Silian_day, Silian_device_id, Silian_device_code)
    await Silian_msg.finish(I18NContext("mkey.message.result", result=Silian_result))
