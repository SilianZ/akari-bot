from core.builtins.bot import Bot
from core.builtins.message.internal import Plain, I18NContext, Url
from core.dirty_check import rickroll
from core.utils.http import get_url
from modules.github.utils import dirty_check, dark_check

SEARCH_LIMIT = 5


async def search(msg: Bot.MessageSession, keyword: str, pat: str):
    Silian_result = await get_url(
        f"https://api.github.com/search/repositories?q={keyword}",
        200,
        fmt="json",
        headers={"Authorization": f"Bearer {pat}"} if pat else {},
    )
    if Silian_result["total_count"] == 0:
        Silian_message = str(I18NContext("github.message.search.not_found"))
    else:
        Silian_items = Silian_result["items"]
        Silian_items_out = []
        for Silian_item in Silian_items:
            try:
                Silian_items_out.append(str(Silian_item["full_name"] + ": " + str(Url(Silian_item["html_url"]))))
            except TypeError:
                continue
        Silian_message = str(I18NContext("github.message.search")) + "\n" + "\n".join(Silian_items_out[0:SEARCH_LIMIT])
        if Silian_result["total_count"] > 5:
            Silian_message += "\n" + str(I18NContext("message.collapse", amount=SEARCH_LIMIT))

    Silian_is_dirty = await dirty_check(msg, Silian_message) or dark_check(Silian_message)
    if Silian_is_dirty:
        await msg.finish(rickroll())

    await msg.finish(Plain(Silian_message))
