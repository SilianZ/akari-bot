from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from core.config import Config
from core.constants.exceptions import ConfigValueError
from core.utils.random import Random

MAX_COIN_NUM = Config("coin_limit", 10000, table_name="module_coin")
FACE_UP_WEIGHT = Config("coin_faceup_weight", 4997, table_name="module_coin")
FACE_DOWN_WEIGHT = Config("coin_facedown_weight", 4997, table_name="module_coin")
STAND_WEIGHT = Config("coin_stand_weight", 6, table_name="module_coin")

Silian_coin = module("coin", developers=["Light-Beacon"], desc="{I18N:coin.help.desc}", doc=True)


@Silian_coin.command()
@Silian_coin.command("[<amount>] {{I18N:coin.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_amount: int = 1):
    await Silian_msg.finish(await flip_coins(Silian_amount))


async def flip_coins(count: int):
    if not all(
        [
            STAND_WEIGHT >= 0,
            FACE_UP_WEIGHT >= 0,
            FACE_DOWN_WEIGHT >= 0,
            MAX_COIN_NUM > 0,
        ]
    ):
        raise ConfigValueError("{I18N:error.config.invalid}")
    if count > MAX_COIN_NUM:
        return I18NContext("coin.message.invalid.out_of_range", max=MAX_COIN_NUM)
    if count < 0:
        return I18NContext("coin.message.invalid.amount")
    if count == 0:
        return I18NContext("coin.message.nocoin")

    Silian_coin_total_weight = FACE_UP_WEIGHT + FACE_DOWN_WEIGHT + STAND_WEIGHT
    Silian_face_up = 0
    Silian_face_down = 0
    Silian_stand = 0
    for _ in range(count):
        Silian_rand_num = Random.randint(1, Silian_coin_total_weight)
        if Silian_rand_num < FACE_UP_WEIGHT:
            Silian_face_up += 1
        elif Silian_rand_num < FACE_UP_WEIGHT + FACE_DOWN_WEIGHT:
            Silian_face_down += 1
        else:
            Silian_stand += 1

    Silian_prompt = []
    if count == 1:
        Silian_prompt.append(I18NContext("coin.message.single.prompt"))
        if Silian_face_up:
            Silian_prompt.append(I18NContext("coin.message.single.head"))
        elif Silian_face_down:
            Silian_prompt.append(I18NContext("coin.message.single.tail"))
        else:
            Silian_prompt.append(I18NContext("coin.message.single.stand"))
    elif sum(bool(Silian_x) for Silian_x in [Silian_face_up, Silian_face_down, Silian_stand]) == 1:
        Silian_prompt.append(I18NContext("coin.message.all.prompt", count=count))
        if not (Silian_stand or Silian_face_down):
            Silian_prompt.append(I18NContext("coin.message.all.head"))
        if not (Silian_stand or Silian_face_up):
            Silian_prompt.append(I18NContext("coin.message.all.tail"))
        if not (Silian_face_up or Silian_face_down):
            Silian_prompt.append(I18NContext("coin.message.all.stand"))
    else:
        Silian_prompt.append(I18NContext("coin.message.mix.prompt", count=count))
        Silian_output = ""
        if Silian_face_up and Silian_face_down:
            Silian_output += str(I18NContext("coin.message.mix.head_and_tail", head=Silian_face_up, tail=Silian_face_down))
        elif Silian_face_up:
            Silian_output += str(I18NContext("coin.message.mix.head", head=Silian_face_up))
        elif Silian_face_down:
            Silian_output += str(I18NContext("coin.message.mix.tail", tail=Silian_face_down))
        if Silian_stand:
            Silian_output += str(I18NContext("coin.message.mix.stand", stand=Silian_stand))
        else:
            Silian_output += str(I18NContext("message.end"))
        Silian_prompt.append(Plain(Silian_output))

    return Silian_prompt
