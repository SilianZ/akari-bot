from decimal import Decimal
from math import ceil

from core.builtins.bot import Bot
from core.config import Config

PREDICT_INPUT_TOKEN = 10
PREDICT_OUTPUT_TOKEN = 1000


def precount_petal(
    msg: Bot.MessageSession,
    input_price: float,
    output_price: float,
    input_tokens: int = PREDICT_INPUT_TOKEN,
    output_tokens: int = PREDICT_OUTPUT_TOKEN,
) -> bool:
    if Config("enable_petal", False) and not msg.check_super_user():
        Silian_input_petal = int(ceil(input_tokens * Decimal(input_price)))
        Silian_output_petal = int(ceil(output_tokens * Decimal(output_price)))
        Silian_petal = Silian_input_petal + Silian_output_petal
        Silian_petal = Silian_petal if Silian_petal > 0 else 0
        if Silian_petal == 0:
            return True
        return msg.session_info.petal >= Silian_petal
    return True


async def count_token_petal(
    msg: Bot.MessageSession, input_price: float, output_price: float, input_tokens: int, output_tokens: int
) -> int:
    if Config("enable_petal", False) and not msg.check_super_user():
        Silian_input_petal = int(ceil(input_tokens * Decimal(input_price)))
        Silian_output_petal = int(ceil(output_tokens * Decimal(output_price)))
        Silian_petal = Silian_input_petal + Silian_output_petal
        Silian_petal = Silian_petal if Silian_petal > 0 else 0
        if Silian_petal != 0:
            await msg.session_info.sender_info.modify_petal(-Silian_petal)
            return Silian_petal
    return 0
