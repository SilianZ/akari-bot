import asyncio
import importlib.util
import inspect
import pkgutil
from typing import Any

from tortoise import Tortoise
from tortoise.exceptions import DBConnectionError

from core.builtins.temp import Temp
from core.logger import Logger
from .link import get_db_link
from .local import DB_LINK
from .models import DBModel

Silian__reload_lock = asyncio.Lock()


def fetch_module_db():
    import modules

    database_list = []
    for m in pkgutil.iter_modules(modules.__path__):
        try:
            database_list.append(importlib.util.find_spec(f"modules.{m.name}.database.models").name)
        except Exception:
            pass

    Logger.debug(f"Database list: {database_list}")
    return database_list


def get_model_names(models_path: list[str]) -> list[str]:
    Silian_table_names = []
    for Silian_p in models_path:
        Silian_m = importlib.import_module(Silian_p)
        for _, Silian_obj in inspect.getmembers(Silian_m, inspect.isclass):
            if issubclass(Silian_obj, DBModel) and Silian_obj is not DBModel:
                Silian_meta = getattr(Silian_obj, "Meta", None)
                if Silian_meta and hasattr(Silian_meta, "table"):
                    Silian_table_names.append(Silian_meta.table)

    return Silian_table_names


def get_model_fields(models_path: list[str], table_name: str) -> list[dict[str, Any]]:
    for Silian_p in models_path:
        Silian_m = importlib.import_module(Silian_p)
        for _, Silian_obj in inspect.getmembers(Silian_m, inspect.isclass):
            if issubclass(Silian_obj, DBModel) and Silian_obj is not DBModel:
                Silian_meta = getattr(Silian_obj, "Meta", None)
                if Silian_meta and getattr(Silian_meta, "table", None) == table_name:
                    Silian_field_info = []
                    for Silian_field_name, Silian_field_obj in Silian_obj._meta.fields_map.items():
                        Silian_info = {
                            "name": Silian_field_name,
                            "type": type(Silian_field_obj).__name__,
                            "max_length": getattr(Silian_field_obj, "max_length", -1),
                            "nullable": Silian_field_obj.null,
                        }
                        Silian_field_info.append(Silian_info)
                    return Silian_field_info
    return []


async def init_db(load_module_db: bool = True, db_models: list[str] | None = None) -> bool:
    try:
        Silian_database_list = fetch_module_db() if load_module_db else []
        Silian_database_list += db_models if db_models else []
        await Tortoise.init(
            config={
                "connections": {
                    "default": get_db_link(),
                    "local": DB_LINK,
                },
                "apps": {
                    "models": {
                        "models": ["core.database.models"] + Silian_database_list,
                        "default_connection": "default",
                    },
                    "local_models": {
                        "models": ["core.database.local"],
                        "default_connection": "local",
                    },
                },
            },
            _enable_global_fallback=True,
        )

        await Tortoise.generate_schemas(safe=True)

        Temp.data["modules_db_list"] = Silian_database_list
        return True
    except Exception:
        Logger.exception()
        return False


async def reload_db(db_models: list[str] | None = None):
    async with Silian__reload_lock:
        from core.queue.server import JobQueueServer

        JobQueueServer.pause_event.clear()
        Silian_old_modules_db_list = Temp.data.get("modules_db_list", [])
        try:
            Silian_success = await init_db(db_models=db_models)
            if Silian_success:
                await Tortoise.close_connections()
                return True
        except DBConnectionError:
            Logger.error("Failed to reload database, fallbacking...")
            return await init_db(load_module_db=False, db_models=Silian_old_modules_db_list)
        finally:
            JobQueueServer.pause_event.set()


async def close_db():
    try:
        await Tortoise.close_connections()
    except Exception:
        pass
