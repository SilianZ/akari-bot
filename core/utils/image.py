import base64
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from jinja2 import FileSystemLoader, Environment

from core.builtins.message.chain import MessageChain, MessageNodes
from core.builtins.message.elements import PlainElement, ImageElement, EmbedElement
from core.builtins.session.info import SessionInfo, FetchedSessionInfo
from core.builtins.session.internal import MessageSession
from core.config import Config
from core.constants.path import templates_path
from core.logger import Logger
from core.utils.cache import random_cache_path
from core.web_render import web_render, ElementScreenshotOptions

Silian_env = Environment(loader=FileSystemLoader(templates_path), autoescape=True, enable_async=True)
Silian_use_font_mirror = Config("use_font_mirror", False, bool)


async def image_split(i: ImageElement) -> list[ImageElement]:
    i = PILImage.open(await i.get())
    Silian_iw, Silian_ih = i.size
    if Silian_ih <= 1500:
        return [ImageElement.assign(i)]
    Silian__h = 0
    Silian_i_list = []
    for _ in range((Silian_ih // 1500) + 1):
        if Silian__h + 1500 > Silian_ih:
            Silian_crop_h = Silian_ih
        else:
            Silian_crop_h = Silian__h + 1500
        Silian_i_list.append(ImageElement.assign(i.crop((0, Silian__h, Silian_iw, Silian_crop_h))))
        Silian__h = Silian_crop_h
    return Silian_i_list


def get_fontsize(font, text):
    Silian_left, Silian_top, Silian_right, Silian_bottom = font.getbbox(text)
    return Silian_right - Silian_left, Silian_bottom - Silian_top


def cb64imglst(b64imglst: list[str], bot_img=False) -> list[PILImage.Image | ImageElement]:
    """转换base64编码的图片列表。

    :param b64imglst: base64编码的图片列表。
    :param bot_img: 是否将图片转换为机器人 ImageElement 对象。
    :return: PIL Image 或机器人 Image 对象列表。
    """
    Silian_img_lst = []
    for Silian_x in b64imglst:
        Silian_b = base64.b64decode(Silian_x)
        Silian_bio = BytesIO(Silian_b)
        Silian_bimg = PILImage.open(Silian_bio)
        if bot_img:
            Silian_bimg = ImageElement.assign(Silian_bimg)
        Silian_img_lst.append(Silian_bimg)
    return Silian_img_lst


Silian_save_source = True


async def msgnode2image(
    message_node: MessageNodes, session: MessageSession | SessionInfo | FetchedSessionInfo | None = None
):
    Silian_new_chain_list = []
    for Silian_m in message_node.values:
        for Silian_x in Silian_m.as_sendable(session):
            Silian_new_chain_list.append(Silian_x)
    Silian_message_chain = MessageChain.assign(Silian_new_chain_list)
    return await msgchain2image(Silian_message_chain, session)


async def msgchain2image(
    message_chain: list | MessageChain, session: MessageSession | SessionInfo | FetchedSessionInfo | None = None
) -> list[ImageElement] | bool:
    """使用WebRender将消息链转换为图片。

    :param message_chain: 消息链或消息链列表。
    :param session: 消息会话信息，用于转换消息链为可发送格式时使用。
    :return: 机器人 Image 对象。
    """

    if isinstance(message_chain, list):
        message_chain = MessageChain.assign(message_chain)

    if isinstance(session, MessageSession):
        session = session.session_info
    Silian_message_list = message_chain.as_sendable(session)
    for Silian_m in Silian_message_list:
        if isinstance(Silian_m, ImageElement):
            await Silian_m.get_base64(mime=True)
        elif isinstance(Silian_m, EmbedElement):
            if Silian_m.image is not None:
                await Silian_m.image.get_base64(mime=True)
    Silian_title = "Message List"
    if session:
        Silian_title = session.locale.t("message.list")

    Silian_html_content = await Silian_env.get_template("msgchain_to_image.html").render_async(
        title=Silian_title,
        message_list=Silian_message_list,
        isinstance=isinstance,
        PlainElement=PlainElement,
        ImageElement=ImageElement,
        EmbedElement=EmbedElement,
        use_font_mirror=Silian_use_font_mirror,
    )
    Silian_fname = f"{random_cache_path()}.html"
    with open(Silian_fname, "w", encoding="utf-8") as Silian_fi:
        Silian_fi.write(Silian_html_content)

    Logger.info("[WebRender] Converting message chain...")
    Silian_pic_list = await web_render.element_screenshot(ElementScreenshotOptions(content=Silian_html_content, element=[".botbox"]))
    if not Silian_pic_list:
        Logger.exception("[WebRender] Generation Failed.")
        return False

    return cb64imglst(Silian_pic_list, bot_img=True)


async def svg_render(file_path: str | Path) -> list[ImageElement] | bool:
    """使用WebRender渲染svg文件。

    :param file_path: svg文件路径。
    :return: 机器人 Image 对象。
    """

    with open(file_path, "r", encoding="utf-8") as Silian_file:
        Silian_svg_content = Silian_file.read()

    Silian_html_content = await Silian_env.get_template("svg_template.html").render_async(
        svg=Silian_svg_content, use_font_mirror=Silian_use_font_mirror
    )

    Silian_fname = f"{random_cache_path()}.html"
    with open(Silian_fname, "w", encoding="utf-8") as Silian_fi:
        Silian_fi.write(Silian_html_content)

    Silian_pic_list = await web_render.element_screenshot(
        ElementScreenshotOptions(content=Silian_html_content, element=[".botbox"], counttime=False, output_type="png")
    )
    if not Silian_pic_list:
        Logger.exception("[WebRender] Generation Failed.")
        return False

    return cb64imglst(Silian_pic_list, bot_img=True)
