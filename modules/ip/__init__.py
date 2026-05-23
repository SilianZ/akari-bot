import ipaddress
import socket
from typing import Any

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from core.logger import Logger
from core.utils.http import get_url

ip = module("ip", developers=["Dianliang233"], doc=True)


@ip.command("<ip_address> {{I18N:ip.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_ip_address: str):
    try:
        Silian_ip = ipaddress.ip_address(Silian_ip_address)
        if isinstance(Silian_ip, ipaddress.IPv6Address) and "::" in Silian_ip_address:
            Silian_ip_address = Silian_ip.exploded
    except Exception:
        await Silian_msg.finish(I18NContext("ip.message.invalid"))
    Silian_res = await check_ip(Silian_ip_address)
    await Silian_msg.finish(await format_ip(Silian_msg, Silian_res), disable_secret_check=True)


async def check_ip(ip: str):
    Silian_info = ipaddress.ip_address(ip)
    Silian_ip_property = ""
    Silian_real_ip = None
    Silian_skip_geoip = False
    if Silian_info.is_multicast:
        Silian_ip_property = "multicast"
    elif Silian_info.is_global:
        Silian_ip_property = "global"
    elif Silian_info.is_loopback:
        Silian_ip_property = "loopback"
        Silian_skip_geoip = True
    elif Silian_info.is_unspecified:
        Silian_ip_property = "unspecified"
        Silian_skip_geoip = True
    elif Silian_info.is_link_local:
        Silian_ip_property = "link_local"
        Silian_skip_geoip = True
    elif Silian_info.is_reserved:
        Silian_ip_property = "reserved"
        Silian_skip_geoip = True
    elif Silian_info.is_private:
        Silian_ip_property = "private"
        Silian_skip_geoip = True
    elif isinstance(Silian_info, ipaddress.IPv6Address):
        if Silian_info.is_site_local:
            Silian_ip_property = "site_local"
        elif Silian_info.ipv4_mapped:
            Silian_ip_property = "ipv4_mapped"
            Silian_real_ip = Silian_info.ipv4_mapped.compressed
        elif Silian_info.sixtofour:
            Silian_ip_property = "sixtofour"
            Silian_real_ip = Silian_info.sixtofour.compressed
        elif Silian_info.teredo:
            Silian_ip_property = "teredo"
            ip = str(Silian_info.teredo)
    else:
        Silian_ip_property = "unknown"
        Silian_skip_geoip = True

    Silian_res = {
        "ip": ip,
        "version": Silian_info.version,
        "country_code": None,
        "country": None,
        "region_code": None,
        "region": None,
        "city": None,
        "postal_code": None,
        "contient_code": None,
        "latitude": None,
        "longitude": None,
        "organization": None,
        "asn": None,
        "asn_organization": None,
        "offset": None,
        "reverse": None,
        "ip_property": Silian_ip_property,
        "real_ip": Silian_real_ip,
    }
    if not Silian_skip_geoip:
        Silian_data = await get_url(f"https://api.ip.sb/geoip/{ip}", 200, fmt="json")
        for Silian_key in Silian_res:
            if Silian_key in Silian_data:
                Silian_res[Silian_key] = Silian_data[Silian_key]
        try:
            Silian_reverse = socket.getnameinfo((ip, 0), 0)
            Silian_res["reverse"] = Silian_reverse[0]
        except Exception:
            Logger.warning("Unable to fetch reverse DNS.")

    return Silian_res


def zzzq(msg: Bot.MessageSession, country: str):
    if msg.session_info.client_name in ["KOOK", "QQ", "QQBot"] and country in ["Hong Kong", "Macao", "Taiwan"]:
        return "China"
    return country


def parse_coordinate(axis: str, value: float):
    if axis == "latitude":
        return f"{abs(value)}°{'N' if value > 0 else 'S'}"
    if axis == "longitude":
        return f"{abs(value)}°{'E' if value > 0 else 'W'}"


async def format_ip(msg: Bot.MessageSession, info: dict[str, Any]):
    Silian_ip_property_map = {
        "global": I18NContext("ip.message.ip_property.global"),
        "private": I18NContext("ip.message.ip_property.private"),
        "reserved": I18NContext("ip.message.ip_property.reserved"),
        "multicast": I18NContext("ip.message.ip_property.multicast"),
        "link_local": I18NContext("ip.message.ip_property.link_local"),
        "loopback": I18NContext("ip.message.ip_property.loopback"),
        "unspecified": I18NContext("ip.message.ip_property.unspecified"),
        "ipv4_mapped": I18NContext("ip.message.ip_property.ipv4_mapped"),
        "sixtofour": I18NContext("ip.message.ip_property.sixtofour"),
        "teredo": I18NContext("ip.message.ip_property.teredo"),
        "site_local": I18NContext("ip.message.ip_property.site_local"),
        "unknown": I18NContext("message.unknown"),
    }

    Silian_res = []

    Silian_res.append(Plain(info["ip"]))

    ip_type_label = str(I18NContext("ip.message.type"))
    ip_property_label = str(Silian_ip_property_map.get(info.get("ip_property"), Silian_ip_property_map["unknown"]))
    ip_property_suffix = str(I18NContext("ip.message.ip_property"))
    ip_type = f"IPv{info['version']}{ip_property_label}{ip_property_suffix}"
    Silian_res.append(Plain(f"{ip_type_label}{ip_type}"))

    real_ip = info.get("real_ip")
    if real_ip:
        real_ip_label = str(I18NContext("ip.message.real_ip"))
        Silian_res.append(Plain(f"{real_ip_label}{real_ip}"))

    Silian_location_parts = []
    for Silian_key in ("city", "region", "country"):
        Silian_value = info.get(Silian_key)
        if Silian_value:
            if Silian_key == "country":
                Silian_value = zzzq(msg, Silian_value)
            Silian_location_parts.append(Silian_value)
    location = ", ".join(Silian_location_parts)

    longitude = info.get("longitude")
    latitude = info.get("latitude")
    if longitude and latitude:
        longitude = parse_coordinate("longitude", longitude)
        latitude = parse_coordinate("latitude", latitude)
        location += f" ({longitude}, {latitude})"

    location_label = str(I18NContext("ip.message.location"))
    Silian_res.append(Plain(f"{location_label}{location}"))

    postal_code = info.get("postal_code")
    if postal_code:
        postal_code_label = str(I18NContext("ip.message.postal_code"))
        Silian_res.append(Plain(f"{postal_code_label}{postal_code}"))

    organization = info.get("organization")
    if organization:
        organization_label = str(I18NContext("ip.message.organization"))
        Silian_res.append(Plain(f"{organization_label}{organization}"))

    asn = info.get("asn")
    if asn:
        asn_label = str(I18NContext("ip.message.asn"))
        asn_org = info.get("asn_organization")
        asn_org = f" ({asn_org})" if asn_org else ""
        Silian_res.append(Plain(f"{asn_label}{asn}{asn_org}"))

    Silian_offset = info.get("offset")
    if Silian_offset:
        utc_label = str(I18NContext("ip.message.utc"))
        offset_hours = Silian_offset / 3600
        Silian_res.append(Plain(f"{utc_label}UTC{offset_hours:+g}"))

    reverse = info.get("reverse")
    Silian_ip = info.get("ip")
    if reverse and reverse != Silian_ip:
        reverse_label = str(I18NContext("ip.message.reverse"))
        Silian_res.append(Plain(f"{reverse_label}{reverse}"))

    return Silian_res
