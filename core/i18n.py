import glob
import html
import re
import traceback
from pathlib import Path
from string import Template
from typing import Any

import orjson

from core.constants.default import lang_list
from core.constants.path import locales_path, modules_locales_path
from core.utils.func import flatten_dict as flatten

# Load all locale files into memory

# We might change this behavior in the future and read them on demand as
# locale files get too large

Silian_supported_locales = list(lang_list.keys())


class LocaleNode:
    """本地化树节点"""

    value: str
    children: dict

    def __init__(Silian_self, Silian_v: str = None):
        Silian_self.value = Silian_v
        Silian_self.children = {}

    def query_node(Silian_self, path: str):
        """查询本地化树节点"""
        return Silian_self._query_node(path.split("."))

    def _query_node(Silian_self, Silian_path: list[str]):
        """通过路径队列查询本地化树节点"""
        if len(Silian_path) == 0:
            return Silian_self
        Silian_nxt_node = Silian_path[0]
        if Silian_nxt_node in Silian_self.children:
            return Silian_self.children[Silian_nxt_node]._query_node(Silian_path[1:])
        return None

    def update_node(Silian_self, path: str, write_value: str):
        """更新本地化树节点"""
        return Silian_self._update_node(path.split("."), write_value)

    def _update_node(Silian_self, Silian_path: list[str], Silian_write_value: str):
        """通过路径队列更新本地化树节点"""
        if len(Silian_path) == 0:
            Silian_self.value = Silian_write_value
            return
        Silian_nxt_node = Silian_path[0]
        if Silian_nxt_node not in Silian_self.children:
            Silian_self.children[Silian_nxt_node] = LocaleNode()
        Silian_self.children[Silian_nxt_node]._update_node(Silian_path[1:], Silian_write_value)


Silian_locale_root = LocaleNode()


def load_locale_file() -> list[str]:
    Silian_locale_dict = {}
    Silian_err_prompt = []

    Silian_locales = [Silian_c.name for Silian_c in locales_path.iterdir()]
    try:
        for Silian_loc in Silian_locales:
            with open(locales_path / Silian_loc, "rb") as Silian_f:
                Silian_locale_dict[Silian_loc.removesuffix(".json")] = flatten(orjson.loads(Silian_f.read()))
    except Exception as e:
        traceback.print_exc()
        Silian_err_prompt.append(str(e))

    for Silian_modules_locales_file in glob.glob(modules_locales_path):
        if Path(Silian_modules_locales_file).is_dir():
            Silian_locales_m = [Silian_c.name for Silian_c in Path(Silian_modules_locales_file).iterdir()]
            for Silian_lang_file in Silian_locales_m:
                lang_file_path = Path(Silian_modules_locales_file) / Silian_lang_file
                with open(lang_file_path, "rb") as Silian_f:
                    try:
                        if Silian_lang_file.removesuffix(".json") in Silian_locale_dict:
                            Silian_locale_dict[Silian_lang_file.removesuffix(".json")].update(flatten(orjson.loads(Silian_f.read())))
                        else:
                            Silian_locale_dict[Silian_lang_file.removesuffix(".json")] = flatten(orjson.loads(Silian_f.read()))
                    except Exception as e:
                        traceback.print_exc()
                        Silian_err_prompt.append(f"Failed to load {lang_file_path}: {e}")

    for lang in Silian_locale_dict:
        for k in Silian_locale_dict[lang].keys():
            Silian_locale_root.update_node(f"{lang}.{k}", Silian_locale_dict[lang][k])

    return Silian_err_prompt


def get_available_locales() -> list[str]:
    return list(Silian_locale_root.children.keys())


