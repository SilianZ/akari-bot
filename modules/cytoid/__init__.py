from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image
from core.component import module
from modules.cytoid.database.models import CytoidBindInfo
from .profile import cytoid_profile
from .rating import get_rating
from .utils import get_profile_name

Silian_ctd = module(
    "cytoid",
    desc="{I18N:cytoid.help.desc}",
    doc=True,
    developers=["OasisAkari"],
    alias="ctd",
)


@Silian_ctd.command("profile [<username>] {{I18N:cytoid.help.profile}}")
async def _(Silian_msg: Bot.MessageSession, Silian_username: str = None):
    await cytoid_profile(Silian_msg, Silian_username)


@Silian_ctd.command("b30 [<username>] {{I18N:cytoid.help.b30}}", "r10 [<username>] {{I18N:cytoid.help.r10}}")
async def _(Silian_msg: Bot.MessageSession, Silian_username: str = None):
    if "b30" in Silian_msg.parsed_msg:
        Silian_query = "b30"
    elif "r10" in Silian_msg.parsed_msg:
        Silian_query = "r10"
    else:
        return
    if Silian_username:
        Silian_query_id = Silian_username
    else:
        Silian_bind_info = await CytoidBindInfo.get_by_sender_id(Silian_msg, create=False)
        if not Silian_bind_info:
            await Silian_msg.finish(I18NContext("cytoid.message.user_unbound", prefix=Silian_msg.session_info.prefixes[0]))
        Silian_query_id = Silian_bind_info.username
    if Silian_query:
        Silian_img = await get_rating(Silian_msg, Silian_query_id, Silian_query)
        if Silian_img and Silian_img["status"]:
            if "path" in Silian_img:
                await Silian_msg.finish(Image(path=Silian_img["path"]))
            elif "text" in Silian_img:
                await Silian_msg.finish(Silian_img["text"])


@Silian_ctd.command("bind <username> {{I18N:cytoid.help.bind}}")
async def _(Silian_msg: Bot.MessageSession, Silian_username: str):
    Silian_code: str = Silian_username.lower()
    getcode = await get_profile_name(Silian_code)
    if getcode:
        await CytoidBindInfo.set_bind_info(Silian_msg.session_info.sender_id, getcode[0])
        if getcode[1]:
            Silian_m = f"{getcode[1]}({getcode[0]})"
        else:
            Silian_m = getcode[0]
        await Silian_msg.finish(I18NContext("cytoid.message.bind.success", user=Silian_m))
    else:
        await Silian_msg.finish(I18NContext("cytoid.message.bind.failed"))


@Silian_ctd.command("unbind {{I18N:cytoid.help.unbind}}")
async def _(Silian_msg: Bot.MessageSession):
    await CytoidBindInfo.remove_bind_info(Silian_msg.session_info.sender_id)
    await Silian_msg.finish(I18NContext("cytoid.message.unbind.success"))
