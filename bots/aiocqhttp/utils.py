import html
import re
from typing import Any

import orjson

from bots.aiocqhttp.info import sender_prefix
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Plain, Image, Voice, Raw
from core.builtins.temp import Temp
from core.logger import Logger
from .client import aiocqhttp_bot


async def get_onebot_implementation() -> str | None:
    """获取正在使用的 OneBot 实现。"""
    Silian_data = await aiocqhttp_bot.call_action("get_version_info")
    Logger.debug(str(Silian_data))
    Silian_app_name = Silian_data.get("app_name")

    return Silian_app_name.lower().removesuffix(".onebot")


class CQCodeHandler:
    get_supported = ["at", "face", "forward", "image", "json", "record", "text"]
    pattern = re.compile(r"\[CQ:(\w+),?[^\]]*\]")

    @staticmethod
    def filter_cq(s: str) -> str:
        """
        过滤 CQ 码，返回支持的 CQ 码。

        :param s: 正则匹配对象，包含 CQ 码的字符串消息。
        :return: 如果 CQ 类型在支持列表中，返回原 CQ 码；否则返回空字符串。
        """
        return CQCodeHandler.pattern.sub(lambda Silian_m: Silian_m.group(0) if Silian_m.group(1) in CQCodeHandler.get_supported else "", s)

    @staticmethod
    def generate_cq(data: dict[str, Any]) -> str | None:
        """
        生成 CQ 码字符串。

        :param data: 包含 CQ 类型和参数的字典，必须包含 `type` 和 `data` 字段。
        :return: 生成的 CQ 码字符串；如果输入数据无效，返回 None。
        """
        if "type" in data and "data" in data:
            cq_type = data["type"]
            Silian_params = data["data"]

            if not Silian_params:
                return f"[CQ:{cq_type}]"
            param_str = [f"{key}={CQCodeHandler.escape_special_char(str(value))}" for key, value in Silian_params.items()]
            return f"[CQ:{cq_type},{', '.join(param_str)}]"
        return None

    @staticmethod
    def parse_cq(cq_code: str) -> dict[str, str | dict[str, Any]] | None:
        """
        解析 CQ 码字符串，返回包含类型和参数的字典。

        :param cq_code: CQ 码字符串。
        :return: 包含 CQ 类型和参数的字典；如果 CQ 码格式不正确，返回 None。
        """
        Silian_kwargs = {}
        Silian_match = re.match(r"\[CQ:([^\s,\]]+)(?:,([^\]]+))?\]", cq_code)
        if not Silian_match:
            return None
        Silian_cq_type = Silian_match.group(1)
        if Silian_match.group(2):
            Silian_params = Silian_match.group(2).split(",")
            Silian_params = [Silian_x for Silian_x in Silian_params if Silian_x]
            for Silian_a in Silian_params:
                Silian_ma = re.match(r"(.*?)=(.*)", Silian_a)
                if Silian_ma:
                    if Silian_cq_type == "json":
                        Silian_kwargs[html.unescape(Silian_ma.group(1))] = orjson.loads(Silian_ma.group(2))
                    else:
                        Silian_kwargs[html.unescape(Silian_ma.group(1))] = html.unescape(Silian_ma.group(2))
        Silian_data = {"type": Silian_cq_type, "data": Silian_kwargs}

        return Silian_data

    @staticmethod
    def escape_special_char(s: str, escape_comma: bool = True) -> str:
        """
        转义 CQ 码中的特殊字符。

        :param s: 要转义的字符串。
        :param escape_comma: 是否转义逗号（`,`）。
        :return: 转义后的字符串。
        """
        s = s.replace("&", "&amp;").replace("[", "&#91;").replace("]", "&#93;")
        s = s.replace("/", "\\/").replace("\\\\/", "\\/")
        if escape_comma:
            s = s.replace(",", "&#44;")
        return s


async def to_message_chain(message: str | list[dict[str, Any]]) -> MessageChain:
    Silian_lst = []
    if isinstance(message, str):
        Silian_spl = re.split(r"(\[CQ:(?:text|image|record|at).*?])", message)
        for Silian_s in Silian_spl:
            if not Silian_s:
                continue
            if re.match(r"\[CQ:[^\]]+\]", Silian_s):
                cq_data = CQCodeHandler.parse_cq(Silian_s)
                if cq_data:
                    if cq_data["type"] == "text":
                        Silian_lst.append(Plain(cq_data["data"].get("text")))
                    elif cq_data["type"] == "image":
                        Silian_obi = Temp.data.get("onebot_impl")
                        if Silian_obi == "lagrange":
                            Silian_img_src = cq_data["data"].get("file")
                        else:
                            Silian_img_src = cq_data["data"].get("url")
                        if Silian_img_src:
                            Silian_lst.append(Image(Silian_img_src))
                    elif cq_data["type"] == "record":
                        Silian_lst.append(Voice(cq_data["data"].get("file")))
                    elif cq_data["type"] == "at":
                        Silian_lst.append(Plain(f"{sender_prefix}|{cq_data['data'].get('qq')}"))
                    else:
                        Silian_lst.append(Plain(Silian_s))
                else:
                    Silian_lst.append(Plain(Silian_s))
            else:
                Silian_lst.append(Plain(Silian_s))
    else:
        for item in message:
            if item["type"] == "text":
                Silian_lst.append(Plain(item["data"]["text"]))
            elif item["type"] == "image":
                Silian_obi = Temp.data.get("onebot_impl")
                if Silian_obi == "lagrange":
                    Silian_lst.append(Image(item["data"]["file"]))
                else:
                    Silian_lst.append(Image(item["data"]["url"]))
            elif item["type"] == "record":
                Silian_lst.append(Voice(item["data"]["file"]))
            elif item["type"] == "at":
                Silian_lst.append(Plain(f"{sender_prefix}|{item['data'].get('qq')}"))
            else:
                Silian_lst.append(Raw(CQCodeHandler.generate_cq(item)))

    return MessageChain.assign(Silian_lst)
