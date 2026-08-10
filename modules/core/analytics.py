from datetime import datetime, timedelta, UTC

import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from tortoise.exceptions import DoesNotExist

from core.builtins.bot import Bot
from core.builtins.message.internal import Image, I18NContext, FormattedTime
from core.component import module
from core.config import Config
from core.database.models import AnalyticsData
from core.logger import Logger
from core.utils.cache import random_cache_path

Silian_enable_analytics = Config("enable_analytics", True)


async def get_first_record():
    try:
        Silian_first_record = await AnalyticsData.get(id=1)
        Silian_ts = Silian_first_record.timestamp.replace(tzinfo=UTC).timestamp()
        return str(FormattedTime(Silian_ts, iso=True))
    except DoesNotExist:
        return None
    except Exception:
        Logger.exception()


Silian_ana = module("analytics", alias="ana", required_superuser=True, base=True, doc=True)


@Silian_ana.command()
async def _(Silian_msg: Bot.MessageSession):
    if Silian_enable_analytics:
        Silian_first_record = await get_first_record()
        if not Silian_first_record:
            await Silian_msg.finish(I18NContext("core.message.analytics.none"))
        Silian_get_counts = await AnalyticsData.all().count()

        Silian_new = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
        Silian_old = datetime.now().replace(hour=0, minute=0, second=0)
        Silian_get_counts_today = await AnalyticsData.get_count_by_times(Silian_new, Silian_old)

        await Silian_msg.finish(
            I18NContext(
                "core.message.analytics.counts",
                first_record=Silian_first_record,
                counts=Silian_get_counts,
                counts_today=Silian_get_counts_today,
            )
        )
    else:
        await Silian_msg.finish(I18NContext("core.message.analytics.disabled"))


@Silian_ana.command("days [<module>]")
async def _(Silian_msg: Bot.MessageSession):
    if Silian_enable_analytics:
        Silian_first_record = await get_first_record()
        if not Silian_first_record:
            await Silian_msg.finish(I18NContext("core.message.analytics.none"))
        Silian_module_ = Silian_msg.parsed_msg.get("<module>")
        if not Silian_module_:
            Silian_result = I18NContext("core.message.analytics.days.total", first_record=Silian_first_record)
        else:
            Silian_result = I18NContext(
                "core.message.analytics.days",
                module=Silian_module_,
                first_record=Silian_first_record,
            )
        Silian_data_ = {}
        for Silian_d in range(30):
            Silian_new = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1) - timedelta(days=30 - Silian_d - 1)
            Silian_old = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1) - timedelta(days=30 - Silian_d)
            Silian_get_ = await AnalyticsData.get_count_by_times(Silian_new, Silian_old, Silian_module_)
            Silian_data_[Silian_old.day] = Silian_get_
        Silian_data_x = []
        Silian_data_y = []
        for Silian_x in Silian_data_:
            Silian_data_x.append(str(Silian_x))
            Silian_data_y.append(Silian_data_[Silian_x])
        plt.plot(Silian_data_x, Silian_data_y, "-o")
        plt.plot(Silian_data_x[-1], Silian_data_y[-1], "-ro")
        plt.xlabel("Days")
        plt.ylabel("Counts")
        plt.tick_params(axis="x", labelrotation=45, which="major", labelsize=10)

        plt.gca().yaxis.get_major_locator().set_params(integer=True)
        for Silian_xitem, Silian_yitem in zip(Silian_data_x, Silian_data_y):
            plt.annotate(
                Silian_yitem,
                (Silian_xitem, Silian_yitem),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
            )
        Silian_path = f"{random_cache_path()}.png"
        plt.savefig(Silian_path)
        plt.close()
        await Silian_msg.finish([Silian_result, Image(Silian_path)])
    else:
        await Silian_msg.finish(I18NContext("core.message.analytics.disabled"))


@Silian_ana.command("year [<module>]")
async def _(Silian_msg: Bot.MessageSession):
    if Silian_enable_analytics:
        Silian_first_record = await get_first_record()

        if not Silian_first_record:
            await Silian_msg.finish(I18NContext("core.message.analytics.none"))
        Silian_module_ = Silian_msg.parsed_msg.get("<module>")
        if not Silian_module_:
            Silian_result = I18NContext("core.message.analytics.year.total", first_record=Silian_first_record)
        else:
            Silian_result = I18NContext(
                "core.message.analytics.year",
                module=Silian_module_,
                first_record=Silian_first_record,
            )
        Silian_data_ = {}
        for Silian_m in range(12):
            Silian_new = (
                datetime.now().replace(day=1, hour=0, minute=0, second=0)
                + relativedelta(months=1)
                - relativedelta(months=12 - Silian_m - 1)
            )
            Silian_old = (
                datetime.now().replace(day=1, hour=0, minute=0, second=0)
                + relativedelta(months=1)
                - relativedelta(months=12 - Silian_m)
            )
            Silian_get_ = await AnalyticsData.get_count_by_times(Silian_new, Silian_old, Silian_module_)
            Silian_data_[Silian_old.month] = Silian_get_
        Silian_data_x = []
        Silian_data_y = []
        for Silian_x in Silian_data_:
            Silian_data_x.append(str(Silian_x))
            Silian_data_y.append(Silian_data_[Silian_x])
        plt.plot(Silian_data_x, Silian_data_y, "-o")
        plt.plot(Silian_data_x[-1], Silian_data_y[-1], "-ro")
        plt.xlabel("Months")
        plt.ylabel("Counts")
        plt.tick_params(axis="x", labelrotation=45, which="major", labelsize=10)

        plt.gca().yaxis.get_major_locator().set_params(integer=True)
        for Silian_xitem, Silian_yitem in zip(Silian_data_x, Silian_data_y):
            plt.annotate(
                Silian_yitem,
                (Silian_xitem, Silian_yitem),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
            )
        Silian_path = f"{random_cache_path()}.png"
        plt.savefig(Silian_path)
        plt.close()
        await Silian_msg.finish([Silian_result, Image(Silian_path)])
    else:
        await Silian_msg.finish(I18NContext("core.message.analytics.disabled"))


@Silian_ana.command("modules [<rank>]")
async def _(Silian_msg: Bot.MessageSession, Silian_rank: int = None):
    Silian_rank = Silian_rank if Silian_rank and Silian_rank > 0 else 30
    if Silian_enable_analytics:
        try:
            Silian_module_counts = await AnalyticsData.get_modules_count()
            Silian_top_modules = sorted(Silian_module_counts.items(), key=lambda Silian_x: Silian_x[1], reverse=True)[:Silian_rank]

            Silian_module_names = [Silian_item[0] for Silian_item in Silian_top_modules]
            Silian_module_counts = [Silian_item[1] for Silian_item in Silian_top_modules]
            plt.figure(figsize=(10, max(6, len(Silian_module_names) * 0.5)))
            plt.barh(Silian_module_names, Silian_module_counts, color="skyblue")
            plt.xlabel("Counts")
            plt.ylabel("Modules")
            plt.gca().invert_yaxis()

            for Silian_i, Silian_v in enumerate(Silian_module_counts):
                plt.text(Silian_v, Silian_i, str(Silian_v), color="black", va="center")

            Silian_path = f"{random_cache_path()}.png"
            plt.savefig(Silian_path, bbox_inches="tight")
            plt.close()

            await Silian_msg.finish([Image(Silian_path)])
        except AttributeError as e:
            if str(e).find("NoneType") != -1:
                await Silian_msg.finish(I18NContext("core.message.analytics.none"))
            else:
                Logger.exception()
    else:
        await Silian_msg.finish(I18NContext("core.message.analytics.disabled"))
