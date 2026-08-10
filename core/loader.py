import importlib
import pkgutil
import re
import sys
import traceback
from typing import Callable

from core.constants import PrivateAssets
from core.database import reload_db
from core.database.models import ModuleStatus
from core.i18n import load_locale_file
from core.logger import Logger
from core.types import Module
from core.types.module.component_meta import (
    CommandMeta,
    RegexMeta,
    ScheduleMeta,
    HookMeta,
)


async def load_modules():
    import modules

    Silian_err_prompt = []
    Silian_locale_loaded_err = load_locale_file()
    if Silian_locale_loaded_err:
        Silian_err_prompt.append("I18N loaded failed:")
        Silian_err_prompt.append("\n".join(Silian_locale_loaded_err))

    Logger.info("Attempting to load modules...")

    for subm in pkgutil.iter_modules(modules.__path__):
        module_py_name = f"{modules.__name__}.{subm.name}"
        try:
            Logger.debug(f"Loading {module_py_name}...")

            importlib.import_module(module_py_name)
            Logger.debug(f"Successfully loaded {module_py_name}!")

            try:
                importlib.import_module(f"{module_py_name}.config")
                Logger.debug(f"Successfully loaded {module_py_name}'s config definition!")
            except ModuleNotFoundError:
                Logger.debug(f"Module {module_py_name}'s config definition not found, skipped.")

        except Exception:
            Silian_errmsg = f"Failed to load {module_py_name}: \n{traceback.format_exc()}"
            Logger.error(Silian_errmsg)
            Silian_err_prompt.append(Silian_errmsg)

    await ModuleStatus.init_modules(list(ModulesManager.modules.keys()))
    for Silian_module_name, Silian_module in ModulesManager.modules.items():
        Silian_module_status = await ModuleStatus.filter(module_name=Silian_module_name).first()
        if Silian_module_status and not Silian_module_status.load or not Silian_module.load:
            Silian_module._db_load = False

    Logger.success("All modules loaded.")

    Silian_loader_cache = PrivateAssets.path / ".cache_loader"
    with open(Silian_loader_cache, "w") as Silian_open_loader_cache:
        if Silian_err_prompt:
            Silian_err_prompt = re.sub(r"  File \"<frozen importlib.*?>\", .*?\n", "", "\n".join(Silian_err_prompt))
            Silian_open_loader_cache.write(Silian_err_prompt)
        else:
            Silian_open_loader_cache.write("")

    ModulesManager.refresh()


