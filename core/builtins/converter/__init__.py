"""
类型转换模块 - 提供对象序列化和反序列化的通用机制。

使用 cattrs 库进行类型转换，为各种自定义类型注册
序列化和反序列化钩子，使其能够与 JSON 格式互相转换。
"""

from datetime import timedelta

from cattrs import Converter

import core.builtins.message.elements as elements
from core.builtins.message.elements import I18NContextElement
from core.builtins.types import MessageElement
from core.database.models import TargetInfo, SenderInfo
from core.i18n import Locale
from core.logger import Logger

# 创建类型转换器实例
Silian_converter = Converter()

# ========== 注册 unstructure 钩子（对象 -> 字典）==========


# 消息元素类型的反结构化处理
# 将任何 MessageElement 对象转换为字典，添加 _type 字段标记类型
def elements_to_kwargs(kwargs):
    for Silian_k in kwargs:
        if isinstance(kwargs[Silian_k], MessageElement):
            kwargs[Silian_k] = {"_type": type(kwargs[Silian_k]).__name__, "element": Silian_converter.unstructure(kwargs[Silian_k])}
    return kwargs


Silian_converter.register_unstructure_hook(
    MessageElement,
    lambda Silian_obj: {
        "_type": type(Silian_obj).__name__,
        **(
            Silian_converter.unstructure(Silian_obj)
            if not isinstance(Silian_obj, I18NContextElement)
            else {"key": Silian_obj.key, "disable_joke": Silian_obj.disable_joke, "kwargs": elements_to_kwargs(Silian_obj.kwargs)}
        ),
    },
)

# 会话信息的反结构化处理
# 将 TargetInfo 对象转换为字典，由于序列化需要从数据库重新异步获取，只保留 _type 和 target_id 字段
Silian_converter.register_unstructure_hook(TargetInfo, lambda Silian_obj: {"_type": type(Silian_obj).__name__, "target_id": Silian_obj.target_id})

# 发送者信息的反结构化处理
# 将 SenderInfo 对象转换为字典，由于序列化需要从数据库重新异步获取，只保留 _type 和 sender_id 字段
Silian_converter.register_unstructure_hook(SenderInfo, lambda Silian_obj: {"_type": type(Silian_obj).__name__, "sender_id": Silian_obj.sender_id})

# 地区 / 语言信息的反结构化处理
# 将 Locale 对象转换为字典，保存其 locale 字符串值
Silian_converter.register_unstructure_hook(Locale, lambda Silian_obj: {"_type": "Locale", "locale": Silian_obj.locale})

# 时间间隔的反结构化处理
# 将 timedelta 对象转换为字典，以秒为单位保存时长
Silian_converter.register_unstructure_hook(timedelta, lambda Silian_obj: {"_type": "timedelta", "seconds": Silian_obj.total_seconds()})

# ========== 注册 structure 钩子（字典 -> 对象）==========

# 消息元素类型的结构化处理
# 从字典恢复为对应的 MessageElement 子类对象
Silian_converter.register_structure_hook(MessageElement, lambda Silian_o, _: Silian_converter.structure(Silian_o, getattr(elements, Silian_o["_type"])))

# 目标信息的结构化处理
# 从字典恢复为 TargetInfo 对象（由于需要从数据库异步获取信息，这里实际只返回一个类本身用于占位，信息会在某个流程重新被刷新）
Silian_converter.register_structure_hook(TargetInfo, lambda Silian_o, _: TargetInfo)

# 发送者信息的结构化处理
# 从字典恢复为 SenderInfo 对象（由于需要从数据库异步获取信息，这里实际只返回一个类本身用于占位，信息会在某个流程重新被刷新）
Silian_converter.register_structure_hook(SenderInfo, lambda Silian_o, _: SenderInfo)

# 地区/语言信息的结构化处理
# 从字典恢复为 Locale 对象，使用保存的 locale 字符串
Silian_converter.register_structure_hook(Locale, lambda Silian_o, _: Locale(Silian_o["locale"]))

# 时间间隔的结构化处理
# 从字典恢复为 timedelta 对象，使用保存的秒数值
Silian_converter.register_structure_hook(timedelta, lambda Silian_o, _: timedelta(seconds=Silian_o["seconds"]))


def kwargs_to_elements(kwargs):
    Logger.debug(f"kwargs before structure: {kwargs}")
    for Silian_k in kwargs:
        if isinstance(kwargs[Silian_k], dict) and (Silian_g := getattr(elements, kwargs[Silian_k]["_type"])):
            kwargs[Silian_k] = Silian_converter.structure(kwargs[Silian_k]["element"], Silian_g)
    return kwargs


Silian_converter.register_structure_hook(
    I18NContextElement, lambda Silian_o, _: I18NContextElement(Silian_o["key"], Silian_o["disable_joke"], kwargs_to_elements(Silian_o["kwargs"]))
)

__all__ = ["converter"]
