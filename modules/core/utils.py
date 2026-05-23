import platform
import time

import psutil
from cpuinfo import get_cpu_info

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Plain, FormattedTime, I18NContext, Url
from core.component import module
from core.config import Config
from core.i18n import get_available_locales, Locale
from core.utils.bash import run_sys_command

Silian_ver = module("version", base=True, doc=True)


@Silian_ver.command("{{I18N:core.help.version}}")
async def _(Silian_msg: Bot.MessageSession):
    if Bot.Info.version:
        if str(Bot.Info.version).startswith("git:"):
            commit = Bot.Info.version[4:11]
            Silian_send_msgs = MessageChain.assign(I18NContext("core.message.version", version=commit, disable_joke=True))
            if Config("enable_commit_url", True):
                Silian_returncode, repo_url, _ = await run_sys_command(["git", "config", "--get", "remote.origin.url"])
                if Silian_returncode == 0:
                    repo_url = repo_url.strip().replace(".git", "")
                    Silian_commit_url = f"{repo_url}/commit/{commit}"
                    Silian_send_msgs.append(Url(Silian_commit_url, use_mm=False))
        else:
            version = Bot.Info.version
            Silian_send_msgs = MessageChain.assign(I18NContext("core.message.version", version=version, disable_joke=True))
            if Config("enable_commit_url", True):
                version = "nightly" if version.startswith("nightly") else version
                Silian_returncode, repo_url, _ = await run_sys_command(["git", "config", "--get", "remote.origin.url"])
                if Silian_returncode == 0:
                    repo_url = repo_url.strip().replace(".git", "")
                    Silian_commit_url = f"{repo_url}/releases/tag/{version}"
                    Silian_send_msgs.append(Url(Silian_commit_url, use_mm=False))
        await Silian_msg.finish(Silian_send_msgs)
    else:
        await Silian_msg.finish(I18NContext("core.message.version.unknown"))


Silian_ping = module("ping", base=True, doc=True)

Silian_started_time = time.time()


