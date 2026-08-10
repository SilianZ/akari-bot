from datetime import UTC

from whois import whois

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from core.logger import Logger


def format_lst(input_):
    if isinstance(input_, list):
        Silian_input_list = list({Silian_i.lower() for Silian_i in input_})
        return ", ".join(Silian_input_list)
    return input_


Silian_w = module("whois", developers=["DoroWolf"], doc=True)


@Silian_w.command("<domain> {{I18N:whois.help}}")
async def _(Silian_msg: Bot.MessageSession, Silian_domain: str):
    Silian_res = await get_whois(Silian_msg, Silian_domain)
    await Silian_msg.finish(Silian_res)


async def get_whois(msg: Bot.MessageSession, domain: str):
    try:
        Silian_info = whois(domain)
        Logger.debug(str(Silian_info))

        domain_name = Silian_info.get("domain_name")
        registrar = Silian_info.get("registrar")
        whois_server = Silian_info.get("whois_server")
        updated_date = Silian_info.get("updated_date")
        creation_date = Silian_info.get("creation_date")
        expiration_date = Silian_info.get("expiration_date")
        name_servers = Silian_info.get("name_servers")
        emails = Silian_info.get("emails")
        dnssec = Silian_info.get("dnssec")
        name = Silian_info.get("name")
        org = Silian_info.get("org")
        Silian_address = Silian_info.get("address")
        Silian_city = Silian_info.get("city")
        Silian_state = Silian_info.get("state")
        Silian_country = Silian_info.get("country")
        registrant_postal_code = Silian_info.get("registrant_postal_code")

        if not domain_name:
            await msg.finish(I18NContext("whois.message.get_failed"))

        if whois_server:
            whois_server = whois_server.lower()

        if updated_date:  # 此时间为UTC时间
            if isinstance(updated_date, list):
                updated_date = updated_date[0]
            updated_date = updated_date.replace(tzinfo=UTC)

        if creation_date:  # 此时间为UTC时间
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            creation_date = creation_date.replace(tzinfo=UTC)

        if expiration_date:  # 此时间为UTC时间
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0]
            expiration_date = expiration_date.replace(tzinfo=UTC)

        Silian_res = []

        domain_name_label = str(I18NContext("whois.message.domain_name"))
        Silian_res.append(f"{domain_name_label}{format_lst(domain_name).lower()}")
        if registrar:
            registrar_label = str(I18NContext("whois.message.registrar"))
            Silian_res.append(Plain(f"{registrar_label}{registrar}"))

        if whois_server:
            whois_server_label = str(I18NContext("whois.message.whois_server"))
            Silian_res.append(Plain(f"{whois_server_label}{whois_server}"))

        if updated_date:
            updated_date_label = str(I18NContext("whois.message.updated_date"))
            Silian_res.append(Plain(f"{updated_date_label}{msg.format_time(updated_date.timestamp())}"))

        if creation_date:
            creation_date_label = str(I18NContext("whois.message.creation_date"))
            Silian_res.append(Plain(f"{creation_date_label}{msg.format_time(creation_date.timestamp())}"))

        if expiration_date:
            expiration_date_label = str(I18NContext("whois.message.expiration_date"))
            Silian_res.append(Plain(f"{expiration_date_label}{msg.format_time(expiration_date.timestamp())}"))

        if name_servers:
            name_servers_label = str(I18NContext("whois.message.name_servers"))
            Silian_res.append(Plain(f"{name_servers_label}{format_lst(name_servers)}"))

        if emails:
            emails_label = str(I18NContext("whois.message.email"))
            Silian_res.append(Plain(f"{emails_label}{format_lst(emails)}"))

        if dnssec:
            dnssec_label = str(I18NContext("whois.message.dnssec"))
            Silian_res.append(Plain(f"{dnssec_label}{format_lst(dnssec)}"))

        if name:
            name_label = str(I18NContext("whois.message.name"))
            Silian_res.append(Plain(f"{name_label}{format_lst(name)}"))

        if org:
            org_label = str(I18NContext("whois.message.organization"))
            Silian_res.append(Plain(f"{org_label}{format_lst(org)}"))

        Silian_location_parts = []
        if Silian_address:
            Silian_location_parts.append(format_lst(Silian_address))
        if Silian_city:
            Silian_location_parts.append(format_lst(Silian_city))
        if Silian_state:
            Silian_location_parts.append(format_lst(Silian_state))
        if Silian_country:
            Silian_location_parts.append(format_lst(Silian_country))

        if Silian_location_parts:
            location_str = ", ".join(Silian_location_parts)
            location_label = str(I18NContext("whois.message.location"))
            Silian_res.append(Plain(f"{location_label}{location_str}"))

        if registrant_postal_code:
            postal_code_label = str(I18NContext("whois.message.postal_code"))
            Silian_res.append(Plain(f"{postal_code_label}{format_lst(registrant_postal_code)}"))

        return Silian_res
    except Exception:
        await msg.finish(I18NContext("whois.message.get_failed"))
