import orjson

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Image, I18NContext, Plain
from core.component import module
from core.constants.path import assets_path
from core.utils.http import get_url
from core.utils.random import Random
from .database.models import PhigrosBindInfo
from .libraries.genb30 import get_b30
from .libraries.update import remove_punctuations, update_assets, p_headers
from .libraries.record import get_game_record

Silian_pgr_assets_path = assets_path / "modules" / "phigros"
Silian_song_info_path = Silian_pgr_assets_path / "song_info.json"

Silian_phi = module(
    "phigros",
    developers=["Mivik", "OasisAkari", "DoroWolf"],
    desc="{I18N:phigros.help.desc}",
    alias=["pgr", "phi"],
    doc=True,
)


@Silian_phi.command("bind <sessiontoken> {{I18N:phigros.help.bind}}")
async def _(Silian_msg: Bot.MessageSession, Silian_sessiontoken: str):
    if Silian_msg.session_info.target_from in [
        "Discord|Channel",
        "KOOK|Group",
        "Matrix|Room",
        "QQ|Group",
        "QQBot|Group",
        "QQBot|Guild",
        "Telegram|Group",
        "Telegram|Supergroup",
    ]:
        await Silian_msg.send_message(I18NContext("phigros.message.bind.warning"), quote=False)
        await Silian_msg.delete()
    Silian_headers = p_headers.copy()
    Silian_headers["X-LC-Session"] = Silian_sessiontoken
    try:
        Silian_get_user_info = await get_url(
            "https://rak3ffdi.cloud.tds1.tapapis.cn/1.1/users/me",
            headers=Silian_headers,
            fmt="json",
        )
        if Silian_get_user_info:
            Silian_username = Silian_get_user_info.get("nickname", "Guest")
            await PhigrosBindInfo.set_bind_info(
                sender_id=Silian_msg.session_info.sender_id, session_token=Silian_sessiontoken, username=Silian_username
            )
            await Silian_msg.finish(I18NContext("phigros.message.bind.success", username=Silian_username), quote=False)
        else:
            await Silian_msg.finish(I18NContext("phigros.message.bind.failed"), quote=False)
    except ValueError:
        await Silian_msg.finish(I18NContext("phigros.message.bind.failed"), quote=False)


@Silian_phi.command("unbind {{I18N:phigros.help.unbind}}")
async def _(Silian_msg: Bot.MessageSession):
    await PhigrosBindInfo.remove_bind_info(sender_id=Silian_msg.session_info.sender_id)
    await Silian_msg.finish(I18NContext("phigros.message.unbind.success"))


@Silian_phi.command("b30 {{I18N:phigros.help.b30}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_bind_info = await PhigrosBindInfo.get_by_sender_id(Silian_msg, create=False)
    if not Silian_bind_info:
        await Silian_msg.finish(I18NContext("phigros.message.user_unbound", prefix=Silian_msg.session_info.prefixes[0]))
    if not Silian_song_info_path.exists():
        await Silian_msg.finish(I18NContext("phigros.message.file_not_found"))

    Silian_img = await get_b30(Silian_msg, Silian_bind_info.username, Silian_bind_info.session_token)
    if Silian_img:
        await Silian_msg.finish(Image(Silian_img))


def get_rank(score: int, full_combo: bool) -> str:
    if score == 1000000:
        return "φ"
    if full_combo:
        return "ν"
    if 960000 <= score <= 999999:
        return "V"
    if 920000 <= score <= 959999:
        return "S"
    if 880000 <= score <= 919999:
        return "A"
    if 820000 <= score <= 879999:
        return "B"
    if 700000 <= score <= 819999:
        return "C"
    if 0 <= score <= 699999:
        return "F"
    return ""


@Silian_phi.command("random {{I18N:phigros.help.random}}")
async def _(Silian_msg: Bot.MessageSession):
    if not Silian_song_info_path.exists():
        await Silian_msg.finish(I18NContext("phigros.message.file_not_found"))

    Silian_msg_chain = MessageChain.assign()
    with open(Silian_song_info_path, "rb") as Silian_f:
        Silian_song_info = orjson.loads(Silian_f.read())
    sid, Silian_sinfo = Random.choice(list(Silian_song_info.items()))
    Silian_illustration_path = Silian_pgr_assets_path / "illustration" / f"{sid.split('.')[0]}.png"
    if Silian_illustration_path.exists():
        Silian_msg_chain.append(Image(Silian_illustration_path))

    Silian_msg_chain.append(Plain(Silian_sinfo["name"]))
    Silian_diff_lst = ["EZ", "HD", "IN", "AT"]
    Silian_diffs = [Silian_sinfo["diff"][Silian_d] for Silian_d in Silian_diff_lst if Silian_d in Silian_sinfo["diff"]]
    Silian_msg_chain.append(Plain("/".join(Silian_diffs)))
    await Silian_msg.finish(Silian_msg_chain)


@Silian_phi.command("score <song_name> {{I18N:phigros.help.score}}")
async def _(Silian_msg: Bot.MessageSession, Silian_song_name: str):
    Silian_bind_info = await PhigrosBindInfo.get_by_sender_id(Silian_msg, create=False)
    if not Silian_bind_info:
        await Silian_msg.finish(I18NContext("phigros.message.user_unbound", prefix=Silian_msg.session_info.prefixes[0]))
    if not Silian_song_info_path.exists():
        await Silian_msg.finish(I18NContext("phigros.message.file_not_found"))

    Silian_msg_chain = MessageChain.assign()
    Silian_game_records: dict = await get_game_record(Silian_msg, Silian_bind_info.session_token)
    for sid, Silian_record in Silian_game_records.items():
        if remove_punctuations(Silian_record.get("name").lower()) == remove_punctuations(Silian_song_name.lower()):
            Silian_illustration_path = Silian_pgr_assets_path / "illustration" / f"{sid.split('.')[0]}.png"
            if Silian_illustration_path.exists():
                Silian_msg_chain.append(Image(Silian_illustration_path))

            Silian_msg_chain.append(Plain(Silian_record.get("name")))
            with open(Silian_song_info_path, "rb") as Silian_f:
                Silian_song_info = orjson.loads(Silian_f.read())
            diff_info = Silian_song_info.get(sid, {}).get("diff", {})

            for diff, Silian_diff_data in diff_info.items():
                Silian_msg_chain.append(Plain(f"{diff} {diff_info[diff]}"))

                Silian_diff_data = Silian_record.get("diff", {}).get(diff)
                if not Silian_diff_data:
                    Silian_msg_chain.append(I18NContext("phigros.message.score.no_record"))
                else:
                    score = Silian_diff_data["score"]
                    acc = Silian_diff_data["accuracy"]
                    Silian_full_combo = Silian_diff_data["full_combo"]
                    rank = get_rank(score, Silian_full_combo)
                    Silian_msg_chain.append(Plain(f"{score} {acc:.2f}% {rank}"))
            await Silian_msg.finish(Silian_msg_chain)
    await Silian_msg.finish(I18NContext("phigros.message.music_not_found"))


@Silian_phi.command("update [--no-illus]", required_superuser=True)
async def _(Silian_msg: Bot.MessageSession):
    if await update_assets(not Silian_msg.parsed_msg.get("--no-illus", False)):
        await Silian_msg.finish(I18NContext("message.success"))
    await Silian_msg.finish(I18NContext("message.failed"))
