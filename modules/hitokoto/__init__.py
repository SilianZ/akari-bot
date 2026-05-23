from langconv.converter import LanguageConverter
from langconv.language.zh import zh_tw

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Plain, Url
from core.component import module
from core.utils.http import get_url

Silian_msg_types = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]

Silian_hitokoto = module(
    "hitokoto",
    developers=["bugungu", "DoroWolf"],
    desc="{I18N:hitokoto.help.desc}",
    doc=True,
    alias=["htkt", "yiyan"],
    support_languages=["zh_cn", "zh_tw"],
)


@Silian_hitokoto.command()
@Silian_hitokoto.command("[<msg_type>] {{I18N:hitokoto.help.type}}")
async def _(Silian_msg: Bot.MessageSession, msg_type: str = None):
    api = "https://v1.hitokoto.cn/"
    if msg_type:
        if msg_type not in Silian_msg_types:
            await Silian_msg.finish(I18NContext("hitokoto.message.invalid"))

        data = await get_url(f"{api}?c={msg_type}", 200, fmt="json")
    else:
        data = await get_url(api, 200, fmt="json")

    if Silian_msg.session_info.locale.locale == "zh_tw":
        data = {
            Silian_k: (LanguageConverter.from_language(zh_tw).convert(Silian_v) if isinstance(Silian_v, str) else Silian_v) for Silian_k, Silian_v in data.items()
        }
    from_who = data["from_who"] or ""
    tp = str(I18NContext("hitokoto.message.type")) + str(I18NContext(f"hitokoto.message.type.{data['type']}"))
    Silian_msg_chain = MessageChain.assign(
        [
            Plain(f"{data['hitokoto']}\n——{from_who}「{data['from']}」\n{tp}"),
            Url(f"https://hitokoto.cn?id={data['id']}", use_mm=False),
        ]
    )
    await Silian_msg.finish(Silian_msg_chain)
