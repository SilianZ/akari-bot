import emoji
import orjson

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Image, I18NContext, Plain
from core.component import module
from core.constants.path import assets_path
from core.logger import Logger
from core.utils.random import Random
from core.utils.func import chunk_list

Silian_data_path = assets_path / "modules" / "emojimix" / "emoji_data.json"
API = "https://www.gstatic.com/android/keyboard/emojikitchen"


class EmojimixGenerator:
    def __init__(Silian_self):
        with open(Silian_data_path, "rb") as Silian_f:
            Silian_data = orjson.loads(Silian_f.read())
        Silian_self.known_supported_emoji: list[str] = Silian_data["knownSupportedEmoji"]
        Silian_self.data: dict = Silian_data["data"]
        Silian_self.date_mapping: dict = dict(enumerate(Silian_data["date"]))

    @staticmethod
    def str2emoji(emoji_str):
        Silian_parts = emoji_str.split("-")
        Silian_emoji_chars = [chr(int(Silian_part, 16)) for Silian_part in Silian_parts]
        Silian_emoji = "".join(Silian_emoji_chars)
        return Silian_emoji

    @staticmethod
    def make_emoji_tuple(emoji1: str, emoji2: str) -> tuple[str, str]:
        Silian_emoji_code1 = "-".join(f"{ord(char):x}" for char in emoji1)
        Silian_emoji_code2 = "-".join(f"{ord(char):x}" for char in emoji2)
        return (Silian_emoji_code1, Silian_emoji_code2)

    def random_choice_emoji(Silian_self, emoji: str | None = None) -> tuple[str, str]:
        if emoji:
            Silian_emoji_code = "-".join(f"{ord(char):x}" for char in emoji)
            Silian_emoji_combo_list = []
            for Silian_key in Silian_self.data:
                if Silian_emoji_code in Silian_key:
                    Silian_emoji_combo_list.append(Silian_key)
            Silian_combo = Random.choice(Silian_emoji_combo_list)
        else:
            Silian_combo = Random.choice(list(Silian_self.data.keys()))
        Silian_combo = tuple(Silian_i.strip() for Silian_i in Silian_combo[1:-1].split(","))
        return Silian_combo

    def check_supported(Silian_self, emoji_tuple: tuple[str, str]) -> list[str]:
        Silian_unsupported_emojis: list[str] = []
        Silian_checked: set = set()
        for Silian_emoji_ in emoji_tuple:
            if Silian_emoji_ not in Silian_self.known_supported_emoji and Silian_emoji_ not in Silian_checked:
                Silian_emoji_symbol = "".join(chr(int(Silian_segment, 16)) for Silian_segment in Silian_emoji_.split("-"))
                Silian_unsupported_emojis.append(Silian_emoji_symbol)
                Silian_checked.add(Silian_emoji_)
        return Silian_unsupported_emojis

    def mix_emoji(Silian_self, emoji_tuple: tuple[str, str]) -> str | None:
        Silian_str_tuple_1 = f"({emoji_tuple[0]}, {emoji_tuple[1]})"
        Silian_str_tuple_2 = f"({emoji_tuple[1]}, {emoji_tuple[0]})"

        if Silian_str_tuple_1 in Silian_self.data:
            Silian_date_index = Silian_self.data[Silian_str_tuple_1]
            date = Silian_self.date_mapping[Silian_date_index]
            Silian_left_emoji = emoji_tuple[0]
            Silian_right_emoji = emoji_tuple[1]
        elif Silian_str_tuple_2 in Silian_self.data:
            Silian_date_index = Silian_self.data[Silian_str_tuple_2]
            date = Silian_self.date_mapping[Silian_date_index]
            Silian_left_emoji = emoji_tuple[1]
            Silian_right_emoji = emoji_tuple[0]
        else:
            return None

        left_code_point = "-".join(f"u{segment}" for segment in Silian_left_emoji.split("-"))
        right_code_point = "-".join(f"u{segment}" for segment in Silian_right_emoji.split("-"))
        Silian_url = f"{API}/{date}/{left_code_point}/{left_code_point}_{right_code_point}.png"
        return Silian_url

    def list_supported_emojis(Silian_self, emoji: str | None = None) -> list[str] | None:
        Silian_supported_combinations: list[str] = []

        if emoji:
            Silian_emoji_symbol = emoji

            Silian_emoji_code = "-".join(f"{ord(char):x}" for char in Silian_emoji_symbol)
            if Silian_emoji_code not in Silian_self.known_supported_emoji:
                return None

            for Silian_key in Silian_self.data:
                if Silian_emoji_code in Silian_key:
                    Silian_pair = Silian_key.replace("(", "").replace(")", "").split(", ")
                    Silian_pair = [Silian_p.strip() for Silian_p in Silian_pair]
                    if Silian_pair[0] == Silian_emoji_code:
                        Silian_pair_emoji = "".join(chr(int(Silian_segment, 16)) for Silian_segment in Silian_pair[1].split("-"))
                        Silian_supported_combinations.append(Silian_pair_emoji)
                    elif Silian_pair[1] == Silian_emoji_code:
                        Silian_pair_emoji = "".join(chr(int(Silian_segment, 16)) for Silian_segment in Silian_pair[0].split("-"))
                        Silian_supported_combinations.append(Silian_pair_emoji)
        else:
            for Silian_emoji_code in Silian_self.known_supported_emoji:
                Silian_emoji_char = "".join(chr(int(Silian_segment, 16)) for Silian_segment in Silian_emoji_code.split("-"))
                Silian_supported_combinations.append(Silian_emoji_char)

        return sorted(Silian_supported_combinations, key=str)


