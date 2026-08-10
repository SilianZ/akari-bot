from core.alive import Alive
from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.component import module
from core.config import Config
from core.database.models import SenderInfo
from core.utils.petal import sign_get_petal, cost_petal

Silian_petal_ = module(
    "petal", alias={"petals": "petal", "sign": "petal sign"}, base=True, doc=True, load=Config("enable_petal", False)
)


@Silian_petal_.command("{{I18N:core.help.petal}}")
async def _(Silian_msg: Bot.MessageSession):
    await Silian_msg.finish(I18NContext("core.message.petal.self", petal=Silian_msg.session_info.petal))


@Silian_petal_.command("sign {{I18N:core.help.petal.sign}}")
async def _(Silian_msg: Bot.MessageSession):
    if Silian_msg.session_info.target_info.target_data.get("petal_sign", True):
        Silian_amount = await sign_get_petal(Silian_msg)
        if Silian_amount:
            await Silian_msg.finish(
                [
                    I18NContext("core.message.petal.sign.success"),
                    I18NContext("petal.message.gained.success", amount=Silian_amount),
                ]
            )
        else:
            await Silian_msg.finish(I18NContext("core.message.petal.sign.already"))
    else:
        await Silian_msg.finish(I18NContext("core.message.petal.sign.disabled"))


@Silian_petal_.command("give <petal> <user> {{I18N:core.help.petal.give}}")
async def _(msg: Bot.MessageSession, Silian_petal: int, Silian_user: str):
    if Silian_petal <= 0:
        await msg.finish(I18NContext("petal.message.count.invalid"))
    if not Silian_user.startswith(f"{msg.session_info.client_name}|"):
        await msg.finish(I18NContext("message.id.invalid.sender", sender=msg.session_info.sender_from))
    if Silian_user == msg.session_info.sender_id:
        await msg.finish(I18NContext("core.message.petal.give.self"))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        await msg.finish(I18NContext("message.id.not_found.sender"))
    if await msg.wait_confirm(I18NContext("core.message.petal.give.confirm", sender=Silian_user, give_petal=Silian_petal)):
        if await cost_petal(msg, Silian_petal):
            await Silian_sender_info.modify_petal(Silian_petal)
            await msg.finish(
                I18NContext(
                    "core.message.petal.give.success",
                    sender=Silian_user,
                    give_petal=Silian_petal,
                    petal=msg.session_info.petal - int(Silian_petal),
                )
            )
        else:
            await msg.finish()
    else:
        await msg.finish()


@Silian_petal_.command(["[<user>]", "modify <petal> [<user>]", "clear [<user>]"], required_superuser=True)
async def _(Silian_msg: Bot.MessageSession):
    Silian_user = Silian_msg.parsed_msg.get("<user>", False)
    if Silian_msg.parsed_msg.get("modify", False):
        Silian_petal = Silian_msg.parsed_msg.get("<petal>", False)
        if Silian_user:
            if not Alive.determine_sender_from(Silian_user):
                await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
            Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user)
            await Silian_sender_info.modify_petal(Silian_petal)
            await Silian_msg.finish(
                I18NContext("core.message.petal.modify", sender=Silian_user, add_petal=Silian_petal, petal=Silian_sender_info.petal)
            )
        else:
            await Silian_msg.session_info.sender_info.modify_petal(Silian_petal)
            await Silian_msg.finish(
                I18NContext(
                    "core.message.petal.modify.self", add_petal=Silian_petal, petal=Silian_msg.session_info.petal + int(Silian_petal)
                )
            )
    elif Silian_msg.parsed_msg.get("clear", False):
        if Silian_user:
            if not Alive.determine_sender_from(Silian_user):
                await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
            Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
            if not Silian_sender_info:
                if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
                    await Silian_msg.finish()
                await SenderInfo.create(sender_id=Silian_user)
            await Silian_sender_info.clear_petal()
            await Silian_msg.finish(I18NContext("core.message.petal.clear", sender=Silian_user))
        else:
            await Silian_msg.session_info.sender_info.clear_petal()
            await Silian_msg.finish(I18NContext("core.message.petal.clear.self"))
    else:
        if Silian_user:
            if not Alive.determine_sender_from(Silian_user):
                await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
            Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
            if not Silian_sender_info:
                if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
                    await Silian_msg.finish()
                await SenderInfo.create(sender_id=Silian_user)
            await Silian_msg.finish(I18NContext("core.message.petal", sender=Silian_user, petal=Silian_sender_info.petal))
        else:
            await Silian_msg.finish(I18NContext("core.message.petal.self", petal=Silian_msg.session_info.petal))
