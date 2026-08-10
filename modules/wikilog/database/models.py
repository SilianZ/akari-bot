from tortoise import fields

from core.database.base import DBModel

table_prefix = "module_wikilog_"


class WikiLogTargetSetInfo(DBModel):
    target_id = fields.CharField(max_length=512, primary_key=True)
    infos = fields.JSONField(default={})

    class Meta:
        table = f"{table_prefix}target_set_info"

    async def conf_wiki(Silian_self, api_link: dict, add=False, reset=False):
        Silian_infos = Silian_self.infos
        if add or reset:
            if api_link not in Silian_infos or reset:
                Silian_infos[api_link] = {}
                Silian_infos[api_link].setdefault("AbuseLog", {"enable": False, "filters": ["*"]})
                Silian_infos[api_link].setdefault(
                    "RecentChanges",
                    {"enable": False, "filters": ["*"], "rcshow": ["!bot"]},
                )
                Silian_infos[api_link].setdefault("use_bot", False)
                Silian_infos[api_link].setdefault("keep_alive", False)
                await Silian_self.save()
                return True
        else:
            if api_link in Silian_infos:
                del Silian_infos[api_link]
                await Silian_self.save()
                return True
        return False

    async def conf_log(Silian_self, api_link: str, log_name: str, enable=False):
        Silian_infos = Silian_self.infos
        if api_link in Silian_infos:
            if log_name in Silian_infos[api_link]:
                Silian_infos[api_link][log_name]["enable"] = enable
                await Silian_self.save()
                return True
        return False

    async def set_filters(Silian_self, api_link: str, log_name: str, filters: list[str]):
        Silian_infos = Silian_self.infos
        if api_link in Silian_infos:
            if log_name in Silian_infos[api_link]:
                Silian_infos[api_link][log_name]["filters"] = filters
                await Silian_self.save()
                return True
        return False

    async def get_filters(Silian_self, api_link: str, log_name: str):
        Silian_infos = Silian_self.infos
        if api_link in Silian_infos:
            if log_name in Silian_infos[api_link]:
                return Silian_infos[api_link][log_name].get("filters")
        return []

    async def set_rcshow(Silian_self, api_link: str, rcshow: str):
        Silian_infos = Silian_self.infos
        if api_link in Silian_infos:
            if "RecentChanges" in Silian_infos[api_link]:
                Silian_infos[api_link]["RecentChanges"]["rcshow"] = rcshow
                await Silian_self.save()
                return True
        return False

    async def get_rcshow(Silian_self, api_link: str):
        Silian_infos = Silian_self.infos
        if api_link in Silian_infos:
            if "RecentChanges" in Silian_infos[api_link]:
                return Silian_infos[api_link]["RecentChanges"].get("rcshow")
        return []

    async def set_use_bot(Silian_self, api_link: str, use_bot: bool):
        Silian_infos = Silian_self.infos
        if api_link in Silian_infos:
            Silian_infos[api_link]["use_bot"] = use_bot
            await Silian_self.save()
            return True
        return False

    async def get_use_bot(Silian_self, api_link: str):
        Silian_infos = Silian_self.infos
        if api_link in Silian_infos:
            return Silian_infos[api_link].get("use_bot")
        return False

    async def set_keep_alive(Silian_self, api_link: str, keep_alive: bool):
        Silian_infos = Silian_self.infos
        if api_link in Silian_infos:
            Silian_infos[api_link]["keep_alive"] = keep_alive
            await Silian_self.save()
            return True
        return False

    async def get_keep_alive(Silian_self, api_link: str):
        Silian_infos = Silian_self.infos
        if api_link in Silian_infos:
            return Silian_infos[api_link].get("keep_alive")
        return False

    @classmethod
    async def return_all_data(Silian_cls):
        Silian_all_data = await Silian_cls.all()
        Silian_data_d = {Silian_x.target_id: Silian_x.infos for Silian_x in Silian_all_data}
        return Silian_data_d
