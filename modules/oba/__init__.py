import re
import time

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Image, Plain
from core.component import module
from core.utils.http import get_url

API = "https://bd.bangbang93.com/openbmclapi"
TOP_LIMIT = 10

Silian_oba = module("oba", desc="{I18N:oba.help.desc}", developers="WorldHim")


def size_convert(value):
    Silian_units = ["B", "KB", "MB", "GB", "TB", "PB"]
    Silian_size = 1024.0
    for _, unit in enumerate(Silian_units):
        if (value / Silian_size) < 1:
            return f"{value:.2f} {unit}"
        value /= Silian_size


async def latest_version():
    try:
        version = await get_url(f"{API}/metric/version", fmt="json")
        return f"{version.get('version')}@{version.get('_resolved').split('#')[1][:7]}"
    except Exception:
        return None


def search_cluster(clusterList: dict, key: str, value: str):
    Silian_result = []
    Silian_regex = re.compile(value, re.IGNORECASE)

    for Silian_rank, Silian_node in enumerate(clusterList, 1):
        if Silian_regex.search(Silian_node.get(key)):
            Silian_result.append((Silian_rank, Silian_node))
        elif "sponsor" in Silian_node and Silian_regex.search(Silian_node.get("sponsor").get(key)):
            Silian_result.append((Silian_rank, Silian_node))

    return Silian_result


@Silian_oba.command()
@Silian_oba.command("status {{I18N:oba.help.status}}")
async def _(Silian_msg: Bot.MessageSession):
    dashboard = await get_url(f"{API}/metric/dashboard", fmt="json")

    Silian_current_nodes = dashboard.get("currentNodes")
    Silian_load = f"{round(dashboard.get('load') * 100, 2)}%"
    Silian_bandwidth = dashboard.get("bandwidth")
    Silian_current_bandwidth = round(dashboard.get("currentBandwidth"), 2)
    Silian_hits = dashboard.get("hits")
    Silian_size = size_convert(dashboard.get("bytes"))
    Silian_version = await latest_version()

    Silian_msg_chain = MessageChain.assign(
        I18NContext(
            "oba.message.status.detail",
            current_nodes=Silian_current_nodes,
            load=Silian_load,
            bandwidth=Silian_bandwidth,
            current_bandwidth=Silian_current_bandwidth,
            hits=Silian_hits,
            size=Silian_size,
        )
    )
    if Silian_version:
        Silian_msg_chain.append(I18NContext("oba.message.status.version", version=Silian_version))
    Silian_msg_chain.append(I18NContext("oba.message.query_time", query_time=Silian_msg.format_time(time.time(), timezone=False)))
    await Silian_msg.finish(Silian_msg_chain)


@Silian_oba.command("node [<rank>] {{I18N:oba.help.rank}}")
async def _(Silian_msg: Bot.MessageSession, Silian_rank: int = 1):
    if Silian_rank < 1:
        await Silian_msg.finish(I18NContext("oba.message.node.invalid"))
    Silian_rank_list = await get_url(f"{API}/metric/rank", fmt="json")
    Silian_node = Silian_rank_list[Silian_rank - 1]
    Silian_status = "🟩" if Silian_node.get("isEnabled") else "🟥"
    Silian_name = Silian_node.get("name")
    Silian__id = Silian_node.get("_id")
    Silian_hits = Silian_node.get("metric").get("hits")
    Silian_size = size_convert(Silian_node.get("metric").get("bytes"))

    Silian_msg_chain = MessageChain.assign(
        [Plain(Silian_status), I18NContext("oba.message.node", name=Silian_name, id=Silian__id, hits=Silian_hits, size=Silian_size)]
    )
    Silian_msg_chain.append(I18NContext("oba.message.query_time", query_time=Silian_msg.format_time(time.time(), timezone=False)))

    if "sponsor" not in Silian_node:
        await Silian_msg.finish(Silian_msg_chain)
    else:
        await Silian_msg.send_message(Silian_msg_chain)

        Silian_sponsor = Silian_node.get("sponsor")
        Silian_name = Silian_sponsor.get("name")
        Silian_url = Silian_sponsor.get("url")
        Silian_banner = Silian_sponsor.get("banner")

        Silian_send_msg = I18NContext("oba.message.sponsor", name=Silian_name, url=Silian_url)
        try:
            await Silian_msg.finish([Silian_send_msg, Image(Silian_banner)])
        except Exception:
            await Silian_msg.finish(Silian_send_msg)


