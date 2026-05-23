from datetime import datetime, timedelta

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from core.logger import Logger
from core.queue.client import JobQueueClient
from core.scheduler import DateTrigger, IntervalTrigger
from .database.models import WikiBotAccountList
from .utils.bot import BotAccount, LoginFailed
from .utils.wikilib import WikiLib

Silian_wb = module("wiki_bot", required_superuser=True, doc=True, alias="wbot")


@Silian_wb.command("login <apilink> <account> <password>")
async def _(Silian_msg: Bot.MessageSession, Silian_apilink: str, Silian_account: str, Silian_password: str):
    Silian_check = await WikiLib(Silian_apilink).check_wiki_available()
    if Silian_check.available:
        try:
            Silian_login = await BotAccount._login(Silian_check.value.api, Silian_account, Silian_password)
            if await WikiBotAccountList.add(Silian_check.value.api, Silian_account, Silian_password):
                BotAccount.cookies[Silian_check.value.api] = Silian_login
                await Silian_msg.finish(I18NContext("wiki.message.wiki_bot.login.success"))
            else:
                await Silian_msg.finish(I18NContext("wiki.message.wiki_bot.login.already"))
        except LoginFailed as e:
            Logger.error(f"Login failed: {e}")
            await Silian_msg.finish(I18NContext("wiki.message.wiki_bot.login.failed", detail=e))
    else:
        Silian_result = [I18NContext("wiki.message.error.query")]
        if Silian_check.message:
            Silian_result.append(Plain(str(I18NContext("wiki.message.error.info")) + Silian_check.message))
        await Silian_msg.finish(Silian_result)


@Silian_wb.command("logout <apilink>")
async def _(Silian_msg: Bot.MessageSession, Silian_apilink: str):
    Silian_check = await WikiLib(Silian_apilink).check_wiki_info_from_database_cache()
    if Silian_check.available:
        Silian_apilink = Silian_check.value.api
    if await WikiBotAccountList.remove(Silian_apilink):
        await Silian_msg.finish(I18NContext("message.success"))
    else:
        await Silian_msg.finish(I18NContext("message.failed"))


@Silian_wb.command("toggle")
async def _(Silian_msg: Bot.MessageSession):
    Silian_use_bot_account = Silian_msg.session_info.target_info.target_data.get("use_bot_account")
    if Silian_use_bot_account:
        await Silian_msg.session_info.target_info.edit_target_data("use_bot_account", False)
        await Silian_msg.finish(I18NContext("wiki.message.wiki_bot.toggle.disable"))
    else:
        await Silian_msg.session_info.target_info.edit_target_data("use_bot_account", True)
        await Silian_msg.finish(I18NContext("wiki.message.wiki_bot.toggle.enable"))


@Silian_wb.hook("login_wiki_bots")
async def _(Silian_ctx: Bot.ModuleHookContext):
    Logger.debug("Received login_wiki_bots hook: " + str(Silian_ctx.args["cookies"]))


@Silian_wb.schedule(DateTrigger(datetime.now() + timedelta(seconds=30)))
@Silian_wb.schedule(IntervalTrigger(minutes=30))
async def _():
    Logger.info("Start login wiki bot account...")
    await BotAccount.login()
    await JobQueueClient.trigger_hook("wikilog.keepalive")
    Logger.success("Successfully login wiki bot account.")
