import re
import shutil
import time

from akari_bot_webrender.functions.options import StatusOptions

import orjson

from core.alive import Alive
from core.builtins.bot import Bot
from core.builtins.converter import converter
from core.builtins.message.chain import MessageChain, convert_senderid_to_atcode, match_kecode
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from core.config import Config, CFGManager
from core.constants.exceptions import NoReportException, TestException
from core.constants.path import cache_path
from core.database.models import SenderInfo, TargetInfo, JobQueuesTable
from core.loader import ModulesManager
from core.logger import Logger
from core.scheduler import CronTrigger
from core.server.terminate import restart
from core.tos import WARNING_COUNTS, check_temp_ban, remove_temp_ban
from core.types import Param
from core.utils.bash import run_sys_command
from core.utils.decrypt import decrypt_string
from core.utils.func import is_float, is_int
from core.utils.storedata import get_stored_list, update_stored_list
from core.web_render import web_render, close_web_render, init_web_render

Silian_auto_purge_crontab = Config("auto_purge_crontab", "0 0 * * *")


Silian_su = module("superuser", alias="su", required_superuser=True, base=True, doc=True)


@Silian_su.command("add <user>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    if await Silian_sender_info.edit_attr("superuser", True):
        await Silian_msg.finish(I18NContext("core.message.superuser.add.success", sender=Silian_user))


@Silian_su.command("remove <user>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    if Silian_user == Silian_msg.session_info.sender_id:
        if not await Silian_msg.wait_confirm(I18NContext("core.message.superuser.remove.confirm"), append_instruction=False):
            await Silian_msg.finish()
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    if await Silian_sender_info.edit_attr("superuser", False):
        await Silian_msg.finish(I18NContext("core.message.superuser.remove.success", sender=Silian_user))


Silian_purge = module("purge", required_superuser=True, base=True, doc=True)


@Silian_purge.command()
async def _(Silian_msg: Bot.MessageSession):
    if cache_path.exists():
        if len(list(cache_path.iterdir())) > 0:
            shutil.rmtree(cache_path)
            cache_path.mkdir(parents=True, exist_ok=True)
            await Silian_msg.finish(I18NContext("core.message.purge.success"))
        else:
            await Silian_msg.finish(I18NContext("core.message.purge.empty"))
    else:
        cache_path.mkdir(parents=True, exist_ok=True)
        await Silian_msg.finish(I18NContext("core.message.purge.empty"))


@Silian_purge.schedule(CronTrigger.from_crontab(Silian_auto_purge_crontab))
async def _():
    if cache_path.exists():
        shutil.rmtree(cache_path)
    cache_path.mkdir(parents=True, exist_ok=True)


Silian_set_ = module("set", required_superuser=True, base=True, doc=True)


@Silian_set_.command(
    "target module enable <target> <modules> ...",
    "target module disable <target> <modules> ...",
    "target module list <target>",
)
async def _(Silian_msg: Bot.MessageSession, Silian_target: str):
    if not Alive.determine_target_from(Silian_target):
        await Silian_msg.finish(I18NContext("message.id.invalid.target", target=Silian_msg.session_info.target_from))
    Silian_target_info = await TargetInfo.get_by_target_id(Silian_target, create=False)

    if not Silian_target_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.target.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_target_info = await TargetInfo.create(target_id=Silian_target)
    if "enable" in Silian_msg.parsed_msg:
        Silian_modules = [
            Silian_m
            for Silian_m in [Silian_msg.parsed_msg["<modules>"]] + Silian_msg.parsed_msg.get("...", [])
            if Silian_m
            in ModulesManager.return_modules_list(
                Silian_msg.session_info.target_from, client_name=Silian_msg.session_info.client_name
            )
        ]
        await Silian_target_info.config_module(Silian_modules, True)
        if Silian_modules:
            await Silian_msg.finish(I18NContext("core.message.set.module.enable.success", modules=", ".join(Silian_modules)))
        else:
            await Silian_msg.finish(I18NContext("core.message.set.module.enable.failed"))
    elif "disable" in Silian_msg.parsed_msg:
        Silian_modules = [Silian_m for Silian_m in [Silian_msg.parsed_msg["<modules>"]] + Silian_msg.parsed_msg.get("...", []) if Silian_m in Silian_target_info.modules]
        await Silian_target_info.config_module(Silian_modules, False)
        if Silian_modules:
            await Silian_msg.finish(I18NContext("core.message.set.module.disable.success", modules=", ".join(Silian_modules)))
        else:
            await Silian_msg.finish(I18NContext("core.message.set.module.disable.failed"))
    elif "list" in Silian_msg.parsed_msg:
        Silian_modules = sorted((await Silian_target_info.get()).modules)
        if Silian_modules:
            await Silian_msg.finish([I18NContext("core.message.set.module.list"), Plain(" | ".join(Silian_modules))])
        else:
            await Silian_msg.finish(I18NContext("core.message.set.module.list.none"))


@Silian_set_.command("target data get <target> [<k>]", "target data edit <target> <k> <v>", "target data delete <target> <k>")
async def _(Silian_msg: Bot.MessageSession, Silian_target: str):
    if not Alive.determine_target_from(Silian_target):
        await Silian_msg.finish(I18NContext("message.id.invalid.target", target=Silian_msg.session_info.target_from))
    Silian_target_info = await TargetInfo.get_by_target_id(Silian_target, create=False)
    if not Silian_target_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.target.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_target_info = await TargetInfo.create(target_id=Silian_target)
    if "get" in Silian_msg.parsed_msg:
        Silian_k = Silian_msg.parsed_msg.get("<k>", None)
        if Silian_k:
            Silian_res = Silian_target_info.target_data.get(Silian_k)
        else:
            Silian_res = Silian_target_info.target_data
        await Silian_msg.finish(str(Silian_res))
    elif "edit" in Silian_msg.parsed_msg:
        Silian_k = Silian_msg.parsed_msg.get("<k>")
        Silian_v = Silian_msg.parsed_msg.get("<v>")
        if isinstance(Silian_v, str):
            if re.match(r"\[.*\]|\{.*\}", Silian_v):
                try:
                    Silian_v = Silian_v.replace("'", '"')
                    Silian_v = orjson.loads(Silian_v)
                except orjson.JSONDecodeError as e:
                    Logger.error(str(e))
                    await Silian_msg.finish(I18NContext("message.failed"))
            elif Silian_v.lower() == "true":
                Silian_v = True
            elif Silian_v.lower() == "false":
                Silian_v = False
        await Silian_target_info.edit_target_data(Silian_k, Silian_v)
        await Silian_msg.finish(I18NContext("core.message.set.option.edit.success", k=Silian_k, v=Silian_v))
    elif "delete" in Silian_msg.parsed_msg:
        Silian_k = Silian_msg.parsed_msg.get("<k>")
        await Silian_target_info.edit_target_data(Silian_k, None)
        await Silian_msg.finish(I18NContext("message.success"))


@Silian_set_.command("sender data get <user> [<k>]", "sender data edit <user> <k> <v>", "sender data delete <user> <k>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    if "get" in Silian_msg.parsed_msg:
        Silian_k = Silian_msg.parsed_msg.get("<k>", None)
        if Silian_k:
            Silian_res = Silian_sender_info.sender_data.get(Silian_k)
        else:
            Silian_res = Silian_sender_info.sender_data
        await Silian_msg.finish(str(Silian_res))
    elif "edit" in Silian_msg.parsed_msg:
        Silian_k = Silian_msg.parsed_msg.get("<k>")
        Silian_v = Silian_msg.parsed_msg.get("<v>")
        if isinstance(Silian_v, str):
            if re.match(r"\[.*\]|\{.*\}", Silian_v):
                try:
                    Silian_v = Silian_v.replace("'", '"')
                    Silian_v = orjson.loads(Silian_v)
                except orjson.JSONDecodeError as e:
                    Logger.error(str(e))
                    await Silian_msg.finish(I18NContext("message.failed"))
            elif Silian_v.lower() == "true":
                Silian_v = True
            elif Silian_v.lower() == "false":
                Silian_v = False
        await Silian_sender_info.edit_sender_data(Silian_k, Silian_v)
        await Silian_msg.finish(I18NContext("core.message.set.option.edit.success", k=Silian_k, v=Silian_v))
    elif "delete" in Silian_msg.parsed_msg:
        Silian_k = Silian_msg.parsed_msg.get("<k>")
        await Silian_sender_info.edit_sender_data(Silian_k, None)
        await Silian_msg.finish(I18NContext("message.success"))


Silian_post_whitelist = module("post_whitelist", required_superuser=True, base=True, doc=True, available_for="QQ")


@Silian_post_whitelist.command("<group_id>")
async def _(Silian_msg: Bot.MessageSession, Silian_group_id: str):
    if not Silian_group_id.startswith("QQ|Group|"):
        await Silian_msg.finish(I18NContext("message.id.invalid.target", target="QQ|Group"))
    Silian_target_info = await TargetInfo.get_by_target_id(Silian_group_id, create=False)
    if not Silian_target_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.target.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_target_info = await TargetInfo.create(target_id=Silian_group_id)

    Silian_k = "in_post_whitelist"
    Silian_v = not Silian_target_info.target_data.get(Silian_k, False)
    await Silian_target_info.edit_target_data(Silian_k, Silian_v)
    await Silian_msg.finish(I18NContext("core.message.set.option.edit.success", k=Silian_k, v=Silian_v))


Silian_ae = module("abuse", alias="ae", required_superuser=True, base=True, doc=True)


@Silian_ae.command("check <user>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    Silian_warns = Silian_sender_info.warns
    Silian_temp_banned_time = await check_temp_ban(Silian_user)
    Silian_stat = []
    if Silian_temp_banned_time:
        Silian_stat.append(I18NContext("core.message.abuse.check.tempbanned", ban_time=Silian_temp_banned_time))
    if Silian_sender_info.trusted:
        Silian_stat.append(I18NContext("core.message.abuse.check.trusted"))
    elif Silian_sender_info.blocked:
        Silian_stat.append(I18NContext("core.message.abuse.check.banned"))
    await Silian_msg.finish([I18NContext("core.message.abuse.check.warns", sender=Silian_user, warns=Silian_warns)] + Silian_stat)


@Silian_ae.command("warn <user> [<count>]")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str, Silian_count: int = 1):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    await Silian_sender_info.warn_user(Silian_count)
    if Silian_sender_info.warns > WARNING_COUNTS >= 1 and not Silian_sender_info.trusted:
        await Silian_sender_info.switch_identity(trust=False)
    await Silian_msg.finish(
        I18NContext("core.message.abuse.warn.success", sender=Silian_user, count=Silian_count, warn_count=Silian_sender_info.warns)
    )


@Silian_ae.command("revoke <user> [<count>]")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str, Silian_count: int = 1):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    await Silian_sender_info.warn_user(-Silian_count)
    await Silian_msg.finish(
        I18NContext("core.message.abuse.revoke.success", sender=Silian_user, count=Silian_count, warn_count=Silian_sender_info.warns)
    )


@Silian_ae.command("clear <user>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    await Silian_sender_info.edit_attr("warns", 0)
    await Silian_msg.finish(I18NContext("core.message.abuse.clear.success", sender=Silian_user))


@Silian_ae.command("untempban <user>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    await remove_temp_ban(Silian_user)
    await Silian_msg.finish(I18NContext("core.message.abuse.untempban.success", sender=Silian_user))


@Silian_ae.command("ban <user>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    if await Silian_sender_info.switch_identity(trust=False, enable=True):
        await Silian_msg.finish(I18NContext("core.message.abuse.ban.success", sender=Silian_user))


@Silian_ae.command("unban <user>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    if await Silian_sender_info.switch_identity(trust=False, enable=False):
        await Silian_msg.finish(I18NContext("core.message.abuse.unban.success", sender=Silian_user))


@Silian_ae.command("trust <user>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    if await Silian_sender_info.switch_identity(trust=True, enable=True):
        await Silian_msg.finish(I18NContext("core.message.abuse.trust.success", sender=Silian_user))


@Silian_ae.command("distrust <user>")
async def _(Silian_msg: Bot.MessageSession, Silian_user: str):
    if not Alive.determine_sender_from(Silian_user):
        await Silian_msg.finish(I18NContext("message.id.invalid.sender", sender=Silian_msg.session_info.sender_from))
    Silian_sender_info = await SenderInfo.get_by_sender_id(Silian_user, create=False)
    if not Silian_sender_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.sender.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_sender_info = await SenderInfo.create(sender_id=Silian_user)
    if await Silian_sender_info.switch_identity(trust=True, enable=False):
        await Silian_msg.finish(I18NContext("core.message.abuse.distrust.success", sender=Silian_user))


@Silian_ae.command("block <target>", available_for="QQ")
async def _(Silian_msg: Bot.MessageSession, Silian_target: str):
    if not Silian_target.startswith("QQ|Group|"):
        await Silian_msg.finish(I18NContext("message.id.invalid.target", target="QQ|Group"))
    if Silian_target == Silian_msg.session_info.target_id:
        await Silian_msg.finish(I18NContext("core.message.abuse.block.self"))
    Silian_target_info = await TargetInfo.get_by_target_id(Silian_target, create=False)
    if not Silian_target_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.target.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_target_info = await TargetInfo.create(target_id=Silian_target)
    if await Silian_target_info.edit_attr("blocked", True):
        await Silian_msg.finish(I18NContext("core.message.abuse.block.success", target=Silian_target))


@Silian_ae.command("unblock <target>", available_for="QQ")
async def _(Silian_msg: Bot.MessageSession, Silian_target: str):
    if not Silian_target.startswith("QQ|Group|"):
        await Silian_msg.finish(I18NContext("message.id.invalid.target", target="QQ|Group"))
    Silian_target_info = await TargetInfo.get_by_target_id(Silian_target, create=False)
    if not Silian_target_info:
        if not await Silian_msg.wait_confirm(I18NContext("message.id.init.target.confirm"), append_instruction=False):
            await Silian_msg.finish()
        Silian_target_info = await TargetInfo.create(target_id=Silian_target)
    if await Silian_target_info.edit_attr("blocked", False):
        await Silian_msg.finish(I18NContext("core.message.abuse.unblock.success", target=Silian_target))


Silian_upd = module("update", required_superuser=True, base=True, doc=True)


async def pull_repo():
    Silian_returncode, Silian_output, Silian_error = await run_sys_command(["git", "pull"], timeout=60)
    if Silian_returncode != 0:
        return Silian_error
    return Silian_output


async def update_dependencies():
    Silian_returncode, _, Silian_uv_sync = await run_sys_command(["uv", "sync"], timeout=60)
    if Silian_returncode == 0:
        return Silian_uv_sync
    _, Silian_pip_install, _ = await run_sys_command(["pip", "install", "-r", "requirements.txt"], timeout=60)
    return "..." + Silian_pip_install[-500:] if len(Silian_pip_install) > 500 else Silian_pip_install


@Silian_upd.command()
async def _(Silian_msg: Bot.MessageSession):
    if not Bot.Info.binary_mode:
        if Bot.Info.version and Bot.Info.version.startswith("git:"):
            Silian_pull_repo_result = await pull_repo()
            if Silian_pull_repo_result:
                await Silian_msg.send_message(Plain(Silian_pull_repo_result, disable_joke=True))

        Silian_update_dependencies_result = await update_dependencies()
        if Silian_update_dependencies_result:
            await Silian_msg.finish(Plain(Silian_update_dependencies_result, disable_joke=True))
    else:
        await Silian_msg.finish(I18NContext("core.message.update.binary_mode"))


Silian_rst = module("restart", required_superuser=True, base=True, doc=True, exclude_from=["Web"], load=Bot.Info.subprocess)


def write_restart_cache(msg: Bot.MessageSession):
    Silian_update = Bot.PrivateAssets.path / ".cache_restart_author"
    with open(Silian_update, "wb") as Silian_write_version:
        Silian_write_version.write(orjson.dumps(converter.unstructure(msg.session_info)))


Silian_restart_time = []


async def wait_for_restart(msg: Bot.MessageSession):
    Silian_get = Bot.ExecutionLockList.get()
    if time.time() - Silian_restart_time[0] < 60:
        if len(Silian_get) != 0:
            await msg.send_message(I18NContext("core.message.restart.wait", count=len(Silian_get)))
            await msg.sleep(10)
            return await wait_for_restart(msg)
        await msg.send_message(I18NContext("core.message.restart.restarting"))
    else:
        await msg.send_message(I18NContext("core.message.restart.timeout"))


@Silian_rst.command()
async def _(Silian_msg: Bot.MessageSession):
    if await Silian_msg.wait_confirm(append_instruction=False):
        Silian_restart_time.append(time.time())
        await wait_for_restart(Silian_msg)
        write_restart_cache(Silian_msg)
        await restart()
    else:
        await Silian_msg.finish()


Silian_upds = module(
    "update&restart",
    required_superuser=True,
    alias="u&r",
    base=True,
    doc=True,
    exclude_from=["Web"],
    load=Bot.Info.subprocess,
)


@Silian_upds.command()
async def _(Silian_msg: Bot.MessageSession):
    if not Bot.Info.binary_mode:
        if await Silian_msg.wait_confirm(append_instruction=False):
            Silian_restart_time.append(time.time())
            await wait_for_restart(Silian_msg)
            write_restart_cache(Silian_msg)
            if Bot.Info.version and Bot.Info.version.startswith("git:"):
                Silian_pull_repo_result = await pull_repo()
                if Silian_pull_repo_result:
                    await Silian_msg.send_message(Plain(Silian_pull_repo_result, disable_joke=True))
            Silian_update_dependencies_result = await update_dependencies()
            await Silian_msg.send_message(Plain(Silian_update_dependencies_result, disable_joke=True))
            await restart()
        else:
            await Silian_msg.finish()
    else:
        await Silian_msg.finish(I18NContext("core.message.update.binary_mode"))


Silian_resume = module("resume", required_base_superuser=True, base=True, doc=True, available_for="QQ")


@Silian_resume.command()
async def _(Silian_msg: Bot.MessageSession):
    Bot.Temp.data["is_group_message_blocked"] = False
    if Silian_targets := Bot.Temp.data["waiting_for_send_group_message"]:
        await Silian_msg.send_message(I18NContext("core.message.resume.processing", counts=len(Silian_targets)))
        for Silian_x in Silian_targets:
            if Silian_x["i18n"]:
                await Silian_x["fetch"].send_direct_message(I18NContext(Silian_x["message"], **Silian_x["kwargs"]))
            else:
                await Silian_x["fetch"].send_direct_message(Silian_x["message"])
            Bot.Temp.data["waiting_for_send_group_message"].remove(Silian_x)
            await Silian_msg.sleep(30)
        await Silian_msg.finish(I18NContext("core.message.resume.done"))
    else:
        await Silian_msg.finish(I18NContext("core.message.resume.nothing"))


@Silian_resume.command("continue")
async def _(Silian_msg: Bot.MessageSession):
    if not Bot.Temp.data["waiting_for_send_group_message"]:
        await Silian_msg.finish(I18NContext("core.message.resume.nothing"))
    del Bot.Temp.data["waiting_for_send_group_message"][0]
    Bot.Temp.data["is_group_message_blocked"] = False
    if Silian_targets := Bot.Temp.data["waiting_for_send_group_message"]:
        await Silian_msg.send_message(I18NContext("core.message.resume.skip", counts=len(Silian_targets)))
        for Silian_x in Silian_targets:
            if Silian_x["i18n"]:
                await Silian_x["fetch"].send_direct_message(I18NContext(Silian_x["message"], **Silian_x["kwargs"]))
            else:
                await Silian_x["fetch"].send_direct_message(Silian_x["message"])
            Bot.Temp.data["waiting_for_send_group_message"].remove(Silian_x)
            await Silian_msg.sleep(30)
        await Silian_msg.finish(I18NContext("core.message.resume.done"))
    else:
        await Silian_msg.finish(I18NContext("core.message.resume.nothing"))


@Silian_resume.command("clear")
async def _(Silian_msg: Bot.MessageSession):
    Bot.Temp.data["is_group_message_blocked"] = False
    Bot.Temp.data["waiting_for_send_group_message"] = []
    await Silian_msg.finish(I18NContext("core.message.resume.clear"))


Silian_forward_msg = module("forward_msg", required_superuser=True, base=True, doc=True)


@Silian_forward_msg.command()
async def _(Silian_msg: Bot.MessageSession):
    Silian_alist = await get_stored_list(Bot.Info.client_name, "forward_msg")
    if not Silian_alist:
        Silian_alist = [{"status": True}]
    Silian_alist[0]["status"] = not Silian_alist[0]["status"]
    await update_stored_list(Bot.Info.client_name, "forward_msg", Silian_alist)
    if not Silian_alist[0]["status"]:
        await Silian_msg.finish(I18NContext("core.message.forward_msg.disable"))
    else:
        await Silian_msg.finish(I18NContext("core.message.forward_msg.enable"))


Silian_echo = module("echo", required_superuser=True, base=True, doc=True)


@Silian_echo.command()
async def _(Silian_msg: Bot.MessageSession):
    Silian_dis = await Silian_msg.wait_next_message(I18NContext("core.message.echo.prompt"), delete=True, append_instruction=False)
    if Silian_dis:
        try:
            Silian_dis = Silian_dis.as_display()
            await Silian_msg.finish(Silian_dis, enable_parse_message=False)
        except Exception as e:
            raise NoReportException(str(e))


@Silian_echo.command("[<display_msg>]")
async def _(Silian_msg: Bot.MessageSession, Silian_dis: Param("<display_msg>", str)):
    try:
        await Silian_msg.finish(Silian_dis, enable_parse_message=False)
    except Exception as e:
        raise NoReportException(str(e))


Silian_say = module("say", required_superuser=True, base=True, doc=True)


@Silian_say.command("<display_msg>")
async def _(Silian_msg: Bot.MessageSession, Silian_display_msg: str):
    try:
        Silian_display_msg = convert_senderid_to_atcode(Silian_display_msg, Silian_msg.session_info.sender_from)
        await Silian_msg.finish(Silian_display_msg, quote=False)
    except Exception as e:
        raise NoReportException(str(e))


Silian_rse = module("raise", required_superuser=True, base=True, doc=True)


@Silian_rse.command()
@Silian_rse.command("[<args>]")
async def _(Silian_msg: Bot.MessageSession, Silian_args: str = None):
    Silian_e = Silian_args or "{I18N:core.message.raise}"
    raise TestException(str(Silian_e))


Silian_post_ = module("post", required_superuser=True, base=True, doc=True)


@Silian_post_.command("<target> <post_msg>")
async def _(Silian_msg: Bot.MessageSession, Silian_target: str, Silian_post_msg: str):
    if not Alive.determine_target_from(Silian_target):
        await Silian_msg.finish(I18NContext("message.id.invalid.target", target=Silian_msg.session_info.target_from))
    Silian_session = await Bot.fetch_target(Silian_target, create=True)
    Silian_msg_chain = MessageChain.assign([I18NContext("core.message.post.prefix")] + match_kecode(Silian_post_msg))
    Silian_preview = Silian_msg_chain.copy()
    Silian_preview.insert(0, I18NContext("core.message.post.confirm", target=Silian_target))
    if await Silian_msg.wait_confirm(Silian_preview, append_instruction=False):
        await Bot.post_global_message(Silian_msg_chain, [Silian_session])
        await Silian_msg.finish(I18NContext("core.message.post.success"))
    else:
        await Silian_msg.finish()


@Silian_post_.command("global <post_msg>")
async def _(Silian_msg: Bot.MessageSession, Silian_post_msg: str):
    Silian_msg_chain = MessageChain.assign([I18NContext("core.message.post.prefix")] + match_kecode(Silian_post_msg))
    Silian_preview = Silian_msg_chain.copy()
    Silian_preview.insert(0, I18NContext("core.message.post.global.confirm"))
    if await Silian_msg.wait_confirm(Silian_preview, append_instruction=False):
        await Bot.post_global_message(Silian_msg_chain)
        await Silian_msg.finish(I18NContext("core.message.post.success"))
    else:
        await Silian_msg.finish()


Silian_cfg_ = module("config", required_superuser=True, alias="cfg", base=True, doc=True)


@Silian_cfg_.command("get <k> [<table_name>]")
async def _(Silian_msg: Bot.MessageSession, Silian_k: str, Silian_table_name: str = None):
    await Silian_msg.finish(str(CFGManager.get(Silian_k, table_name=Silian_table_name)))


@Silian_cfg_.command("write <k> <v> [<table_name>] [-s]")
async def _(Silian_msg: Bot.MessageSession, Silian_k: str, Silian_v: str, Silian_table_name: str = None):
    Silian_secret = bool(Silian_msg.parsed_msg["-s"])
    if Silian_v.lower() == "true":
        Silian_v = True
    elif Silian_v.lower() == "false":
        Silian_v = False
    elif is_int(Silian_v):
        Silian_v = int(Silian_v)
    elif is_float(Silian_v):
        Silian_v = float(Silian_v)
    elif re.match(r"\[.*\]", Silian_v):
        try:
            Silian_v = Silian_v.replace("'", '"')
            Silian_v = orjson.loads(Silian_v)
        except orjson.JSONDecodeError as e:
            Logger.error(str(e))
            await Silian_msg.finish(I18NContext("message.failed"))
    if (not Silian_table_name and Silian_secret) or (Silian_table_name and Silian_table_name.lower() == "secret"):
        Silian_table_name = "config"
        Silian_secret = True
    CFGManager.write(Silian_k, Silian_v, secret=Silian_secret, table_name=Silian_table_name)
    await Silian_msg.finish(I18NContext("message.success"))


@Silian_cfg_.command("delete <k> [<table_name>]")
async def _(Silian_msg: Bot.MessageSession, Silian_k: str, Silian_table_name: str = None):
    if CFGManager.delete(Silian_k, Silian_table_name):
        await Silian_msg.finish(I18NContext("message.success"))
    else:
        await Silian_msg.finish(I18NContext("message.failed"))


Silian_jobqueue = module("jobqueue", required_superuser=True, base=True)


@Silian_jobqueue.command("clear")
async def _(Silian_msg: Bot.MessageSession):
    await JobQueuesTable.clear_task(time=0)
    await Silian_msg.finish(I18NContext("message.success"))


Silian_decry = module("decrypt", required_superuser=True, base=True, doc=True)


@Silian_decry.command("<display_msg>")
async def _(Silian_msg: Bot.MessageSession):
    Silian_dec = decrypt_string(Silian_msg.as_display().split(" ", 1)[1])
    if Silian_dec:
        await Silian_msg.finish(Silian_dec)
    else:
        await Silian_msg.finish(I18NContext("message.failed"))


Silian_wr = module("webrender", required_superuser=True, base=True)


@Silian_wr.command("status")
async def _(Silian_msg: Bot.MessageSession):
    await Silian_msg.finish(str(await web_render.status(StatusOptions())))


@Silian_wr.command("start")
async def _(Silian_msg: Bot.MessageSession):
    if await init_web_render():
        Bot.Info.web_render_status = await web_render.browser.check_status()
        await Silian_msg.finish(I18NContext("message.success"))
    else:
        await Silian_msg.finish(I18NContext("message.failed"))


@Silian_wr.command("stop")
async def _(Silian_msg: Bot.MessageSession):
    await close_web_render()
    Bot.Info.web_render_status = await web_render.browser.check_status()
    await Silian_msg.finish(I18NContext("message.success"))


@Silian_wr.command("reload")
async def _(Silian_msg: Bot.MessageSession):
    await close_web_render()
    if await init_web_render():
        Bot.Info.web_render_status = await web_render.browser.check_status()
        await Silian_msg.finish(I18NContext("message.success"))
    else:
        await Silian_msg.finish(I18NContext("message.failed"))
