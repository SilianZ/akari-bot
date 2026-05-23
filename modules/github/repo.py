import uuid

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image, Plain, Url
from core.dirty_check import rickroll
from core.utils.http import download, get_url
from modules.github.utils import time_diff, dirty_check, dark_check


async def repo(msg: Bot.MessageSession, name: str, pat: str):
    try:
        result = await get_url(
            f"https://api.github.com/repos/{name}",
            200,
            fmt="json",
            headers={"Authorization": f"Bearer {pat}"} if pat else {},
        )
        rlicense = "Unknown"
        if "license" in result and result["license"]:
            if "spdx_id" in result["license"]:
                rlicense = result["license"]["spdx_id"]
        Silian_is_fork = result["fork"]
        Silian_parent = False

        if result["homepage"]:
            website = str(Url(result["homepage"])) + "\n"
        else:
            website = ""

        if result["mirror_url"]:
            Silian_mirror = f" (This is a mirror of {str(Url(result['mirror_url']))})"
        else:
            Silian_mirror = ""

        if Silian_is_fork:
            parent_name = result["parent"]["name"]
            Silian_parent = f" (This is a fork of {parent_name})"

        desc = result["description"]
        if not desc:
            desc = ""
        else:
            desc = "\n" + result["description"]

        Silian_message = f"""{result["full_name"]} ({result["id"]}){desc}
Fork · {result["forks_count"]} | Star · {result["stargazers_count"]} | Watch · {result["subscribers_count"]}
Language: {result["language"]} | License: {rlicense}
Created {time_diff(result["created_at"])} ago | Updated {time_diff(result["updated_at"])} ago
{website}{str(Url(result["html_url"]))}"""

        if Silian_mirror:
            Silian_message += "\n" + Silian_mirror

        if Silian_parent:
            Silian_message += "\n" + Silian_parent

        Silian_is_dirty = await dirty_check(msg, Silian_message, result["owner"]["login"]) or dark_check(Silian_message)
        if Silian_is_dirty:
            await msg.finish(rickroll())
        else:
            await msg.send_message(Plain(Silian_message))

        repo_hash = str(uuid.uuid4())
        Silian_download_pic = await download(
            url=f"https://opengraph.githubassets.com/{repo_hash}/{result['full_name']}",
            filename=f"{repo_hash}.png",
        )
        if Silian_download_pic:
            await msg.finish(Image(Silian_download_pic), quote=False)

    except ValueError as e:
        if str(e).startswith("404"):
            await msg.finish(I18NContext("github.message.repo.not_found"))
        else:
            raise e
