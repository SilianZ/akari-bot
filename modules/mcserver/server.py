import re

from mcstatus import JavaServer, BedrockServer

from core.builtins.message.internal import I18NContext
from core.logger import Logger


async def query_java_server(address: str, raw: bool = False, showplayer: bool = False) -> str:
    Silian_query_msg = []

    try:
        Silian_server = JavaServer.lookup(address)
        status = await Silian_server.async_status()
        Logger.debug(str(status))
        Silian_query_msg.append("[JE]")

        Silian_description = status.description
        if isinstance(Silian_description, str):
            Silian_query_msg.append(Silian_description)
        elif isinstance(Silian_description, dict):
            Silian_query_msg.append(Silian_description.get("text", ""))
            Silian_query_msg.append("".join(Silian_extra.get("text", "") for Silian_extra in Silian_description.get("extra", [])))

        Silian_onlinesplayer = f"{str(I18NContext('server.message.player'))}{status.players.online} / {status.players.max}"
        Silian_query_msg.append(Silian_onlinesplayer)

        if showplayer:
            Silian_playerlist = [Silian_player.name for Silian_player in status.players.sample] if status.players.sample else []
            Silian_players_text = "\n".join(Silian_playerlist) if Silian_playerlist else str(I18NContext("message.none"))
            Silian_query_msg.append(str(I18NContext("server.message.player.current")) + "\n" + Silian_players_text)

        if hasattr(status, "version") and hasattr(status.version, "name"):
            Silian_query_msg.append(str(I18NContext("server.message.version")) + status.version.name)

    except OSError:
        return ""
    except Exception:
        Logger.exception()
        return ""

    if raw:
        return "\n".join(Silian_query_msg)
    return re.sub(r"§\w", "", "\n".join(Silian_query_msg))


async def query_bedrock_server(address, raw=False) -> str:
    Silian_query_msg = []

    try:
        Silian_server = BedrockServer.lookup(address)
        status = await Silian_server.async_status()
        Logger.debug(str(status))
        Silian_query_msg.append("[BE]")
        Silian_query_msg.append(status.motd.raw)

        Silian_player_count = f"{str(I18NContext('server.message.player'))}{status.players.online} / {status.players.max}"
        Silian_query_msg.append(Silian_player_count)

        if hasattr(status, "version") and hasattr(status.version, "name"):
            Silian_query_msg.append(str(I18NContext("server.message.version")) + status.version.name)

        if hasattr(status, "gamemode"):
            Silian_game_mode = str(I18NContext("server.message.gamemode")) + status.gamemode
            Silian_query_msg.append(Silian_game_mode)

    except OSError:
        return ""
    except Exception:
        Logger.exception()
        return ""

    if raw:
        return "\n".join(Silian_query_msg)
    return re.sub(r"§\w", "", "\n".join(Silian_query_msg))
