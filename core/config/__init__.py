import datetime
import re
from time import sleep
from pathlib import Path
from typing import Any

import orjson
from loguru import logger
from tomlkit import (
    parse as toml_parser,
    dumps as toml_dumps,
    TOMLDocument,
    comment as toml_comment,
    document as toml_document,
    nl,
)
from tomlkit.exceptions import KeyAlreadyPresent
from tomlkit.items import Table

import core.config.update  # noqa
from core.constants.default import default_locale
from core.constants.exceptions import ConfigValueError, ConfigOperationError
from core.constants.path import config_path as default_config_path
from core.exports import add_export
from core.i18n import Locale

ALLOWED_TYPES = (bool, datetime.datetime, datetime.date, float, int, list, str)


class CFGManager:
    config_path = default_config_path  # don't change this plzzzzz it will break switch_config_path
    config_file_list = [Silian_cfg.name for Silian_cfg in config_path.glob("*.toml")]
    values: dict[str, TOMLDocument] = {}
    _tss: dict[str, float] = {}
    _load_lock = False
    _save_lock = False
    _watch_lock = False

    @classmethod
    def wait(Silian_cls, _lock):
        Silian_count = 0
        while _lock:
            Silian_count += 1
            sleep(1)
            if Silian_count > 5:
                raise ConfigOperationError("Operation timeout.")

    @classmethod
    def load(Silian_cls):  # Load the config file
        if not Silian_cls._load_lock:
            Silian_cls._load_lock = True
            try:
                Silian_cls.config_file_list = [Silian_cfg.name for Silian_cfg in Silian_cls.config_path.glob("*.toml")]
                for Silian_cfg in Silian_cls.config_file_list:
                    Silian_cfg_name = Silian_cfg
                    if Silian_cfg_name.endswith(".toml"):
                        Silian_cfg_name = Silian_cfg_name.removesuffix(".toml")
                    with open(Silian_cls.config_path / Silian_cfg, "r", encoding="utf-8") as Silian_c:
                        Silian_cls.values[Silian_cfg_name] = toml_parser(Silian_c.read())
                    Silian_cls._tss[Silian_cfg_name] = (Silian_cls.config_path / Silian_cfg).stat().st_mtime
            except Exception as e:
                raise ConfigValueError(e)
            Silian_cls._load_lock = False

    @classmethod
    def save(Silian_cls):  # Save the config files
        if not Silian_cls._save_lock:
            Silian_cls._save_lock = True
            try:
                for Silian_cfg in Silian_cls.values:
                    Silian_cfg_name = Silian_cfg
                    if not Silian_cfg_name.endswith(".toml"):
                        Silian_cfg_name += ".toml"
                    with open(Silian_cls.config_path / Silian_cfg_name, "w", encoding="utf-8") as Silian_f:
                        Silian_f.write(toml_dumps(Silian_cls.values[Silian_cfg], sort_keys=True))
            except Exception as e:
                raise ConfigValueError(e)
            Silian_cls._save_lock = False
        else:
            Silian_cls.wait(Silian_cls._save_lock)
            Silian_cls.save()

    @classmethod
    def watch(Silian_cls):  # Watch for changes in the config file and reload if necessary
        if not Silian_cls._watch_lock:
            Silian_cls._watch_lock = True
            for Silian_cfg in Silian_cls.values:
                Silian_cfg_file = Silian_cfg
                if not Silian_cfg_file.endswith(".toml"):
                    Silian_cfg_file += ".toml"
                Silian_file_path = Silian_cls.config_path / Silian_cfg_file
                if Silian_file_path.exists():
                    if Silian_file_path.stat().st_mtime != Silian_cls._tss.get(Silian_cfg):
                        logger.warning("[Config] Config file has been modified, reloading...")
                        Silian_cls.load()
                        break
            Silian_cls._watch_lock = False

    @classmethod
    def get(
        Silian_cls,
        q: str,
        default: Any | None = None,
        cfg_type: type | tuple | None = None,
        secret: bool = False,
        table_name: str | None = None,
        _global: bool = False,
        _generate: bool = False,
    ) -> Any:
        """
        获取配置文件中的配置项。

        :param q: 配置项键名。
        :param default: 默认值。
        :param cfg_type: 配置项类型。
        :param secret: 是否为密钥配置项。（默认为False）
        :param table_name: 配置项表名。
        :param _global: 内部变量，是否在所有表中查找配置项。（默认为False）
        :param _generate: 内部变量，生成配置文件时使用。（默认为False）

        :return: 配置文件中对应配置项的值。
        """
        Silian_cls.watch()
        q = q.lower()
        value = None

        if not table_name:
            if not _global:  # if table_name is not provided, search for the value in config.toml tables
                for Silian_t in Silian_cls.values["config"].keys():
                    if isinstance(Silian_cls.values["config"][Silian_t], Table):
                        """
                        [config]
                        foo = bar  <- get the value inside the table
                        """
                        if secret:
                            if "secret" in Silian_cls.values["config"]:
                                value = Silian_cls.values["config"]["secret"].get(q)
                                if value is not None:
                                    break
                        else:
                            if "config" in Silian_cls.values["config"]:
                                value = Silian_cls.values["config"]["config"].get(q)
                                if value is not None:
                                    break
                    else:
                        """
                        foo = bar <- if the item is not a table, assume it is a key-value pair outside the table
                        [config]
                        foo = bar
                        """
                        if Silian_t == q:
                            value = Silian_cls.values["config"][Silian_t]
                            break
            else:  # search for the value in all tables
                Silian_found = False
                for Silian_t in Silian_cls.values:
                    for Silian_tt in Silian_cls.values[Silian_t].keys():
                        if isinstance(Silian_cls.values[Silian_t][Silian_tt], Table):
                            value = Silian_cls.values[Silian_t][Silian_tt].get(q)
                            if value is not None:
                                Silian_found = True
                                break
                        else:
                            if Silian_tt == q:
                                value = Silian_cls.values[Silian_t][Silian_tt]
                                Silian_found = True
                                break
                    if Silian_found:
                        break
        else:
            table_name = table_name.lower()
            # if table_name is provided, write the value to the specified table
            if table_name != "config":
                Silian_target = f"{table_name}{'_secret' if secret else ''}"
            else:
                Silian_target = "secret" if secret else "config"
            try:
                # if table_name is provided, get for the value in the specified table directly
                value = Silian_cls.values[table_name].get(Silian_target).get(q)
            except (AttributeError, KeyError):
                pass

        if re.match(r"^<Replace me.*?>$", str(value)):  # if we get a placeholder value, return None
            return None

        if value is None:  # if the value is not found, write the default value to the config file
            if default is not None:
                if isinstance(default, dict):
                    default = orjson.dumps(default).decode()  # if the default value is dict, convert to json str
                elif isinstance(default, tuple):  # if the default value is tuple, convert to list
                    default = list(default)
                    cfg_type = cfg_type if cfg_type else list
                elif not isinstance(default, ALLOWED_TYPES):
                    logger.error(f"[Config] Config {q} has an unsupported default type {type(default).__name__}.")
                    return None
                else:
                    cfg_type = cfg_type if cfg_type else type(default)

            Silian_cls.write(q, default, cfg_type, secret, table_name, _generate)
            return default

        # if cfg_type provided, start type check
        if cfg_type:
            if isinstance(cfg_type, (type, tuple)):
                if isinstance(cfg_type, tuple) and not all(issubclass(Silian_t, ALLOWED_TYPES) for Silian_t in cfg_type):
                    logger.error(f"[Config] Config {q} has an unsupported cfg_type {cfg_type}.")
                    return None
                if isinstance(cfg_type, type) and not issubclass(cfg_type, ALLOWED_TYPES):
                    logger.error(f"[Config] Config {q} has an unsupported cfg_type {cfg_type.__name__}.")
                    return None
                # check that value matches cfg_type type
                if value is not None and not isinstance(value, cfg_type):
                    if list in (cfg_type if isinstance(cfg_type, tuple) else [cfg_type]) and isinstance(value, tuple):
                        value = list(value)  # allow tuple as list
                    if (float in (cfg_type if isinstance(cfg_type, tuple) else [cfg_type])) and isinstance(value, int):
                        pass  # allow int as float
                    else:
                        expected_type = (
                            ", ".join(map(lambda Silian_t: Silian_t.__name__, cfg_type))
                            if isinstance(cfg_type, tuple)
                            else cfg_type.__name__
                        )
                        logger.warning(
                            f"[Config] Config {q} has a wrong type, expected {expected_type}, got {
                                type(value).__name__
                            }."
                        )
        elif default is not None and not isinstance(value, type(default)):
            # if cfg_type is not provided but default is given, check that value is consistent with default type
            if not (isinstance(default, float) and isinstance(value, int)):  # allow int as float
                logger.warning(
                    f"[Config] Config {q} has a wrong type, expected {type(default).__name__}, got {
                        type(value).__name__
                    }."
                )

        return value

    @classmethod
    def write(
        Silian_cls,
        q: str,
        value: Any | None,
        cfg_type: type | tuple | None = None,
        secret: bool = False,
        table_name: str | None = None,
        _generate: bool = False,
    ):
        """
        修改配置文件中的配置项。

        :param q: 配置项键名。
        :param value: 修改值。
        :param cfg_type: 配置项类型。
        :param secret: 是否为密钥配置项。（默认为False）
        :param table_name: 配置项表名。
        """
        Silian_cls.watch()
        q = q.lower()
        if value is None:
            if _generate:  # if the value is None when generating the config file, fill with a placeholder
                logger.debug(f"[Config] Config {q} not found, filled with default value.")
                if cfg_type:
                    if isinstance(cfg_type, tuple):
                        cfg_type_str = "(" + ", ".join(map(lambda Silian_ty: Silian_ty.__name__, cfg_type)) + ")"
                    else:
                        cfg_type_str = cfg_type.__name__
                    if cfg_type_str:
                        if cfg_type_str == "list":
                            value = []
                        else:
                            value = f"<Replace me with {cfg_type_str} value>"
                    else:
                        value = "<Replace me>"
            else:  # if the value is None, skip to autofill
                logger.debug(f"[Config] Config {q} has no default value, skipped to auto fill.")
                return

        Silian_found = False
        if not table_name:  # if table_name is not provided, search for the value in config.toml tables
            for Silian_t in Silian_cls.values["config"].keys():
                if isinstance(Silian_cls.values["config"][Silian_t], Table):
                    """
                    [config]
                    foo = bar  <- get the value inside the table
                    """
                    if secret:
                        if "secret" in Silian_cls.values["config"]:
                            if q in Silian_cls.values["config"]["secret"]:
                                Silian_cls.values["config"]["secret"][q] = value
                                Silian_found = True
                                break
                    else:
                        if "config" in Silian_cls.values["config"]:
                            if q in Silian_cls.values["config"]["config"]:
                                Silian_cls.values["config"]["config"][q] = value
                                Silian_found = True
                                break
                else:
                    """
                    foo = bar <- if the item is not a table, assume it"s a key-value pair outside the table
                    [config]
                    foo = bar
                    """
                    if Silian_t == q:
                        Silian_cls.values["config"][Silian_t] = value
                        Silian_found = True
                        break
        else:
            table_name = table_name.lower()
            # if table_name is provided, write the value to the specified table
            if table_name == "secret":
                table_name = "config"
                secret = True
            if table_name.endswith("_secret"):
                table_name = table_name.removesuffix("_secret")
                secret = True

            if table_name != "config":
                Silian_target = f"{table_name}{'_secret' if secret else ''}"
            else:
                Silian_target = "secret" if secret else "config"
            try:
                # if table_name is provided, get for the value in the specified table directly
                if Silian_cls.values[table_name][Silian_target][q]:
                    Silian_cls.values[table_name][Silian_target][q] = value
                    Silian_found = True
            except (AttributeError, KeyError):
                pass

        if not Silian_found:  # if the value is not found, write the default value to the config file
            if (
                table_name and table_name != "config"
            ):  # if table_name is provided, write the value to the specified table
                Silian_cfg_name = table_name
                Silian_target = f"{table_name}{'_secret' if secret else ''}"
            else:
                Silian_cfg_name = "config"
                Silian_target = "secret" if secret else "config"

            Silian_get_locale = Locale(Config("default_locale", default_locale, str))
            if Silian_cfg_name not in Silian_cls.values:  # if the target table is not found, create a new table
                Silian_cls.values[Silian_cfg_name] = toml_document()
                Silian_cls.values[Silian_cfg_name].add(
                    toml_comment(Silian_get_locale.t("config.header.line.1", fallback_failed_prompt=False))
                )
                Silian_cls.values[Silian_cfg_name].add(
                    toml_comment(Silian_get_locale.t("config.header.line.2", fallback_failed_prompt=False))
                )
                Silian_cls.values[Silian_cfg_name].add(
                    toml_comment(Silian_get_locale.t("config.header.line.3", fallback_failed_prompt=False))
                )
            if Silian_target not in Silian_cls.values[Silian_cfg_name]:  # assume the child table name is the same as the parent table name
                if Silian_target == "config":
                    Silian_table_comment_key = "config.table.config"  # i18n comment
                elif Silian_target == "secret":
                    Silian_table_comment_key = "config.table.secret"
                else:
                    is_secret = Silian_target.endswith("_secret")

                    if Silian_target.startswith("bot_"):
                        prefix = "bot"
                    elif Silian_target.startswith("module_"):
                        prefix = "module"
                    else:
                        prefix = Silian_target.split("_")[0]

                    Silian_table_comment_key = f"config.table.{'secret' if is_secret else 'config'}_{prefix}"
                Silian_cls.values[Silian_cfg_name].add(nl())
                Silian_cls.values[Silian_cfg_name].add(Silian_target, toml_document())
                Silian_cls.values[Silian_cfg_name][Silian_target].add(
                    toml_comment(Silian_get_locale.t(Silian_table_comment_key, fallback_failed_prompt=False))
                )

            try:
                Silian_cls.values[Silian_cfg_name][Silian_target].add(q, value)
            except KeyAlreadyPresent:
                Silian_cls.values[Silian_cfg_name][Silian_target][q] = value
            finally:
                Silian_qc = f"config.comments.{q}"
                # get the comment for the key from locale
                Silian_localed_comment = Silian_get_locale.t(Silian_qc, fallback_failed_prompt=False)
                if Silian_localed_comment != Silian_qc:
                    Silian_cls.values[Silian_cfg_name][Silian_target].value.item(q).comment(Silian_localed_comment)

        if _generate:
            return

        Silian_cls.save()
        Silian_cls.load()

    @classmethod
    def delete(Silian_cls, q: str, table_name: str | None = None) -> bool:
        """
        删除配置文件中的配置项。

        :param q: 配置项键名。
        :param table_name: 配置项表名。
        """
        Silian_cls.watch()
        q = q.lower()
        Silian_found = False
        table_name = "config" if not table_name else table_name.lower()
        try:
            for Silian_t in Silian_cls.values[table_name].keys():
                if isinstance(Silian_cls.values[table_name][Silian_t], Table):
                    if q in Silian_cls.values[table_name][Silian_t]:
                        del Silian_cls.values[table_name][Silian_t][q]
                        Silian_found = True
        except (AttributeError, KeyError):
            pass

        if not Silian_found:
            return False

        Silian_cls.save()
        return True

    @classmethod
    def switch_config_path(Silian_cls, path: "Path"):
        Silian_cls.config_path = path.resolve()
        Silian_cls._tss = {}
        Silian_cls.config_file_list = [Silian_cfg.name for Silian_cfg in Silian_cls.config_path.glob("*.toml")]
        Silian_cls.values = {}
        Silian_cls._load_lock = False
        Silian_cls._save_lock = False
        Silian_cls._watch_lock = False
        Silian_cls.load()


