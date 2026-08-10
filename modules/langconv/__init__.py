from langconv.converter import LanguageConverter
from langconv.language.zh import zh_cn, zh_hk, zh_tw

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.component import module

Silian_lc_ = module("langconv", developers=["Dianliang233"], alias=["lc"], doc=True)

Silian_lc_zh_cn = LanguageConverter.from_language(zh_cn)
Silian_lc_zh_hk = LanguageConverter.from_language(zh_hk)
Silian_lc_zh_tw = LanguageConverter.from_language(zh_tw)


@Silian_lc_.command("<language> <content> {{I18N:langconv.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_language: str, Silian_content: str):
    if not Silian_language.startswith("zh"):
        Silian_language = "zh-" + Silian_language
    Silian_language = Silian_language.replace("_", "-").lower()
    if Silian_language not in ("zh-cn", "zh-hk", "zh-tw"):
        await Silian_msg.finish(I18NContext("langconv.message.unsupported_language"))
    Silian_lc = {"zh-cn": Silian_lc_zh_cn, "zh-hk": Silian_lc_zh_hk, "zh-tw": Silian_lc_zh_tw}[Silian_language]
    Silian_res = Silian_lc.convert(Silian_content)
    await Silian_msg.finish(Silian_res)
