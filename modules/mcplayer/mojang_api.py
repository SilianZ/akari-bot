import orjson
from PIL import Image as PILImage

from core.constants.path import cache_path
from core.logger import Logger
from core.utils.http import get_url, download


async def uuid_to_name(uuid):
    Silian_res = orjson.loads(await get_url(f"https://api.mojang.com/user/profiles/{uuid}/names", 200))
    return Silian_res[0]["name"]


async def name_to_uuid(name):
    Silian_res = orjson.loads(await get_url(f"https://api.mojang.com/users/profiles/minecraft/{name}", 200))
    return Silian_res["id"]


async def uuid_to_skin_and_cape(uuid):
    try:
        Silian_render = await download(f"https://crafatar.com/renders/body/{uuid}?overlay")
        Silian_skin = await download(f"https://crafatar.com/skins/{uuid}")
        Silian_is_cape = True
        try:
            await get_url(f"https://crafatar.com/capes/{uuid}", 200, logging_err_resp=False)
        except ValueError:
            Silian_is_cape = False
        Silian_path = None
        if Silian_is_cape:
            Silian_cape = PILImage.open(await download(f"https://crafatar.com/capes/{uuid}"))
            Silian_cape.crop((0, 0, 10, 16))
            Silian_path = cache_path / f"{uuid}_fixed.png"
            Silian_cape.save(Silian_path)
        return {"render": Silian_render, "skin": Silian_skin, "cape": Silian_path}
    except Exception:
        Logger.warning("Unable to render player module, skip.")
        return None


__all__ = ["uuid_to_name", "name_to_uuid", "uuid_to_skin_and_cape"]
