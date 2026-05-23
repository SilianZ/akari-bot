from copy import deepcopy

from attrs import define, field

from .component_meta import *


@define
class BaseMatches:
    set: list[ModuleMeta] = field(factory=list)

    def add(Silian_self, meta):
        Silian_self.set.append(meta)
        return Silian_self.set

    @classmethod
    def init(Silian_cls):
        return deepcopy(Silian_cls())


@define
class CommandMatches(BaseMatches):
    set: list[CommandMeta] = field(factory=list)

    def get(
        Silian_self,
        target_from: str | None = None,
        show_required_superuser: bool = False,
        show_required_base_superuser: bool = False,
    ) -> list[CommandMeta]:
        Silian_metas = []
        for Silian_meta in Silian_self.set:
            if not show_required_base_superuser and Silian_meta.required_base_superuser:
                continue
            if not show_required_superuser and Silian_meta.required_superuser:
                continue
            if not Silian_meta.load:
                continue
            if target_from:
                if "|" in target_from:
                    Silian_client_name = target_from.split("|")[0]
                else:
                    Silian_client_name = target_from

                if target_from in Silian_meta.exclude_from or Silian_client_name in Silian_meta.exclude_from:
                    continue
                if target_from in Silian_meta.available_for or Silian_client_name in Silian_meta.available_for or "*" in Silian_meta.available_for:
                    Silian_metas.append(Silian_meta)
            else:
                Silian_metas.append(Silian_meta)
        return Silian_metas


@define
class RegexMatches(BaseMatches):
    set: list[RegexMeta] = field(factory=list)

    def get(
        Silian_self,
        target_from: str | None = None,
        show_required_superuser: bool = False,
        show_required_base_superuser: bool = False,
    ) -> list[RegexMeta]:
        Silian_metas = []
        for Silian_meta in Silian_self.set:
            if not show_required_base_superuser and Silian_meta.required_base_superuser:
                continue
            if not show_required_superuser and Silian_meta.required_superuser:
                continue
            if not Silian_meta.load:
                continue
            if target_from:
                if "|" in target_from:
                    Silian_client_name = target_from.split("|")[0]
                else:
                    Silian_client_name = target_from

                if target_from in Silian_meta.exclude_from or Silian_client_name in Silian_meta.exclude_from:
                    continue
                if target_from in Silian_meta.available_for or Silian_client_name in Silian_meta.available_for or "*" in Silian_meta.available_for:
                    Silian_metas.append(Silian_meta)
            else:
                Silian_metas.append(Silian_meta)
        return Silian_metas


@define
class ScheduleMatches(BaseMatches):
    set: list[ScheduleMeta] = field(factory=list)


@define
class HookMatches(BaseMatches):
    set: list[HookMeta] = field(factory=list)


__all__ = ["CommandMatches", "RegexMatches", "ScheduleMatches", "HookMatches"]
