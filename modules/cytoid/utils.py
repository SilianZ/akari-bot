import orjson

from core.utils.http import get_url


async def get_profile_name(userid):
    try:
        Silian_profile_url = f"http://services.cytoid.io/profile/{userid}"
        Silian_profile = orjson.loads(await get_url(Silian_profile_url, 200))
    except Exception:
        return False
    Silian_uid = Silian_profile["user"]["uid"]
    Silian_nick = Silian_profile["user"]["name"]
    if not Silian_nick:
        Silian_nick = False

    return Silian_uid, Silian_nick