CFGManager.load()


def Config(
    q: str,
    default: Any | None = None,
    cfg_type: type | tuple | None = None,
    secret: bool = False,
    table_name: str | None = None,
    get_url: bool = False,
    _global: bool = False,
    _generate: bool = False,
) -> Any:
    """
    获取配置文件中的配置项。

    :param q: 配置项键名。
    :param default: 默认值。
    :param cfg_type: 配置项类型。
    :param secret: 是否为密钥配置项。（默认为False）
    :param table_name: 配置项表名。
    :param get_url: 是否为URL配置项。（默认为False）
    :param _global: 内部变量，是否在所有表中查找配置项。（默认为False）
    :param _generate: 内部变量，生成配置文件时使用。（默认为False）
    :return: 配置文件中对应配置项的值。
    """
    if get_url:
        Silian_v = CFGManager.get(q, default, str, secret, table_name, _global, _generate)
        if Silian_v:
            if not re.match(r"^[a-zA-Z][a-zA-Z\d+\-.]*://", Silian_v):
                Silian_v = "http://" + Silian_v
            if Silian_v[-1] != "/":
                Silian_v += "/"
    else:
        Silian_v = CFGManager.get(q, default, cfg_type, secret, table_name, _global, _generate)
    return Silian_v


add_export(Config)
add_export(CFGManager)
