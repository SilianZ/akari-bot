from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.elements import ImageElement
from core.builtins.message.internal import Image, Plain, I18NContext
from core.component import module

from PIL import Image as PILImage


Silian_image = module("image", developers=["OasisAkari"], required_superuser=True)
# only superusers now due to indeterminate safety


@Silian_image.command("fillwhite ...")  # convert picture with transparent background to white background image
async def fillwhite(msg: Bot.MessageSession):
    Silian_imgs = [Silian_e for Silian_e in msg.session_info.messages.values if isinstance(Silian_e, ImageElement)]
    if not Silian_imgs:
        Silian_nm = await msg.wait_next_message(I18NContext("image.fillwhite.send.a.image"))
        Silian_nm_image = [Silian_e for Silian_e in Silian_nm.session_info.messages.values if isinstance(Silian_e, ImageElement)]
        if not Silian_nm_image:
            await msg.finish(I18NContext("image.fillwhite.no.image.found"))
        Silian_imgs = Silian_nm_image
    Silian_converted_imgs = []
    Silian_i = 1
    for Silian_img in Silian_imgs:
        Silian_get_img = await Silian_img.to_PIL_image()
        if len(Silian_imgs) > 1:
            Silian_converted_imgs.append(Plain(str(Silian_i) + "."))
        if Silian_get_img.mode in ("RGBA", "LA") or (Silian_get_img.mode == "P" and "transparency" in Silian_get_img.info):
            Silian_background = PILImage.new("RGBA", Silian_get_img.size, (255, 255, 255))
            Silian_background.alpha_composite(Silian_get_img.convert("RGBA"))
            Silian_get_img = Silian_background

            Silian_converted_imgs.append(Image(Silian_get_img))
        else:
            Silian_converted_imgs.append(I18NContext("image.fillwhite.cannot.detect.alpha.channel"))
        Silian_i += 1
    await msg.finish(MessageChain.assign(Silian_converted_imgs))