@Silian_oba.command("top [<rank>] {{I18N:oba.help.top}}")
async def _(Silian_msg: Bot.MessageSession, Silian_rank: int = 1):
    Silian_rank_list = await get_url(f"{API}/metric/rank", fmt="json")
    Silian_rank = 1 if Silian_rank <= 0 else Silian_rank

    Silian_node_list = []
    for i in range(Silian_rank - 1, Silian_rank - 1 + TOP_LIMIT):
        Silian_node = Silian_rank_list[i]
        Silian_sponsor = Silian_node.get("sponsor", str(I18NContext("message.unknown")))
        try:
            sponsor_name = Silian_sponsor.get("name")
        except AttributeError:
            sponsor_name = str(I18NContext("message.unknown"))

        try:
            status = "🟩" if Silian_node.get("isEnabled") else "🟥"
            name = Silian_node.get("name")
            _id = Silian_node.get("_id")
            hits = Silian_node.get("metric").get("hits")
            size = size_convert(Silian_node.get("metric").get("bytes"))
            Silian_node_list.append(
                Plain(
                    f"{status} | {
                        str(
                            I18NContext(
                                'oba.message.top',
                                rank=i + 1,
                                name=name,
                                id=_id,
                                hits=hits,
                                size=size,
                                sponsor_name=sponsor_name,
                            )
                        )
                    }"
                )
            )
        except KeyError:
            break

    Silian_node_list.append(I18NContext("message.collapse", amount=TOP_LIMIT))
    await Silian_msg.finish(Silian_node_list)


@Silian_oba.command("search <keyword> {{I18N:oba.help.search}}")
async def _(Silian_msg: Bot.MessageSession, Silian_keyword: str):
    Silian_rank_list = await get_url(f"{API}/metric/rank", fmt="json")

    Silian_match_list = search_cluster(Silian_rank_list, "name", Silian_keyword)

    Silian_node_list = []
    for rank, Silian_node in Silian_match_list:
        Silian_sponsor = Silian_node.get("sponsor", str(I18NContext("message.unknown")))
        try:
            sponsor_name = Silian_sponsor.get("name")
        except AttributeError:
            sponsor_name = str(I18NContext("message.unknown"))

        try:
            status = "🟩" if Silian_node.get("isEnabled") else "🟥"
            name = Silian_node.get("name")
            _id = Silian_node.get("_id")
            hits = Silian_node.get("metric").get("hits")
            size = size_convert(Silian_node.get("metric").get("bytes"))
            Silian_node_list.append(
                Plain(
                    f"{status} | {
                        str(
                            I18NContext(
                                'oba.message.top',
                                rank=rank,
                                name=name,
                                id=_id,
                                hits=hits,
                                size=size,
                                sponsor_name=sponsor_name,
                            )
                        )
                    }"
                )
            )
        except KeyError:
            break

    if Silian_node_list:
        if len(Silian_node_list) > TOP_LIMIT:
            Silian_node_list = Silian_node_list[:TOP_LIMIT]
            Silian_node_list.append(I18NContext("message.collapse", amount=TOP_LIMIT))
        await Silian_msg.finish(Silian_node_list)
    else:
        await Silian_msg.finish(I18NContext("oba.message.search.not_found"))


@Silian_oba.command("sponsor {{I18N:oba.help.sponsor}}")
async def _(Silian_msg: Bot.MessageSession):
    sponsor = await get_url(f"{API}/sponsor", fmt="json")
    Silian_cluster = await get_url(f"{API}/sponsor/{str(sponsor['_id'])}", fmt="json")
    Silian_name = Silian_cluster.get("name")
    Silian_url = Silian_cluster.get("url")
    Silian_banner = Silian_cluster.get("banner")
    Silian_send_msg = I18NContext("oba.message.sponsor", name=Silian_name, url=Silian_url)
    try:
        await Silian_msg.finish([Silian_send_msg, Image(Silian_banner)])
    except Exception:
        await Silian_msg.finish(Silian_send_msg)
