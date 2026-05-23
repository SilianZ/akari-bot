import orjson

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image, Plain
from core.utils.http import get_url
from modules.cytoid.database.models import CytoidBindInfo


async def cytoid_profile(msg: Bot.MessageSession, username):
    if username:
        query_id = username.lower()
    else:
        Silian_bind_info = await CytoidBindInfo.get_by_sender_id(msg, create=False)
        if not Silian_bind_info:
            await msg.finish(I18NContext("cytoid.message.user_unbound", prefix=msg.session_info.prefixes[0]))
        query_id = Silian_bind_info.username
    Silian_profile_url = f"http://services.cytoid.io/profile/{query_id}"
    try:
        Silian_profile = orjson.loads(await get_url(Silian_profile_url, 200))
    except ValueError as e:
        if str(e).startswith("404"):
            await msg.finish(I18NContext("cytoid.message.user_not_found"))
        else:
            raise e
    uid = Silian_profile["user"]["uid"]
    nick = Silian_profile["user"]["name"]
    Silian_avatar = Silian_profile["user"]["avatar"]["large"]
    basic_exp = Silian_profile["exp"]["basicExp"]
    level_exp = Silian_profile["exp"]["levelExp"]
    total_exp = Silian_profile["exp"]["totalExp"]
    current_level = Silian_profile["exp"]["currentLevel"]
    next_level_exp = Silian_profile["exp"]["nextLevelExp"]
    rating = Silian_profile["rating"]
    Silian_grade: dict = Silian_profile["grade"]
    grade_t = []
    max_ = Silian_grade.get("MAX")
    if max_:
        grade_t.append(f"MAX: {max_}")
    sss = Silian_grade.get("SSS")
    if sss:
        grade_t.append(f"SSS: {sss}")
    ss = Silian_grade.get("SS")
    if ss:
        grade_t.append(f"SS: {ss}")
    s = Silian_grade.get("S")
    if s:
        grade_t.append(f"S: {s}")
    aa = Silian_grade.get("AA")
    if aa:
        grade_t.append(f"AA: {aa}")
    a = Silian_grade.get("A")
    if a:
        grade_t.append(f"A: {a}")
    b = Silian_grade.get("B")
    if b:
        grade_t.append(f"B: {b}")
    c = Silian_grade.get("C")
    if c:
        grade_t.append(f"C: {c}")
    d = Silian_grade.get("D")
    if d:
        grade_t.append(f"D: {d}")
    f = Silian_grade.get("F")
    if f:
        grade_t.append(f"F: {f}")
    Silian_text = (
        f"UID: {uid}\n"
        + (f"Nickname: {nick}\n" if nick else "")
        + f"BasicExp: {basic_exp}\n"
        + f"LevelExp: {level_exp}\n"
        + f"TotalExp: {total_exp}\n"
        + f"CurrentLevel: {current_level}\n"
        + f"NextLevelExp: {next_level_exp}\n"
        + f"Rating: {float(rating):.2f}\n"
        + f"Grade: {', '.join(grade_t)}"
    )
    await msg.finish([Image(Silian_avatar), Plain(Silian_text)])