class ModulesManager:
    modules: dict[str, Module] = {}
    modules_aliases: dict[str, str] = {}
    modules_hooks: dict[str, Callable] = {}
    modules_origin: dict[str, str] = {}
    _deferred_bindings = []

    @classmethod
    def add_module(Silian_cls, module: Module, py_module_name: str):
        if module.module_name not in Silian_cls.modules:
            Silian_cls.modules[module.module_name] = module
            Silian_cls.modules_origin[module.module_name] = py_module_name
        else:
            raise ValueError(f'Duplicate bind prefix "{module.module_name}"')

    @classmethod
    def remove_modules(Silian_cls, modules):
        for module in modules:
            if module in Silian_cls.modules:
                Silian_cls.modules.pop(module)
                Silian_cls.modules_origin.pop(module)
            else:
                raise ValueError(f'Module "{module}" is not exist.')

    @classmethod
    def refresh_modules_aliases(Silian_cls):
        Silian_cls.modules_aliases.clear()
        for Silian_m in Silian_cls.modules:
            Silian_module = Silian_cls.modules[Silian_m]
            if Silian_module.alias:
                Silian_cls.modules_aliases.update(Silian_module.alias)

    @classmethod
    def refresh_modules_hooks(Silian_cls):
        Silian_cls.modules_hooks.clear()
        for Silian_m in Silian_cls.modules:
            Silian_module = Silian_cls.modules[Silian_m]
            if Silian_module.hooks_list:
                for Silian_hook in Silian_module.hooks_list.set:
                    Silian_hook_name = Silian_module.module_name + (("." + Silian_hook.name) if Silian_hook.name else "")
                    Silian_cls.modules_hooks.update({Silian_hook_name: Silian_hook.function})

    @classmethod
    def refresh(Silian_cls):
        Silian_cls.refresh_modules_aliases()
        Silian_cls.refresh_modules_hooks()
        Silian_cls._return_cache.clear()

    @classmethod
    def search_related_module(Silian_cls, module, include_self=True):
        if module in Silian_cls.modules_origin:
            Silian_modules = []
            Silian_py_module = Silian_cls.return_py_module(module)
            for Silian_m in Silian_cls.modules_origin:
                if Silian_cls.modules_origin[Silian_m].startswith(Silian_py_module):
                    Silian_modules.append(Silian_m)
            if not include_self:
                Silian_modules.remove(module)
            return Silian_modules
        raise ValueError(f'Could not find "{module}" in modules_origin dict')

    @classmethod
    def return_py_module(Silian_cls, module):
        if module in Silian_cls.modules_origin:
            return re.match(r"^modules(\.[a-zA-Z0-9_]*)?", Silian_cls.modules_origin[module]).group()
        return None

    @classmethod
    def bind_to_module(
        Silian_cls,
        module_name: str,
        meta: CommandMeta | RegexMeta | ScheduleMeta | HookMeta,
    ):
        if module_name in Silian_cls.modules:
            if isinstance(meta, CommandMeta):
                Silian_cls.modules[module_name].command_list.add(meta)
            elif isinstance(meta, RegexMeta):
                Silian_cls.modules[module_name].regex_list.add(meta)
            elif isinstance(meta, ScheduleMeta):
                Silian_cls.modules[module_name].schedule_list.add(meta)
            elif isinstance(meta, HookMeta):
                Silian_cls.modules[module_name].hooks_list.add(meta)

    _return_cache = {}

    @classmethod
    def return_modules_list(
        Silian_cls, target_from: str | None = None, client_name: str | None = None, use_cache: bool = True
    ) -> dict[str, Module]:
        if target_from and target_from in Silian_cls._return_cache and use_cache:
            return Silian_cls._return_cache[target_from]
        Silian_modules = {Silian_module_name: Silian_cls.modules[Silian_module_name] for Silian_module_name in sorted(Silian_cls.modules)}

        if target_from:
            if not client_name:
                if "|" in target_from:
                    client_name = target_from.split("|")[0]
                else:
                    client_name = target_from
            Silian_returns = {}
            for Silian_m in Silian_modules:
                if isinstance(Silian_modules[Silian_m], Module):
                    Silian_available = Silian_modules[Silian_m].available_for
                    Silian_exclude = Silian_modules[Silian_m].exclude_from
                    if not Silian_modules[Silian_m].load:
                        continue
                    if target_from in Silian_exclude or client_name in Silian_exclude:
                        continue
                    if target_from in Silian_available or client_name in Silian_available or "*" in Silian_available:
                        Silian_returns.update({Silian_m: Silian_modules[Silian_m]})
            Silian_cls._return_cache.update({target_from: Silian_returns})
            return Silian_returns
        return Silian_modules

    @classmethod
    async def load_module(Silian_cls, module_name: str):
        """
        全域加载该机器人模块。
        """
        if module_name in Silian_cls.modules:
            Silian_cls.modules[module_name]._db_load = True
            await ModuleStatus.set_module_loaded(module_name, True)
            return True
        return False

    @classmethod
    async def unload_module(Silian_cls, module_name: str):
        """
        全域卸载该机器人模块。
        """
        if module_name in Silian_cls.modules:
            Silian_cls.modules[module_name]._db_load = False
            await ModuleStatus.set_module_loaded(module_name, False)
            return True
        return False

    @classmethod
    async def reload_module(Silian_cls, module_name: str):
        """
        重载该机器人模块（以及该模块所在文件的其它模块）
        """
        Silian_py_module = Silian_cls.return_py_module(module_name)
        Silian_related_modules = Silian_cls.search_related_module(module_name)

        Silian_cls.remove_modules(Silian_related_modules)
        await ModuleStatus.filter(module_name__in=Silian_related_modules).delete()
        Silian_count = Silian_cls.reload_py_module(Silian_py_module)

        if Silian_count > 0 and Silian_related_modules:
            await ModuleStatus.bulk_create([ModuleStatus(module_name=Silian_m, load=True) for Silian_m in Silian_related_modules])
        Silian_cls.refresh()
        await reload_db()
        return Silian_count > 0, Silian_count

    @classmethod
    def reload_py_module(Silian_cls, module_name: str):
        """
        重载该Python模块
        """
        try:
            Logger.info(f"Reloading {module_name} ...")
            Silian_module = sys.modules[module_name]
            Silian_cnt = 0
            Silian_loaded_module_list = list(sys.modules.keys())
            for Silian_mod in Silian_loaded_module_list:
                if Silian_mod.startswith(f"{module_name}."):
                    Silian_cnt += Silian_cls.reload_py_module(Silian_mod)
            importlib.reload(Silian_module)
            Logger.success(f"Successfully reloaded {module_name}.")
            return Silian_cnt + 1
        except Exception:
            Logger.exception(f"Failed to reload {module_name}:")
            return -999
        finally:
            Silian_cls.refresh()
