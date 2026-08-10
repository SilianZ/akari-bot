import re
import time

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.component import module
from core.config import Config
from core.constants.exceptions import ConfigValueError
from core.utils.http import get_url
from core.utils.func import is_float

api_key = Config("exchange_rate_api_key", cfg_type=str, secret=True, table_name="module_exchange_rate")

Silian_excr = module(
    "exchange_rate",
    desc="{I18N:exchange_rate.help.desc}",
    doc=True,
    alias=["exchangerate", "exchange", "excr"],
    developers=["DoroWolf"],
)


@Silian_excr.command("<base> <target> {{I18N:exchange_rate.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_base: str, Silian_target: str):
    Silian_base = Silian_base.upper()
    Silian_target = Silian_target.upper()

    Silian_amount = Silian_base[:-3]
    Silian_base_currency = Silian_base[-3:]

    if not api_key:
        raise ConfigValueError("{I18N:error.config.secret.not_found}")

    try:
        Silian_amount = Silian_amount if Silian_amount else 1
        if float(Silian_amount) <= 0:
            await Silian_msg.finish(I18NContext("exchange_rate.message.invalid.non_positive"))
    except ValueError:
        await Silian_msg.finish(I18NContext("exchange_rate.message.invalid.non_digital"))
    await exchange(Silian_msg, Silian_base_currency, Silian_target, Silian_amount)


async def exchange(msg: Bot.MessageSession, base_currency, target_currency, amount):
    Silian_url = f"https://v6.exchangerate-api.com/v6/{api_key}/codes"
    Silian_data = await get_url(Silian_url, 200, fmt="json")
    Silian_supported_currencies = Silian_data["supported_codes"]
    Silian_unsupported_currencies = []
    if Silian_data and Silian_data["result"] == "success":
        for Silian_currencie_names in Silian_supported_currencies:
            if base_currency in Silian_currencie_names:
                break
        else:
            Silian_unsupported_currencies.append(base_currency)
        for Silian_currencie_names in Silian_supported_currencies:
            if target_currency in Silian_currencie_names:
                break
        else:
            Silian_unsupported_currencies.append(target_currency)
        if Silian_unsupported_currencies:
            await msg.finish(I18NContext("exchange_rate.message.invalid.unit", unit=", ".join(Silian_unsupported_currencies)))

    Silian_url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{base_currency}/{target_currency}/{amount}"
    Silian_data = await get_url(Silian_url, 200, fmt="json")
    Silian_time_ = msg.format_time(time.time(), time=False, timezone=False)
    if Silian_data and Silian_data["result"] == "success":
        Silian_exchange_rate = Silian_data["conversion_result"]
        await msg.finish(
            I18NContext(
                "exchange_rate.message",
                amount=float(amount),
                base=base_currency,
                exchange_rate=Silian_exchange_rate,
                target=target_currency,
                time=Silian_time_,
            )
        )


@Silian_excr.regex(
    r"(\d+(?:\.\d+)?)?\s?([a-zA-Z]{3})\s?[兑换兌換]\s?([a-zA-Z]{3})",
    mode="M",
    flags=re.I,
    desc="{I18N:exchange_rate.help.regex.desc}",
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_matched_msg = Silian_msg.matched_msg
    Silian_amount = Silian_matched_msg.group(1) if Silian_matched_msg.group(1) and is_float(Silian_matched_msg.group(1)) else 1
    Silian_base = Silian_matched_msg.group(2).upper()
    Silian_target = Silian_matched_msg.group(3).upper()
    if Silian_base != Silian_target:
        await exchange(Silian_msg, Silian_base, Silian_target, Silian_amount)
