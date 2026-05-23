import asyncio
import re

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext
from core.component import module
from core.dirty_check import check
from .server import query_java_server, query_bedrock_server

Silian_s = module(
    "mcserver",
    alias="server",
    developers=["_LittleC_", "OasisAkari", "DoroWolf"],
    doc=True,
)


@Silian_s.command(
    "<address:port> [-r] [-p] {{I18N:server.help}}",
    options_desc={"-r": "{I18N:server.help.option.r}", "-p": "{I18N:server.help.option.p}"},
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_server_address = Silian_msg.parsed_msg["<address:port>"]
    Silian_raw = Silian_msg.parsed_msg.get("-r", False)
    Silian_showplayer = Silian_msg.parsed_msg.get("-p", False)

    if check_local_address(Silian_server_address):
        await Silian_msg.finish(I18NContext("server.message.local_address"))

    Silian_java_info, Silian_bedrock_info = await asyncio.gather(
        query_java_server(Silian_server_address, Silian_raw, Silian_showplayer),
        query_bedrock_server(Silian_server_address, Silian_raw),
    )

    Silian_sendmsg = [Silian_java_info, Silian_bedrock_info]
    if Silian_sendmsg == ["", ""]:
        await Silian_msg.finish(I18NContext("server.message.not_found"))
    else:
        Silian_sendmsg = "\n".join(Silian_sendmsg).split("\n")
        Silian_sendmsg = await check(Silian_sendmsg, session=Silian_msg)
        Silian_t = "\n".join(Silian_x["content"] for Silian_x in Silian_sendmsg)
        await Silian_msg.finish(Silian_t.strip())


def check_local_address(server_address):
    if "localhost" in server_address.lower():
        return True

    Silian_match_serip = re.match(r"(.*?)\.(.*?)\.(.*?)\.(.*?)", server_address)
    if Silian_match_serip:
        if Silian_match_serip.group(1) == "192":
            if Silian_match_serip.group(2) == "168":
                return True
        if Silian_match_serip.group(1) == "172":
            if 16 <= int(Silian_match_serip.group(2)) <= 31:
                return True
        if Silian_match_serip.group(1) == "10":
            if 0 <= int(Silian_match_serip.group(2)) <= 255:
                return True
        if Silian_match_serip.group(1) == "127":
            return True
        if Silian_match_serip.group(1) == "0":
            if Silian_match_serip.group(2) == "0":
                if Silian_match_serip.group(3) == "0":
                    return True
    return False