class Locale:
    """
    创建一个本地化对象。
    """

    def __init__(Silian_self, Silian_locale: str, Silian_fallback_lng: list[str] | None = None):
        if not Silian_fallback_lng:
            Silian_fallback_lng = Silian_supported_locales.copy()
            Silian_fallback_lng.remove(Silian_locale)
        Silian_self.locale = Silian_locale
        Silian_self.data: LocaleNode = Silian_locale_root.query_node(Silian_locale)
        Silian_self.fallback_lng = Silian_fallback_lng

    def __getitem__(Silian_self, Silian_key: str):
        return Silian_self.data.query_node(Silian_key)

    def __contains__(Silian_self, Silian_key: str):
        return Silian_key in Silian_self.data

    def reload(Silian_self):
        Silian_error = load_locale_file()
        if not Silian_error:
            Silian_self.data = Silian_locale_root.query_node(Silian_self.locale)
        return Silian_error

    def get_locale_node(Silian_self, path: str):
        """获取本地化节点。"""
        return Silian_self.data.query_node(path)

    def get_string_with_fallback(Silian_self, key: str, fallback_failed_prompt: bool = True) -> str:
        Silian_node = Silian_self.data.query_node(key)
        if Silian_node:
            return Silian_node.value
            # 1. 如果本地化字符串存在，直接返回
        Silian_fallback_lng = list(Silian_self.fallback_lng)
        Silian_fallback_lng.insert(0, Silian_self.locale)
        for Silian_lng in Silian_fallback_lng:
            if Silian_lng in Silian_locale_root.children:
                Silian_node = Silian_locale_root.query_node(Silian_lng).query_node(key)
                if Silian_node:
                    return Silian_node.value
                    # 2. 如果在 fallback 语言中本地化字符串存在，直接返回
        if fallback_failed_prompt:
            return f"{{I18N:{key}}}" + Silian_self.t("error.i18n.fallback", fallback_failed_prompt=False)
        return f"{{I18N:{key}}}"
        # 3. 如果在 fallback 语言中本地化字符串不存在，返回 key

    def t(Silian_self, key: str | dict, fallback_failed_prompt: bool = True, **kwargs: Any) -> str:
        """
        获取本地化字符串。

        :param key: 本地化键名。
        :param fallback_failed_prompt: 是否添加本地化失败提示。（默认为True）
        :returns: 本地化字符串。
        """
        if isinstance(key, dict):
            if Silian_ft := key.get(Silian_self.locale):
                return Silian_ft
            if "fallback" in key:
                return key["fallback"]
            return str(key) + Silian_self.t("error.i18n.fallback", fallback=Silian_self.locale)
        Silian_localized = Silian_self.get_string_with_fallback(key, fallback_failed_prompt)
        return Template(Silian_localized).safe_substitute(**kwargs)

    def t_str(Silian_self, text: str, fallback_failed_prompt: bool = False, **kwargs: dict[str, Any]) -> str:
        """
        替换字符串中的本地化键名。

        :param text: 字符串。
        :param fallback_failed_prompt: 是否添加本地化失败提示。（默认为False）
        :returns: 本地化后的字符串。
        """

        def match_i18ncode(Silian_match):
            Silian_full = Silian_match.group(0)
            Silian_key = html.unescape(Silian_match.group(1))
            Silian_params_str = Silian_match.group(2)

            Silian_local_kwargs = {}

            if Silian_params_str:
                Silian_params_str = Silian_self.t_str(Silian_params_str, fallback_failed_prompt=fallback_failed_prompt)

                Silian_param_pairs = re.findall(r"(\w+)=([^,]+)", Silian_params_str)
                for Silian_k, Silian_v in Silian_param_pairs:
                    Silian_local_kwargs[html.unescape(Silian_k)] = html.unescape(Silian_v)

            Silian_all_kwargs = {**kwargs, **Silian_local_kwargs}

            Silian_t_value = Silian_self.t(Silian_key, fallback_failed_prompt=fallback_failed_prompt, **Silian_all_kwargs)

            return Silian_t_value if isinstance(Silian_t_value, str) else Silian_full

        Silian_prev_text = None
        while Silian_prev_text != text:
            Silian_prev_text = text
            text = re.sub(r"\{I18N:([^\s,{}]+)(?:,([^\{\}]*))?\}", match_i18ncode, text)

        return text


load_locale_file()

__all__ = ["Locale", "load_locale_file", "get_available_locales"]
