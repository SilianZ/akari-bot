from core.builtins import Bot, Image
from core.component import module
from modules.github import repo, user, search
from config import Config
import ujson as json
import aiohttp
from aiofile import async_open
from core.utils.http import download_to_cache
from core.utils.cache import random_cache_path

github = module('github', alias='gh', developers=['Dianliang233'], desc='{github.help.desc}')


@github.command('<name> {{github.help}}')
async def _(msg: Bot.MessageSession, name: str):
    if '/' in name:
        await repo.repo(msg)
    else:
        await user.user(msg)


@github.command('repo <name> {{github.help.repo}}')
async def _(msg: Bot.MessageSession):
    await repo.repo(msg)


@github.command('user <name> {{github.help.user}}')
async def _(msg: Bot.MessageSession):
    await user.user(msg)


@github.command('search <query> {{github.help.search}}')
async def _(msg: Bot.MessageSession):
    await search.search(msg)