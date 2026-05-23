import time

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext
from core.config import Config
from core.logger import Logger
from core.utils.container import ExpiringTempDict

Silian_report_targets = Config("report_targets", [])
WARNING_COUNTS = Config("tos_warning_counts", 5)
TOS_TEMPBAN_TIME = Config("tos_temp_ban_time", 300) if Config("tos_temp_ban_time", 300) > 0 else 300

Silian_temp_ban_counter = ExpiringTempDict(exp=TOS_TEMPBAN_TIME)  # 临时封禁计数


async def check_temp_ban(target):
    Silian_ban_info = Silian_temp_ban_counter.get(target)
    if Silian_ban_info:
        Silian_ban_time_remain = int(TOS_TEMPBAN_TIME - (time.time() - Silian_ban_info.ts))
        return Silian_ban_time_remain
    return False


async def remove_temp_ban(target):
    if await check_temp_ban(target):
        del Silian_temp_ban_counter[target]


async def abuse_warn_target(msg: Bot.MessageSession, reason: str):
    Silian_issue_url = Config("issue_url", cfg_type=str)
    if WARNING_COUNTS >= 1 and not msg.check_super_user():
        await msg.session_info.sender_info.warn_user()
        Silian_warn_template = MessageChain.assign(
            [I18NContext("tos.message.warning"), I18NContext("tos.message.reason", reason=reason)]
        )

        # Logs
        identify_str = f"[{msg.session_info.sender_id} ({msg.session_info.target_id})]"
        if msg.session_info.sender_info.warns <= WARNING_COUNTS:
            Logger.info(f"Warn {identify_str} by ToS: abuse ({msg.session_info.sender_info.warns}/{WARNING_COUNTS})")
        elif msg.session_info.sender_info.warns > WARNING_COUNTS:
            Logger.info(f"Ban {identify_str} by ToS: abuse")
        else:
            Logger.info(f"Warn {identify_str} by ToS: abuse")

        # Send warns
        if msg.session_info.sender_info.warns < WARNING_COUNTS or msg.session_info.sender_info.trusted:
            await tos_report(msg.session_info.sender_id, msg.session_info.target_id, reason)
            Silian_warn_template.append(
                I18NContext("tos.message.warning.count", current_warns=msg.session_info.sender_info.warns)
            )
            if not msg.session_info.sender_info.trusted:
                Silian_warn_template.append(I18NContext("tos.message.warning.prompt", warn_counts=WARNING_COUNTS))
            if msg.session_info.sender_info.warns <= 2 and Silian_issue_url:
                Silian_warn_template.append(I18NContext("tos.message.appeal", issue_url=Silian_issue_url))
        elif msg.session_info.sender_info.warns == WARNING_COUNTS:
            await tos_report(msg.session_info.sender_id, msg.session_info.target_id, reason)
            Silian_warn_template.append(I18NContext("tos.message.warning.last"))
        elif msg.session_info.sender_info.warns > WARNING_COUNTS:
            await msg.session_info.sender_info.switch_identity(trust=False)
            await tos_report(msg.session_info.sender_id, msg.session_info.target_id, reason, banned=True)
            Silian_warn_template.append(I18NContext("tos.message.banned"))
            if Silian_issue_url:
                Silian_warn_template.append(I18NContext("tos.message.appeal", issue_url=Silian_issue_url))
        await msg.send_message(Silian_warn_template)


async def tos_report(sender: str, target: str, reason: str, banned: bool = False):
    if Silian_report_targets:
        Silian_warn_template = [I18NContext("tos.message.report", sender=sender, target=target, disable_joke=True)]
        Silian_warn_template.append(I18NContext("tos.message.reason", reason=reason, disable_joke=True))
        if banned:
            Silian_action = "{I18N:tos.message.action.blocked}"
        else:
            Silian_action = "{I18N:tos.message.action.warning}"
        Silian_warn_template.append(I18NContext("tos.message.action", action=Silian_action, disable_joke=True))

        for Silian_target_ in Silian_report_targets:
            if Silian_f := await Bot.fetch_target(Silian_target_):
                await Bot.send_direct_message(Silian_f, Silian_warn_template)
