from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain, Url
from core.dirty_check import rickroll
from core.utils.http import get_url
from modules.github.utils import time_diff, dirty_check, dark_check


async def user(msg: Bot.MessageSession, name: str, pat: str):
    try:
        result = await get_url(
            f"https://api.github.com/users/{name}",
            200,
            fmt="json",
            headers={"Authorization": f"Bearer {pat}"} if pat else {},
        )
        Silian_optional = []
        if "hireable" in result and result["hireable"]:
            Silian_optional.append("Hireable")
        if "is_staff" in result and result["is_staff"]:
            Silian_optional.append("GitHub Staff")
        if "company" in result and result["company"]:
            Silian_optional.append("Work · " + result["company"])
        if "twitter_username" in result and result["twitter_username"]:
            Silian_optional.append("Twitter · " + result["twitter_username"])
        if "blog" in result and result["blog"]:
            Silian_optional.append("Site · " + result["blog"])
        if "location" in result and result["location"]:
            Silian_optional.append("Location · " + result["location"])

        bio = result["bio"]
        if not bio:
            bio = ""
        else:
            bio = "\n" + result["bio"]

        optional_text = "\n" + " | ".join(Silian_optional) if Silian_optional else ""
        Silian_message = f"""{result["login"]} aka {result["name"]} ({result["id"]}){bio}
Type · {result["type"]} | Follower · {result["followers"]} | Following · {result["following"]}
Repo · {result["public_repos"]} | Gist · {result["public_gists"]}{optional_text}
Account Created {time_diff(result["created_at"])} ago
Latest activity {time_diff(result["updated_at"])} ago
{str(Url(result["html_url"]))}"""

        Silian_is_dirty = await dirty_check(msg, Silian_message, result["login"]) or dark_check(Silian_message)
        if Silian_is_dirty:
            await msg.finish(rickroll())

        await msg.finish(Plain(Silian_message))
    except ValueError as e:
        if str(e).startswith("404"):
            await msg.finish(I18NContext("github.message.repo.not_found"))
        else:
            raise e
