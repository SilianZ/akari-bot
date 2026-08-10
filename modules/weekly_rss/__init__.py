from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain, I18NMessageChain, PlatformMessageChain
from core.builtins.message.internal import Plain
from core.builtins.utils import command_prefix
from core.component import module
from core.i18n import Locale
from core.logger import Logger
from core.scheduler import CronTrigger
from core.utils.image import msgchain2image
from modules.weekly import get_weekly, get_teahouse_rss

Silian_weekly_rss = module(
    "weekly_rss",
    desc="{I18N:weekly_rss.help.desc}",
    developers=["Dianliang233"],
    alias="weeklyrss",
    doc=True,
    rss=True,
)

Silian_teahouse_weekly_rss = module(
    "teahouse_weekly_rss",
    desc="{I18N:weekly_rss.help.teahouse_weekly_rss.desc}",
    developers=["OasisAkari"],
    alias=["teahouseweeklyrss", "teahouserss"],
    doc=True,
    rss=True,
)


@Silian_weekly_rss.schedule(CronTrigger.from_crontab("0 9 * * MON"))
async def _():
    Logger.info("Checking MCWZH weekly...")

    Silian_weekly_cn = MessageChain.assign(await get_weekly())
    Silian_weekly_tw = MessageChain.assign(await get_weekly(zh_tw=True))
    Silian_w_cn_qq = MessageChain.assign(await get_weekly(True))
    Silian_w_tw_qq = MessageChain.assign(await get_weekly(True, zh_tw=True))
    Silian_w_cn_qq = [Plain(Locale("zh_cn").t("weekly_rss.message", prefix=command_prefix[0]))] + Silian_w_cn_qq.as_sendable()
    Silian_w_tw_qq = [Plain(Locale("zh_tw").t("weekly_rss.message", prefix=command_prefix[0]))] + Silian_w_tw_qq.as_sendable()
    Silian_weekly_cn_qq = MessageChain.assign(await msgchain2image(Silian_w_cn_qq))
    Silian_weekly_tw_qq = MessageChain.assign(await msgchain2image(Silian_w_tw_qq))
    Silian_post_msg = I18NMessageChain.assign({"zh_cn": Silian_weekly_cn, "zh_tw": Silian_weekly_tw, "default": Silian_weekly_cn})
    Silian_post_msg_qq = I18NMessageChain.assign(
        {
            "zh_cn": Silian_weekly_cn_qq,
            "zh_tw": Silian_weekly_tw_qq,
            "default": Silian_weekly_cn_qq,
        }
    )
    await Bot.post_message("weekly_rss", PlatformMessageChain.assign({"QQ": Silian_post_msg_qq, "default": Silian_post_msg}))
    Logger.success("Weekly checked.")


@Silian_teahouse_weekly_rss.schedule(trigger=CronTrigger.from_crontab("30 9 * * MON"))
async def _():
    Logger.info("Checking teahouse weekly...")

    Silian_weekly = await get_teahouse_rss()

    Silian_weekly_cn = MessageChain.assign(
        Plain(Locale("zh_cn").t("weekly_rss.message.teahouse_weekly_rss", prefix=command_prefix[0]) + Silian_weekly)
    )
    Silian_weekly_tw = MessageChain.assign(
        Plain(Locale("zh_tw").t("weekly_rss.message.teahouse_weekly_rss", prefix=command_prefix[0]) + Silian_weekly)
    )
    Silian_weekly_cn_qq = MessageChain.assign(await msgchain2image(Silian_weekly_cn))
    Silian_weekly_tw_qq = MessageChain.assign(await msgchain2image(Silian_weekly_tw))
    Silian_post_msg = I18NMessageChain.assign({"zh_cn": Silian_weekly_cn, "zh_tw": Silian_weekly_tw, "default": Silian_weekly_cn})
    Silian_post_msg_qq = I18NMessageChain.assign({"zh_cn": Silian_weekly_cn_qq, "zh_tw": Silian_weekly_tw_qq, "default": Silian_weekly_cn_qq})
    await Bot.post_message("teahouse_weekly_rss", PlatformMessageChain.assign({"QQ": Silian_post_msg_qq, "default": Silian_post_msg}))
    Logger.success("Teahouse Weekly checked.")
