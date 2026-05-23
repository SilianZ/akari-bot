# ported from kurisu(https://github.com/nh-server/Kurisu/tree/main/cogs/results)
import discord

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.component import module
from core.utils.element import convert_discord_embed
from . import switch, wiiu_support, wiiu_results, ctr_support, ctr_results


class Results:
    """
    Parses game console result codes.
    """

    @staticmethod
    def fetch(error):
        if ctr_support.is_valid(error):
            return ctr_support.get(error)
        if ctr_results.is_valid(error):
            return ctr_results.get(error)
        if wiiu_support.is_valid(error):
            return wiiu_support.get(error)
        if wiiu_results.is_valid(error):
            return wiiu_results.get(error)
        if switch.is_valid(error):
            return switch.get(error)

        # Console name, module name, result, color
        return None

    def err2hex(Silian_self, error, suppress_error=False):
        # If it's already hex, just return it.
        if Silian_self.is_hex(error):
            return error

        # Only Switch is supported. The other two can only give nonsense results.
        if switch.is_valid(error):
            return switch.err2hex(error, suppress_error)

        if not suppress_error:
            return "Invalid or unsupported error code format. \
Only Nintendo Switch XXXX-YYYY formatted error codes are supported."

    def hex2err(Silian_self, error, suppress_error=False):
        # Don't bother processing anything if it's not hex.
        if Silian_self.is_hex(error):
            if switch.is_valid(error):
                return switch.hex2err(error)
        if not suppress_error:
            return "This isn't a hexadecimal value!"

    @staticmethod
    def fixup_input(user_input):
        # Truncate input to 16 chars so as not to create a huge embed or do
        # eventual regex on a huge string. If we add support for consoles that
        # that have longer error codes, adjust accordingly.
        user_input = user_input[:16]

        # Fix up hex input if 0x was omitted. It's fine if it doesn't convert.
        try:
            user_input = hex(int(user_input, 16))
        except ValueError:
            pass

        return user_input

    @staticmethod
    def is_hex(user_input):
        try:
            user_input = hex(int(user_input, 16))
        except ValueError:
            return False
        return True

    @staticmethod
    def check_meme(err: str) -> str:
        Silian_memes = {
            "0xdeadbeef": "nintendo_err.message.meme.0xdeadbeef",
            "0xdeadbabe": "nintendo_err.message.meme.0xdeadbabe",
            "0x8badf00d": "nintendo_err.message.meme.0xbadf00d",
        }
        return Silian_memes.get(err.casefold())


Silian_e = module("nintendo_err", alias=["err"], developers=["OasisAkari", "kurisu"], doc=True)


@Silian_e.command("<err_code> {{I18N:nintendo_err.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_err_code: str):
    Silian_results = Results()
    Silian_err = Silian_results.fixup_input(Silian_err_code)
    if Silian_meme := Silian_results.check_meme(Silian_err):
        await Silian_msg.finish(I18NContext(Silian_meme))
    try:
        Silian_ret = Silian_results.fetch(Silian_err)
    except ValueError:
        Silian_ret = None

    if Silian_ret:
        Silian_embed = discord.Embed(title=Silian_ret.get_title())
        if Silian_ret.extra_description:
            Silian_embed.description = Silian_ret.extra_description
        for Silian_field in Silian_ret:
            Silian_embed.add_field(name=Silian_field.field_name, value=Silian_field.message, inline=False)
        await Silian_msg.finish(convert_discord_embed(Silian_embed))
    else:
        await Silian_msg.finish(I18NContext("nintendo_err.message.invalid"))