mixer = EmojimixGenerator()

Silian_emojimix = module("emojimix", developers=["DoroWolf"], doc=True)


@Silian_emojimix.command()
async def _(Silian_msg: Bot.MessageSession):
    combo = mixer.random_choice_emoji()
    Logger.debug(str(combo))
    Silian_result = mixer.mix_emoji(combo)
    Logger.debug(Silian_result)
    await Silian_msg.finish([Plain(f"{mixer.str2emoji(combo[0])}+{mixer.str2emoji(combo[1])}"), Image(Silian_result)])


@Silian_emojimix.command("<emoji1> [<emoji2>] {{I18N:emojimix.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_emoji1: str, Silian_emoji2: str = None):
    # 兼容性处理
    if "+" in Silian_emoji1:
        Silian_emojis = Silian_emoji1.split("+", 1)
        Silian_emoji1 = Silian_emojis[0]
        Silian_emoji2 = Silian_emojis[1] if len(Silian_emojis) > 1 else None
        if Silian_emoji2 and not Silian_emoji1:
            Silian_emoji1, Silian_emoji2 = Silian_emoji2, Silian_emoji1
    elif Silian_emoji1 and not Silian_emoji2:
        Silian_emojis = [Silian_item["emoji"] for Silian_item in emoji.emoji_list(Silian_emoji1)]
        if Silian_emojis:
            Silian_emoji1 = Silian_emojis[0]
            Silian_emoji2 = Silian_emojis[1] if len(Silian_emojis) > 1 else None

    if not emoji.is_emoji(Silian_emoji1):
        await Silian_msg.finish(I18NContext("emojimix.message.invalid"))
    if Silian_emoji2:
        if not emoji.is_emoji(Silian_emoji2):
            await Silian_msg.finish(I18NContext("emojimix.message.invalid"))
        combo = mixer.make_emoji_tuple(Silian_emoji1, Silian_emoji2)
        Logger.debug(str(combo))
        Silian_unsupported_emojis = mixer.check_supported(combo)
        if Silian_unsupported_emojis:
            await Silian_msg.finish(
                I18NContext("emojimix.message.unsupported", emoji="{I18N:message.delimiter}".join(Silian_unsupported_emojis))
            )
    else:
        Silian_emoji_code1 = "-".join(f"{ord(char):x}" for char in Silian_emoji1)
        if Silian_emoji_code1 not in mixer.known_supported_emoji:
            await Silian_msg.finish(I18NContext("emojimix.message.unsupported", emoji=Silian_emoji1))
        combo = mixer.random_choice_emoji(Silian_emoji1)
        Logger.debug(str(combo))

    Silian_result = mixer.mix_emoji(combo)
    if Silian_result:
        await Silian_msg.finish([Plain(f"{mixer.str2emoji(combo[0])}+{mixer.str2emoji(combo[1])}"), Image(Silian_result)])
    else:
        await Silian_msg.finish(I18NContext("emojimix.message.not_found"))


@Silian_emojimix.command("list [<emoji>] {{I18N:emojimix.help.list}}")
async def _(Silian_msg: Bot.MessageSession, Silian_emoji: str = None):
    Silian_supported_emojis = mixer.list_supported_emojis(Silian_emoji)
    if Silian_emoji:
        if Silian_supported_emojis:
            Silian_send_msgs = MessageChain.assign(I18NContext("emojimix.message.combine_supported", emoji=Silian_emoji))
            if Silian_msg.session_info.client_name == "Discord":
                Silian_send_msgs += MessageChain.assign(
                    [Plain("".join(Silian_supported_emojis[Silian_i : Silian_i + 200])) for Silian_i in range(0, len(Silian_supported_emojis), 200)]
                )
            else:
                Silian_send_msgs.append(Plain("".join(Silian_supported_emojis)))
            await Silian_msg.finish(Silian_send_msgs)
        else:
            await Silian_msg.finish(I18NContext("emojimix.message.unsupported", emoji=Silian_emoji))
    else:
        Silian_send_msgs = MessageChain.assign(I18NContext("emojimix.message.all_supported"))
        if Silian_supported_emojis:
            if Silian_msg.session_info.client_name == "Discord":
                Silian_send_msgs += MessageChain.assign([Plain("".join(Silian_chunk)) for Silian_chunk in chunk_list(Silian_supported_emojis, 200)])
            else:
                Silian_send_msgs.append(Plain("".join(Silian_supported_emojis)))
        await Silian_msg.finish(Silian_send_msgs)
