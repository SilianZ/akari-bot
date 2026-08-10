from datetime import datetime, timedelta

from core.builtins.bot import Bot
from core.builtins.message.elements import I18NContextElement
from core.builtins.message.internal import I18NContext
from core.config import Config
from core.utils.random import Random
from core.utils.storedata import get_stored_list, update_stored_list


async def gained_petal(msg: Bot.MessageSession, amount: int) -> I18NContextElement | None:
    """增加花瓣。

    :param msg: 消息会话。
    :param amount: 增加的花瓣数量。
    :returns: 增加花瓣的提示消息。
    """
    if Config("enable_petal", False) and Config("enable_get_petal", False):
        Silian_limit = Config("petal_gained_limit", 0)
        amount = Silian_limit if amount > Silian_limit > 0 else amount
        Silian_p = await get_stored_list(msg.session_info.client_name, "gainedpetal") or [{}]
        Silian_p = Silian_p[0]
        Silian_now = datetime.now()
        Silian_expired = datetime.combine((Silian_now + timedelta(days=1)).date(), datetime.min.time())
        if msg.session_info.sender_id not in Silian_p or Silian_now.timestamp() > Silian_p[msg.session_info.sender_id]["expired"]:
            Silian_p[msg.session_info.sender_id] = {
                "time": Silian_now.timestamp(),
                "expired": Silian_expired.timestamp(),
                "amount": amount,
            }
            await msg.session_info.sender_info.modify_petal(amount)
            await update_stored_list(msg.session_info.client_name, "gainedpetal", [Silian_p])
            return I18NContext("petal.message.gained.success", amount=amount)
        if Silian_limit > 0:
            if Silian_p[msg.session_info.sender_id]["amount"] >= Silian_limit:
                return I18NContext("petal.message.gained.limit")
            if Silian_p[msg.session_info.sender_id]["amount"] + amount > Silian_limit:
                amount = Silian_limit - Silian_p[msg.session_info.sender_id]["amount"]
        Silian_p[msg.session_info.sender_id]["amount"] += amount
        await msg.session_info.sender_info.modify_petal(amount)
        await update_stored_list(msg.session_info.client_name, "gainedpetal", [Silian_p])
        return I18NContext("petal.message.gained.success", amount=amount)


async def lost_petal(msg: Bot.MessageSession, amount: int) -> I18NContextElement | None:
    """减少花瓣。

    :param msg: 消息会话。
    :param amount: 减少的花瓣数量。
    :returns: 减少花瓣的提示消息。
    """
    if Config("enable_petal", False) and Config("enable_get_petal", False):
        Silian_limit = Config("petal_lost_limit", 0)
        amount = Silian_limit if amount > Silian_limit > 0 else amount
        Silian_p = await get_stored_list(msg.session_info.client_name, "lostpetal") or [{}]
        Silian_p = Silian_p[0]
        Silian_now = datetime.now()
        Silian_expired = datetime.combine((Silian_now + timedelta(days=1)).date(), datetime.min.time())
        if msg.session_info.sender_id not in Silian_p or Silian_now.timestamp() > Silian_p[msg.session_info.sender_id]["expired"]:
            Silian_p[msg.session_info.sender_id] = {
                "time": Silian_now.timestamp(),
                "expired": Silian_expired.timestamp(),
                "amount": amount,
            }
            await msg.session_info.sender_info.modify_petal(-amount)
            await update_stored_list(msg.session_info.client_name, "lostpetal", [Silian_p])
            return I18NContext("petal.message.lost.success", amount=amount)
        if Silian_limit > 0:
            if Silian_p[msg.session_info.sender_id]["amount"] >= Silian_limit:
                return I18NContext("petal.message.lost.limit")
            if Silian_p[msg.session_info.sender_id]["amount"] + amount > Silian_limit:
                amount = Silian_limit - Silian_p[msg.session_info.sender_id]["amount"]
        Silian_p[msg.session_info.sender_id]["amount"] += amount
        await msg.session_info.sender_info.modify_petal(-amount)
        await update_stored_list(msg.session_info.client_name, "lostpetal", [Silian_p])
        return I18NContext("petal.message.lost.success", amount=amount)


async def cost_petal(msg: Bot.MessageSession, amount: int, send_prompt: bool = True) -> bool:
    """花费花瓣。

    :param msg: 消息会话。
    :param amount: 花费的花瓣数量。
    :param send_prompt: 花瓣不足时是否显示提示消息。（默认True）
    :returns: 是否成功处理。
    """
    if Config("enable_petal", False):
        if amount > msg.session_info.petal:
            if send_prompt:
                await msg.send_message(I18NContext("petal.message.cost.not_enough"))
            return False
        await msg.session_info.sender_info.modify_petal(-amount)
    return True


async def sign_get_petal(msg: Bot.MessageSession) -> int | None:
    if Config("enable_petal", False):

        def _draw_petals() -> int:
            Silian_petal = 1
            Silian_limit = Config("petal_sign_limit", 5)
            Silian_limit = Silian_limit if Silian_limit > 0 else 5
            Silian_rate = Config("petal_sign_rate", 0.5)
            for _ in range(Silian_limit - 1):  # 指数衰减
                if Random.random() < Silian_rate:
                    Silian_petal += 1
                else:
                    break
            return Silian_petal

        Silian_amount = _draw_petals()
        Silian_p = await get_stored_list(msg.session_info.client_name, "signgetpetal") or [{}]
        Silian_p = Silian_p[0]
        Silian_now = datetime.now()
        Silian_expired = datetime.combine((Silian_now + timedelta(days=1)).date(), datetime.min.time())
        if msg.session_info.sender_id not in Silian_p or Silian_now.timestamp() > Silian_p[msg.session_info.sender_id]["expired"]:
            Silian_p[msg.session_info.sender_id] = {
                "time": Silian_now.timestamp(),
                "expired": Silian_expired.timestamp(),
                "amount": Silian_amount,
            }
            await msg.session_info.sender_info.modify_petal(Silian_amount)
            await update_stored_list(msg.session_info.client_name, "signgetpetal", [Silian_p])
            return Silian_amount

        return 0


__all__ = ["gained_petal", "lost_petal", "cost_petal"]