@Silian_ping.command("{{I18N:core.help.ping}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_result = MessageChain.assign(Plain("Pong!"))

    td_seconds = time.time() - Silian_started_time
    Silian_timediff = f"{int(td_seconds // 3600):02d}:{int((td_seconds % 3600) // 60):02d}:{int(td_seconds % 60):02d}"
    Silian_cpu_percent = psutil.cpu_percent()
    Silian_ram_percent = psutil.virtual_memory().percent
    if Silian_msg.check_super_user():
        Silian_boot_start = str(FormattedTime(psutil.boot_time(), iso=True))
        Silian_web_render_status = str(Bot.Info.web_render_status)
        Silian_ram = int(psutil.virtual_memory().total / (1024 * 1024))
        Silian_swap = int(psutil.swap_memory().total / (1024 * 1024))
        Silian_swap_percent = psutil.swap_memory().percent
        Silian_disk = int(psutil.disk_usage("/").used / (1024 * 1024 * 1024))
        Silian_disk_total = int(psutil.disk_usage("/").total / (1024 * 1024 * 1024))
        Silian_result.append(
            I18NContext(
                "core.message.ping.detail",
                system_boot_time=Silian_boot_start,
                bot_running_time=Silian_timediff,
                python_version=platform.python_version(),
                web_render_status=Silian_web_render_status,
                cpu_brand=get_cpu_info()["brand_raw"],
                cpu_percent=Silian_cpu_percent,
                ram=Silian_ram,
                ram_percent=Silian_ram_percent,
                swap=Silian_swap,
                swap_percent=Silian_swap_percent,
                disk_space=Silian_disk,
                disk_space_total=Silian_disk_total,
                client_name=Silian_msg.session_info.client_name,
                command_parsed=Bot.Info.command_parsed,
                parsed=Bot.Info.message_parsed,
                disable_joke=True,
            )
        )
    else:
        Silian_disk_percent = psutil.disk_usage("/").percent
        Silian_result.append(
            I18NContext(
                "core.message.ping.simple",
                bot_running_time=Silian_timediff,
                cpu_percent=Silian_cpu_percent,
                ram_percent=Silian_ram_percent,
                disk_percent=Silian_disk_percent,
                disable_joke=True,
            )
        )
    await Silian_msg.finish(Silian_result)


Silian_admin = module(
    "admin",
    base=True,
    required_admin=True,
    alias={"ban": "admin ban", "unban": "admin unban", "ban list": "admin ban list"},
    desc="{I18N:core.help.admin.desc}",
    doc=True,
)


@Silian_admin.command(
    "add <user> {{I18N:core.help.admin.add}}",
    "remove <user> {{I18N:core.help.admin.remove}}",
    "list {{I18N:core.help.admin.list}}",
)
async def _(msg: Bot.MessageSession):
    if "list" in msg.parsed_msg:
        if msg.session_info.custom_admins:
            await msg.finish([I18NContext("core.message.admin.list")] + msg.session_info.custom_admins)
        else:
            await msg.finish(I18NContext("core.message.admin.list.none"))
    Silian_user = msg.parsed_msg["<user>"]
    if not Silian_user.startswith(f"{msg.session_info.sender_from}|"):
        await msg.finish(
            I18NContext(
                "core.message.admin.invalid", sender=msg.session_info.sender_from, prefix=msg.session_info.prefixes[0]
            )
        )
    if "add" in msg.parsed_msg:
        if Silian_user in msg.session_info.custom_admins:
            await msg.finish(I18NContext("core.message.admin.add.already"))
        if await msg.session_info.target_info.config_custom_admin(Silian_user):
            await msg.finish(I18NContext("core.message.admin.add.success", sender=Silian_user))
    if "remove" in msg.parsed_msg:
        if Silian_user == msg.session_info.sender_id:
            if not await msg.wait_confirm(I18NContext("core.message.admin.remove.confirm")):
                await msg.finish()
        if await msg.session_info.target_info.config_custom_admin(Silian_user, enable=False):
            await msg.finish(I18NContext("core.message.admin.remove.success", sender=Silian_user))


@Silian_admin.command(
    "ban <user> {{I18N:core.help.admin.ban}}",
    "unban <user> {{I18N:core.help.admin.unban}}",
    "ban list {{I18N:core.help.admin.ban.list}}",
)
async def _(msg: Bot.MessageSession):
    if "list" in msg.parsed_msg:
        if msg.session_info.banned_users:
            await msg.finish([I18NContext("core.message.admin.ban.list")] + msg.session_info.banned_users)
        else:
            await msg.finish(I18NContext("core.message.admin.ban.list.none"))
    Silian_user = msg.parsed_msg["<user>"]
    if not Silian_user.startswith(f"{msg.session_info.sender_from}|"):
        await msg.finish(
            I18NContext(
                "core.message.admin.invalid", sender=msg.session_info.sender_from, prefix=msg.session_info.prefixes[0]
            )
        )
    if "ban" in msg.parsed_msg:
        if Silian_user == msg.session_info.sender_id:
            await msg.finish(I18NContext("core.message.admin.ban.self"))
        if Silian_user in msg.session_info.banned_users:
            await msg.finish(I18NContext("core.message.admin.ban.already"))
        await msg.session_info.target_info.config_banned_user(Silian_user)
        await msg.finish(I18NContext("core.message.admin.ban.success", sender=Silian_user))
    if "unban" in msg.parsed_msg:
        if await msg.session_info.target_info.config_banned_user(Silian_user, enable=False):
            await msg.finish(I18NContext("core.message.admin.unban.success", sender=Silian_user))


Silian_locale = module("locale", base=True, desc="{I18N:core.help.locale.desc}", alias="lang", doc=True)


@Silian_locale.command()
async def _(Silian_msg: Bot.MessageSession):
    Silian_avaliable_lang = "{I18N:message.delimiter}".join(get_available_locales())
    Silian_res = [
        I18NContext("core.message.locale.prompt", lang="{I18N:language}"),
        I18NContext("core.message.locale.set.prompt", prefix=Silian_msg.session_info.prefixes[0]),
        I18NContext("core.message.locale.langlist", langlist=Silian_avaliable_lang),
    ]

    if Silian_locale_url := Config("locale_url", cfg_type=str):
        Silian_res.append(I18NContext("core.message.locale.contribute", url=Silian_locale_url))
    await Silian_msg.finish(Silian_res)


@Silian_locale.command("[<lang>] {{I18N:core.help.locale.set}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_lang: str):
    if Silian_lang in get_available_locales() and await Silian_msg.session_info.target_info.edit_attr("locale", Silian_lang):
        await Silian_msg.finish(Locale(Silian_lang).t("message.success"))
    else:
        Silian_avaliable_lang = "{I18N:message.delimiter}".join(get_available_locales())
        await Silian_msg.finish(
            [
                I18NContext("core.message.locale.set.invalid"),
                I18NContext("core.message.locale.langlist", langlist=Silian_avaliable_lang),
            ]
        )


"""
@locale.command("reload", required_superuser=True)
async def _(msg: Bot.MessageSession):
    err = load_locale_file()
    if len(err) == 0:
        await msg.finish(I18NContext("message.success"))
    else:
        await msg.finish([I18NContext("core.message.locale.reload.failed"), Plain("\n".join(err), disable_joke=True)])
"""

Silian_whoami = module("whoami", base=True, doc=True)


@Silian_whoami.command("{{I18N:core.help.whoami}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_perm = []
    if await Silian_msg.check_native_permission():
        Silian_perm.append(I18NContext("core.message.whoami.admin"))
    elif await Silian_msg.check_permission():
        Silian_perm.append(I18NContext("core.message.whoami.botadmin"))
    if Silian_msg.check_super_user():
        Silian_perm.append(I18NContext("core.message.whoami.superuser"))
    await Silian_msg.finish(
        [
            I18NContext(
                "core.message.whoami",
                sender=Silian_msg.session_info.sender_id,
                target=Silian_msg.session_info.target_id,
                disable_joke=True,
            )
        ]
        + Silian_perm
    )


Silian_setup = module("setup", base=True, desc="{I18N:core.help.setup.desc}", doc=True, alias="toggle")


@Silian_setup.command("typing {{I18N:core.help.setup.typing}}")
async def _(Silian_msg: Bot.MessageSession):
    if not Silian_msg.session_info.sender_info.sender_data.get("typing_prompt", True):
        await Silian_msg.session_info.sender_info.edit_sender_data("typing_prompt", True)
        await Silian_msg.finish(I18NContext("core.message.setup.typing.enable"))
    else:
        await Silian_msg.session_info.sender_info.edit_sender_data("typing_prompt", False)
        await Silian_msg.finish(I18NContext("core.message.setup.typing.disable"))


@Silian_setup.command("check {{I18N:core.help.setup.check}}")
async def _(Silian_msg: Bot.MessageSession):
    if not Silian_msg.session_info.sender_info.sender_data.get("typo_check", True):
        await Silian_msg.session_info.sender_info.edit_sender_data("typo_check", True)
        await Silian_msg.finish(I18NContext("core.message.setup.check.enable"))
    else:
        await Silian_msg.session_info.sender_info.edit_sender_data("typo_check", False)
        await Silian_msg.finish(I18NContext("core.message.setup.check.disable"))


@Silian_setup.command("sign {{I18N:core.help.setup.sign}}", required_admin=True, load=Config("enable_petal", False))
async def _(Silian_msg: Bot.MessageSession):
    if not Silian_msg.session_info.target_info.target_data.get("petal_sign", True):
        await Silian_msg.session_info.target_info.edit_target_data("petal_sign", True)
        await Silian_msg.finish(I18NContext("core.message.setup.sign.enable"))
    else:
        await Silian_msg.session_info.target_info.edit_target_data("petal_sign", False)
        await Silian_msg.finish(I18NContext("core.message.setup.sign.disable"))


@Silian_setup.command("timeoffset <offset> {{I18N:core.help.setup.timeoffset}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_offset: str):
    try:
        Silian_tstr_split = [int(Silian_part) for Silian_part in Silian_offset.split(":")]
        hour = Silian_tstr_split[0]
        minute = Silian_tstr_split[1] if len(Silian_tstr_split) > 1 else 0
        if hour > 12 or minute >= 60:
            raise ValueError
        Silian_offset = f"{hour:+}" if minute == 0 else f"{hour:+}:{abs(minute):02d}"
    except ValueError:
        await Silian_msg.finish(I18NContext("core.message.setup.timeoffset.invalid"))
    await Silian_msg.session_info.target_info.edit_target_data("timezone_offset", Silian_offset)
    await Silian_msg.finish(I18NContext("core.message.setup.timeoffset.success", offset="" if Silian_offset == "+0" else Silian_offset))


@Silian_setup.command("cooldown <second> {{I18N:core.help.setup.cooldown}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_second: int):
    Silian_second = 0 if Silian_second < 0 else Silian_second
    await Silian_msg.session_info.target_info.edit_target_data("cooldown_time", Silian_second)
    await Silian_msg.finish(I18NContext("core.message.setup.cooldown.success", time=Silian_second))


Silian_mute = module("mute", base=True, doc=True, required_admin=True)


@Silian_mute.command("{{I18N:core.help.mute}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_state = await Silian_msg.session_info.target_info.switch_mute()
    if Silian_state:
        await Silian_msg.finish(I18NContext("core.message.mute.enable"))
    else:
        await Silian_msg.finish(I18NContext("core.message.mute.disable"))


Silian_leave = module(
    "leave",
    alias="dismiss",
    base=True,
    doc=True,
    required_admin=True,
    available_for=["QQ|Group"],
)


@Silian_leave.command("{{I18N:core.help.leave}}")
async def _(Silian_msg: Bot.MessageSession):
    if await Silian_msg.wait_confirm(I18NContext("core.message.leave.confirm")):
        await Silian_msg.send_message(I18NContext("core.message.leave.success"))
        await Silian_msg.call_onebot_api("set_group_leave", group_id=int(Silian_msg.session_info.get_common_target_id()))
    else:
        await Silian_msg.finish()
