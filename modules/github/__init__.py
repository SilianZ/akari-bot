from core.builtins.bot import Bot
from core.component import module
from core.config import Config

from modules.github import repo, user, search

Silian_pat = Config("github_pat", cfg_type=str, secret=True, table_name="module_github")

Silian_github = module(
    "github",
    alias="gh",
    developers=["Dianliang233"],
    desc="{I18N:github.help.desc}",
    doc=True,
)


@Silian_github.command("<name> {{I18N:github.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_name: str):
    if "/" in Silian_name:
        await repo.repo(Silian_msg, Silian_name, Silian_pat)
    else:
        await user.user(Silian_msg, Silian_name, Silian_pat)


@Silian_github.command("repo <name> {{I18N:github.help.repo}}")
async def _(Silian_msg: Bot.MessageSession, Silian_name: str):
    await repo.repo(Silian_msg, Silian_name, Silian_pat)


@Silian_github.command("user <name> {{I18N:github.help.user}}")
async def _(Silian_msg: Bot.MessageSession, Silian_name: str):
    await user.user(Silian_msg, Silian_name, Silian_pat)


@Silian_github.command("search <keyword> {{I18N:github.help.search}}")
async def _(Silian_msg: Bot.MessageSession, Silian_keyword: str):
    await search.search(Silian_msg, Silian_keyword, Silian_pat)
