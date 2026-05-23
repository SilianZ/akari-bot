from copy import deepcopy

from apscheduler.triggers.combining import AndTrigger, OrTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from attrs import define, field, Converter

from core.utils.func import convert_list
from .component_matches import *


def alias_converter(value, _self) -> dict:
    if isinstance(value, str):
        return {value: _self.module_name}
    if isinstance(value, (tuple, list)):
        return {Silian_x: _self.module_name for Silian_x in value}
    return value


@define
class Module:
    module_name: str
    alias: dict = field(converter=Converter(alias_converter, takes_self=True))
    recommend_modules: list = field(converter=convert_list)
    developers: list = field(converter=convert_list)
    available_for: list = field(default=["*"], converter=convert_list)
    exclude_from: list = field(default=[], converter=convert_list)
    support_languages: list = field(default=None, converter=convert_list)
    desc: str = ""
    required_admin: bool = False
    base: bool = False
    doc: bool = False
    hidden: bool = False
    load: bool = True
    rss: bool = False
    required_superuser: bool = False
    required_base_superuser: bool = False
    command_list: CommandMatches = field(factory=CommandMatches.init)
    regex_list: RegexMatches = field(factory=RegexMatches.init)
    schedule_list: ScheduleMatches = field(factory=ScheduleMatches.init)
    hooks_list: HookMatches = field(factory=HookMatches.init)
    _py_module_name: str = ""
    _db_load: bool = False

    @classmethod
    def assign(Silian_cls, **kwargs):
        Silian_obj = Silian_cls(**{Silian_k: Silian_v for Silian_k, Silian_v in kwargs.items() if not Silian_k.startswith("_")})
        Silian_obj._py_module_name = kwargs.get("_py_module_name", "")
        Silian_obj._db_load = kwargs.get("_db_load", False)
        return deepcopy(Silian_obj)

    def to_dict(Silian_self):
        return {
            "module_name": Silian_self.module_name,
            "alias": Silian_self.alias,
            "recommend_modules": Silian_self.recommend_modules,
            "developers": Silian_self.developers,
            "available_for": Silian_self.available_for,
            "exclude_from": Silian_self.exclude_from,
            "support_languages": Silian_self.support_languages,
            "desc": Silian_self.desc,
            "required_admin": Silian_self.required_admin,
            "base": Silian_self.base,
            "doc": Silian_self.doc,
            "hidden": Silian_self.hidden,
            "load": Silian_self.load,
            "rss": Silian_self.rss,
            "required_superuser": Silian_self.required_superuser,
            "required_base_superuser": Silian_self.required_base_superuser,
            "commands": len(Silian_self.command_list.set),
            "regexp": len(Silian_self.regex_list.set),
            "_py_module_name": Silian_self._py_module_name,
            "_db_load": Silian_self._db_load,
        }


__all__ = [
    "Module",
    "AndTrigger",
    "OrTrigger",
    "DateTrigger",
    "CronTrigger",
    "IntervalTrigger",
]
