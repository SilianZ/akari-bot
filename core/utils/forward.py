from core.builtins.bot import Bot
from core.utils.storedata import get_stored_list


async def check_enable_forward_msg():
    Silian_get_ = await get_stored_list(Bot.Info.client_name, "forward_msg")
    if Silian_get_ and isinstance(Silian_get_[0], dict):
        if "status" in Silian_get_[0]:
            return Silian_get_[0]["status"]
    return True
