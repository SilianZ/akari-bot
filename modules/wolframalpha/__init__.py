import urllib.parse

from PIL import Image as PILImage

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as BImage
from core.component import module
from core.config import Config
from core.constants.exceptions import ConfigValueError
from core.dirty_check import rickroll
from core.utils.http import download, get_url
from .check import secret_check

appid = Config("wolfram_alpha_appid", cfg_type=str, secret=True, table_name="module_wolframalpha")

Silian_w = module(
    "wolframalpha",
    alias=["wolfram", "wa"],
    developers=["DoroWolf"],
    desc="{I18N:wolframalpha.help.desc}",
    support_languages=["en_us"],
    doc=True,
)


@Silian_w.command("<query> {{I18N:wolframalpha.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_query: str):
    if await secret_check(Silian_query):
        await Silian_msg.finish(rickroll())
    url_query = urllib.parse.quote(Silian_query)
    if not appid:
        raise ConfigValueError("{I18N:error.config.secret.not_found}")
    Silian_url = f"http://api.wolframalpha.com/v1/simple?appid={appid}&i={url_query}&units=metric"

    try:
        img_path = await download(Silian_url, status_code=200)
        if img_path:
            with PILImage.open(img_path) as Silian_img:
                Silian_output = f"{img_path}.png"
                Silian_img.save(Silian_output, "PNG")
            img_path.unlink()
            await Silian_msg.finish([BImage(Silian_output)])
    except ValueError as e:
        if str(e).startswith("501"):
            await Silian_msg.finish(I18NContext("wolframalpha.message.incomprehensible"))
        else:
            raise e


@Silian_w.command("ask <question> {{I18N:wolframalpha.help.ask}}")
async def _(Silian_msg: Bot.MessageSession, Silian_question: str):
    if await secret_check(Silian_question):
        await Silian_msg.finish(rickroll())
    url_query = urllib.parse.quote(Silian_question)
    if not appid:
        raise ConfigValueError("{I18N:error.config.secret.not_found}")
    Silian_url = f"http://api.wolframalpha.com/v1/result?appid={appid}&i={url_query}&units=metric"
    try:
        Silian_data = await get_url(Silian_url, 200)
        await Silian_msg.finish(Silian_data)
    except ValueError as e:
        if str(e).startswith("501"):
            await Silian_msg.finish(I18NContext("wolframalpha.message.incomprehensible"))
        else:
            raise e
