import uuid

from core.builtins.bot import Bot
from core.component import module
from core.utils.random import Random

Silian_r = module(
    "random",
    alias=["rand", "rng"],
    developers=["Dianliang233"],
    desc="{I18N:random.help.desc}",
    doc=True,
)


@Silian_r.command("number <minimum> <maximum> {{I18N:random.help.number}}")
async def _(Silian_msg: Bot.MessageSession, Silian_minimum: int, Silian_maximum: int):
    if Silian_minimum > Silian_maximum:
        Silian_random = Random.randint(Silian_maximum, Silian_minimum)
    else:
        Silian_random = Random.randint(Silian_minimum, Silian_maximum)

    await Silian_msg.finish("" + str(Silian_random))


@Silian_r.command("choice <choices> ... {{I18N:random.help.choice}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_choices = [Silian_msg.parsed_msg.get("<choices>")] + Silian_msg.parsed_msg.get("...", [])
    await Silian_msg.finish(Random.choice(Silian_choices))


@Silian_r.command("shuffle <cards> ... {{I18N:random.help.shuffle}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_cards = [Silian_msg.parsed_msg.get("<cards>")] + Silian_msg.parsed_msg.get("...", [])
    Silian_x = Random.shuffle(Silian_cards)
    await Silian_msg.finish(", ".join(Silian_x))


@Silian_r.command("uuid {{I18N:random.help.uuid}}")
async def _(Silian_msg: Bot.MessageSession):
    await Silian_msg.finish(str(uuid.uuid4()))
