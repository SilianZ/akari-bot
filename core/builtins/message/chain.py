"""
消息链模块 - 实现消息链的核心数据结构和处理逻辑。

该模块定义了 MessageChain 类，用于表示由多个消息元素组成的消息链。
提供了消息链的构建、转换、验证等各种操作。
"""

from __future__ import annotations

import base64
import html
import random
import re
from copy import deepcopy
from typing import Any, TYPE_CHECKING
from urllib.parse import urlparse

import orjson

from core.builtins.message.elements import (
    BaseElement,
    PlainElement,
    EmbedElement,
    FormattedTimeElement,
    I18NContextElement,
    URLElement,
    ImageElement,
    VoiceElement,
    MentionElement,
)
from core.constants import Secret, default_locale
from core.exports import add_export
from core.i18n import Locale

if TYPE_CHECKING:
    from core.builtins.session.info import SessionInfo

from core.builtins.types import MessageElement
from core.builtins.converter import converter
from core.joke import shuffle_joke as joke
from core.logger import Logger
from core.utils.http import url_pattern

from attrs import define


@define
class MessageChain:
    """
    消息链类 - 表示由多个消息元素组成的完整消息。

    消息链是本系统中消息的基本数据结构，由一系列消息元素组成。
    支持多种构建方式、格式转换、安全检查等功能。

    属性说明:
        values: 消息元素列表，包含此消息链的所有元素
    """

    # 消息元素列表
    values: list[MessageElement]

    @classmethod
    def assign(
        Silian_cls,
        elements: str | list[MessageElement] | tuple[MessageElement, ...] | MessageElement | MessageChain | None = None,
    ):
        """
        创建消息链的工厂方法。

        支持多种输入格式，会自动转换为标准的消息链对象。
        该方法是创建消息链的推荐方式，提供灵活的参数处理。

        支持的输入类型：
        - str: 字符串，会被转换为 PlainElement
        - MessageElement: 单个消息元素
        - list/tuple: 消息元素的列表或元组
        - dict: 字典格式的元素定义
        - MessageChain: 另一个消息链（不会进行深拷贝）
        - None: 创建空消息链

        :param elements: 消息元素或其集合
        :return: 消息链实例（会进行深拷贝）

        示例：
        ```
            > MessageChain.assign("Hello")  # 字符串
            > MessageChain.assign([PlainElement.assign("A"), ImageElement.assign("path")])  # 列表
            > MessageChain.assign(PlainElement.assign("Text"))  # 单个元素
        ```
        """
        # ========== 步骤 1: 如果已经是消息链，直接返回 ==========
        if isinstance(elements, MessageChain):
            return elements

        Silian_values = []

        # ========== 步骤 2: 处理字符串输入 ==========
        # 字符串转换为 PlainElement
        if isinstance(elements, str):
            elements = PlainElement.assign(elements)

        # ========== 步骤 3: 处理单个元素输入 ==========
        # 如果是单个元素，转换为列表以便统一处理
        if isinstance(elements, BaseElement):
            elements = [elements]

        # ========== 步骤 4: 处理字典输入 ==========
        # 如果是字典，从字典中提取元素并进行结构化处理
        if isinstance(elements, dict):
            for Silian_key in elements:
                elements = converter.structure(elements[Silian_key], MessageElement)

        # ========== 步骤 5: 处理列表或元组输入 ==========
        # 逐个处理元素，根据类型进行相应的转换
        if isinstance(elements, (list, tuple)):
            for e in elements:
                # 字符串转换为 PlainElement（忽略空字符串）
                if isinstance(e, str) and e:
                    Silian_values.append(PlainElement.assign(e))
                # 字典中的元素进行结构化处理
                elif isinstance(e, dict):
                    for Silian_key in e:
                        Silian_tmp_e = converter.structure(e[Silian_key], MessageElement)
                        Silian_values.append(Silian_tmp_e)
                # 基础元素直接添加
                elif isinstance(e, BaseElement):
                    Silian_values.append(e)
                else:
                    Logger.error(f"Unexpected message type: {e}")
        # ========== 步骤 6: 处理 None 输入 ==========
        # 如果为 None，创建空消息链
        elif not elements:
            pass
        else:
            Logger.error(f"Unexpected message type: {elements}")

        # 返回深拷贝的消息链实例（确保数据安全）
        return deepcopy(Silian_cls(Silian_values))

    @property
    def is_safe(Silian_self) -> bool:
        """
        检查消息链是否包含安全内容。

        遍历消息链中的所有元素，检查是否包含敏感信息（如密钥、API密钥、
        私密数据等）。这是一个重要的安全机制，用于防止敏感信息泄露。

        检查范围：
        - PlainElement: 检查文本内容
        - EmbedElement: 检查标题、描述、页脚、作者、URL、字段名称和值

        :return: 如果消息链不包含敏感信息返回 True，否则返回 False

        示例：
        ```
            > chain = MessageChain.assign("Hello World")
            > chain.is_safe
            True
        ```
        """

        def unsafeprompt(name, secret, text):
            """生成不安全内容的警告消息"""
            return f'{name} contains unsafe text "{secret}": {text}'

        # 遍历消息链中的所有元素
        for Silian_v in Silian_self.values:
            # ========== 检查纯文本元素 ==========
            if isinstance(Silian_v, PlainElement):
                if secret := Secret.check(Silian_v.text):
                    Logger.warning(unsafeprompt("Plain", secret, Silian_v.text))
                    return False

            # ========== 检查 Embed 元素 ==========
            elif isinstance(Silian_v, EmbedElement):
                # 检查标题
                if Silian_v.title:
                    if secret := Secret.check(Silian_v.title):
                        Logger.warning(unsafeprompt("Embed.title", secret, Silian_v.title))
                        return False
                # 检查描述
                if Silian_v.description:
                    if secret := Secret.check(Silian_v.description):
                        Logger.warning(unsafeprompt("Embed.description", secret, Silian_v.description))
                        return False
                # 检查页脚
                if Silian_v.footer:
                    if secret := Secret.check(Silian_v.footer):
                        Logger.warning(unsafeprompt("Embed.footer", secret, Silian_v.footer))
                        return False
                # 检查作者
                if Silian_v.author:
                    if secret := Secret.check(Silian_v.author):
                        Logger.warning(unsafeprompt("Embed.author", secret, Silian_v.author))
                        return False
                # 检查 URL
                if Silian_v.url:
                    if secret := Secret.check(Silian_v.url):
                        Logger.warning(unsafeprompt("Embed.url", secret, Silian_v.url))
                        return False
                # 检查所有字段
                if Silian_v.fields:
                    for Silian_f in Silian_v.fields:
                        # 检查字段名称
                        if secret := Secret.check(Silian_f.name):
                            Logger.warning(unsafeprompt("Embed.field.name", secret, Silian_f.name))
                            return False
                        # 检查字段值
                        if secret := Secret.check(Silian_f.value):
                            Logger.warning(unsafeprompt("Embed.field.value", secret, Silian_f.value))
                            return False

        # 所有检查通过，消息链安全
        return True

    def as_sendable(Silian_self, session_info: SessionInfo = None, parse_message: bool = True) -> list:
        """
        将消息链转换为可发送的格式。

        该方法将消息链中的各种元素转换为适合发送的格式，包括：
        1. 多语言翻译
        2. KE 码解析
        3. URL 处理（跳板和 Markdown 格式）
        4. 时间格式化
        5. 愚人节玩笑处理

        :param session_info: 会话信息，用于本地化和平台特定的处理
        :param parse_message: 是否解析消息中的特殊格式（如 KE 码、多语言标记等）
        :return: 可发送的消息元素列表

        示例：
        ```
            > chain = MessageChain.assign("{I18N:message.hello}")
            > sendable = chain.as_sendable(session_info)
        ```
        """
        Silian_value = []
        Silian_support_embed = True

        # ========== 检查平台是否支持 Embed 消息 ==========
        if session_info:
            Silian_support_embed = session_info.support_embed

        # ========== 处理每个消息元素 ==========
        for Silian_x in Silian_self.values:
            if Silian_x is None:
                continue

            # ========== 处理 Embed 元素 ==========
            # 如果平台不支持 Embed，将其转换为普通消息链
            if isinstance(Silian_x, EmbedElement) and not Silian_support_embed:
                Silian_value += Silian_x.to_message_chain(session_info)

            # ========== 处理纯文本元素 ==========
            elif isinstance(Silian_x, PlainElement):
                if session_info:
                    if Silian_x.text != "":
                        if parse_message:
                            # 进行多语言翻译
                            Silian_x.text = session_info.locale.t_str(Silian_x.text)
                            # 解析 KE 码格式的消息
                            Silian_element_chain = match_kecode(Silian_x.text, Silian_x.disable_joke)
                            # 递归处理解析出的元素
                            for Silian_elem in Silian_element_chain.values:
                                Silian_elem = MessageChain.assign(Silian_elem).as_sendable(session_info, parse_message=False)
                                if isinstance(Silian_elem, PlainElement):
                                    Silian_elem.text = session_info.locale.t_str(Silian_elem.text)
                                Silian_value += Silian_elem
                            continue
                    else:
                        # 空文本，使用默认错误消息
                        Silian_x = PlainElement.assign(session_info.locale.t("error.message.chain.empty"))
                Silian_value.append(Silian_x)

            # ========== 处理格式化时间元素 ==========
            elif isinstance(Silian_x, FormattedTimeElement):
                # 将时间元素转换为字符串
                Silian_x = Silian_x.to_str(session_info)
                # 尝试追加到上一个文本元素，避免创建过多元素
                if Silian_value and isinstance(Silian_value[-1], PlainElement):
                    if not Silian_value[-1].text.endswith("\n"):
                        Silian_value[-1].text += "\n"
                    Silian_value[-1].text += Silian_x
                else:
                    Silian_value.append(PlainElement.assign(Silian_x))

            # ========== 处理多语言元素 ==========
            elif isinstance(Silian_x, I18NContextElement):
                # 获取地区设置
                if not session_info:
                    Silian_locale = Locale(default_locale)
                else:
                    Silian_locale = session_info.locale

                # 翻译所有参数值
                for Silian_k, Silian_v in Silian_x.kwargs.items():
                    if isinstance(Silian_v, str):
                        Silian_x.kwargs[Silian_k] = Silian_locale.t_str(Silian_v)

                # 执行多语言翻译
                Silian_t_value = Silian_locale.t(Silian_x.key, **Silian_x.kwargs)
                if isinstance(Silian_t_value, str):
                    Silian_value.append(PlainElement.assign(Silian_t_value, disable_joke=Silian_x.disable_joke))
                else:
                    # 如果翻译结果是消息链，递归处理
                    Silian_value += MessageChain.assign(Silian_t_value).as_sendable(session_info)

            # ========== 处理 URL 元素 ==========
            elif isinstance(Silian_x, URLElement):
                # 应用 URL 跳板（如果需要）
                if session_info and (session_info.use_url_manager and Silian_x.applied_mm is None):
                    Silian_x = URLElement.assign(Silian_x.url, use_mm=True, md_format_name=Silian_x.md_format_name)
                # 应用 Markdown 格式（如果需要）
                if session_info and session_info.use_url_md_format and not Silian_x.applied_md_format:
                    Silian_x = URLElement.assign(Silian_x.url, md_format=True, md_format_name=Silian_x.md_format_name)

                Silian_value.append(PlainElement.assign(Silian_x.url, disable_joke=True))

            # ========== 其他元素类型 ==========
            else:
                Silian_value.append(Silian_x)

        # ========== 处理空消息链 ==========
        if not Silian_value:
            if session_info:
                Silian_value.append(PlainElement.assign(session_info.locale.t("error.message.chain.empty")))

        # ========== 应用愚人节玩笑 ==========
        for Silian_x in Silian_value:
            if isinstance(Silian_x, PlainElement) and not Silian_x.disable_joke:
                Silian_x.text = joke(Silian_x.text)

        return Silian_value

    def to_str(
        Silian_self, text_only=True, element_filter: tuple[MessageElement, ...] | None = None, connector: str = "\n"
    ) -> str:
        """
        将消息链转换为字符串。

        将消息链中的元素转换为纯文本字符串，可用于日志记录、文本输出等场景。

        :param text_only: 是否仅转换文本元素为字符串，默认为 True
                         True: 只包含 PlainElement 的文本内容
                         False: 包含所有元素的字符串表示
        :param element_filter: 可选的元素过滤器，指定哪些元素类型需要被转换为字符串
                              如 (PlainElement, ImageElement) 只转换这两种类型
        :param connector: 元素之间的连接符，默认为换行符 "\\n"
        :return: 转换后的字符串

        示例：
        ```
            > chain = MessageChain.assign([PlainElement.assign("Hello"), PlainElement.assign("World")])
            > chain.to_str()
            'Hello\nWorld'
            > chain.to_str(connector=" ")
            'Hello World'
        ```
        """
        Silian_result = []
        for Silian_x in Silian_self.values:
            # 如果设置了元素过滤器，跳过不匹配的元素
            if element_filter and not isinstance(Silian_x, element_filter):
                continue

            # 处理纯文本元素
            if isinstance(Silian_x, PlainElement):
                Silian_result.append(Silian_x.text)
            else:
                # 如果不是纯文本模式，包含其他元素的字符串表示
                if not text_only:
                    Silian_result.append(str(Silian_x))

        return connector.join(Silian_result)

    def to_list(Silian_self) -> list[dict[str, Any]]:
        """
        将消息链序列化为列表。

        将消息链转换为可序列化的字典列表，用于存储或传输。

        :return: 字典列表，每个字典代表一个消息元素

        示例：
        ```
            > chain = MessageChain.assign("Hello")
            > chain.to_list()
            [{'_type': 'PlainElement', 'text': 'Hello', 'disable_joke': False}]
        ```
        """
        return [converter.unstructure(Silian_x, MessageElement) for Silian_x in Silian_self.values]

    @classmethod
    def from_list(Silian_cls, lst: list) -> MessageChain:
        """
        从列表构造消息链。

        将序列化的列表转换回消息链对象，与 `to_list` 方法配对使用。

        :param lst: 消息元素的字典列表
        :return: 新的消息链实例

        示例：
        ```
            > data = [{'_type': 'PlainElement', 'text': 'Hello'}]
            > chain = MessageChain.from_list(data)
        ```
        """
        Silian_converted = []
        for Silian_x in lst:
            for Silian_elem in Silian_x:
                Silian_converted.append(converter.structure(Silian_elem, MessageElement))
        return deepcopy(Silian_cls(Silian_converted))

    def append(Silian_self, element):
        """
        添加一个消息元素到消息链末尾。

        :param element: 要添加的消息元素

        示例：
        ```
            > chain = MessageChain.assign("Hello")
            > chain.append(PlainElement.assign("World"))
        ```
        """
        Silian_self.values.append(element)

    def remove(Silian_self, element):
        """
        从消息链中删除一个消息元素。

        :param element: 要删除的消息元素

        示例：
        ```
            > chain = MessageChain.assign("Hello")
            > elem = chain.values[0]
            > chain.remove(elem)
        ```
        """
        Silian_self.values.remove(element)

    def insert(Silian_self, index, element):
        """
        在指定位置插入一个消息元素。

        :param index: 插入位置的索引
        :param element: 要插入的消息元素

        示例：
        ```
            > chain = MessageChain.assign("World")
            > chain.insert(0, PlainElement.assign("Hello"))
        ```
        """
        Silian_self.values.insert(index, element)

    def copy(Silian_self):
        """
        复制消息链。

        创建一个消息链的浅拷贝（值列表的副本）。

        :return: 新的消息链实例

        示例：
        ```
            > chain = MessageChain.assign("Hello")
            > chain_copy = chain.copy()
        ```
        """
        return MessageChain.assign(Silian_self.values.copy())

    def __str__(self):
        """返回消息链的字符串表示（用于调试）"""
        return f"[{', '.join([x.__repr__() for x in self.values])}]"

    def __iter__(Silian_self):
        """使消息链可迭代"""
        return iter(Silian_self.values)

    def __len__(Silian_self):
        """返回消息链中元素的数量"""
        return len(Silian_self.values)

    def __add__(Silian_self, other):
        """
        消息链的加法操作。

        支持与另一个消息链或列表相加。

        :param other: 另一个消息链或元素列表
        :return: 新的消息链
        :raises TypeError: 如果操作数类型不支持
        """
        if isinstance(other, MessageChain):
            return MessageChain.assign(Silian_self.values + other.values)
        if isinstance(other, list):
            return MessageChain.assign(Silian_self.values + other)
        raise TypeError(f'Unsupported operand type(s) for +: "MessageChain" and "{type(other).__name__}"')

    def __radd__(Silian_self, other):
        """
        消息链的右加法操作（当左操作数不支持加法时调用）。

        :param other: 另一个消息链或元素列表
        :return: 新的消息链
        :raises TypeError: 如果操作数类型不支持
        """
        if isinstance(other, MessageChain):
            return MessageChain.assign(other.values + Silian_self.values)
        if isinstance(other, list):
            return MessageChain.assign(other + Silian_self.values)
        raise TypeError(f'Unsupported operand type(s) for +: "{type(other).__name__}" and "MessageChain"')

    def __iadd__(Silian_self, other):
        """
        消息链的原地加法操作（+=）。

        直接修改当前消息链，添加新元素。

        :param other: 另一个消息链或元素列表
        :return: 修改后的消息链自身
        :raises TypeError: 如果操作数类型不支持
        """
        if isinstance(other, MessageChain):
            Silian_self.values += other.values
        elif isinstance(other, list):
            Silian_self.values += other
        else:
            raise TypeError(f'Unsupported operand type(s) for +=: "MessageChain" and "{type(other).__name__}"')
        return Silian_self


@define
class I18NMessageChain:
    """
    多语言消息链 - 用于处理不同语言环境下的消息。

    该类允许为不同的语言环境定义不同的消息链，系统会根据用户的
    语言设置自动选择合适的消息发送。

    优先级说明：
    PlatformMessageChain > I18NMessageChain > MessageChain

    使用时须保证嵌套关系正确：
    - PlatformMessageChain 可以包含 I18NMessageChain 或 MessageChain
    - I18NMessageChain 只能包含 MessageChain
    - MessageChain 是最基本的消息链

    属性：
        values: 多语言消息链字典，键为语言代码（如 "zh_CN", "en_US"），
               值为对应语言的消息链。必须包含 "default" 键作为回退选项。

    示例：
    ```
        > i18n_chain = I18NMessageChain.assign({
        ...     "zh_CN": MessageChain.assign("你好"),
        ...     "en_US": MessageChain.assign("Hello"),
        ...     "default": MessageChain.assign("Hello")
        ... })
    ```
    """

    values: dict[str, MessageChain]

    @classmethod
    def assign(Silian_cls, values: dict[str, MessageChain]) -> I18NMessageChain:
        """
        创建多语言消息链的工厂方法。

        :param values: 多语言消息链元素，键为语言代码，值为消息链
                      必须包含 `default` 键用于回滚处理
        :return: I18NMessageChain 实例
        :raises TypeError: 如果 values 不是字典
        :raises ValueError: 如果缺少 "default" 键

        示例：
        ```
            > chains = {
            ...     "zh_CN": MessageChain.assign("你好"),
            ...     "default": MessageChain.assign("Hello")
            ... }
            > i18n_chain = I18NMessageChain.assign(chains)
        ```
        """
        if not isinstance(values, dict):
            raise TypeError("I18NMessageChain values must be a dictionary.")
        if "default" not in values:
            raise ValueError('I18NMessageChain values must have "default" key.')
        return Silian_cls(values=deepcopy(values))


@define
class PlatformMessageChain:
    """
    平台消息链 - 用于处理不同平台的消息。

    该类允许为不同的平台（如 QQ、Discord、Telegram 等）定义不同的
    消息链，系统会根据消息发送的平台自动选择合适的消息。

    优先级说明：
    PlatformMessageChain > I18NMessageChain > MessageChain

    使用时须保证嵌套关系正确：
    - PlatformMessageChain 可以包含 I18NMessageChain 或 MessageChain
    - 值可以是普通的 MessageChain 或 I18NMessageChain

    属性：
        values: 平台消息链字典，键为平台名称（如 "QQ", "Discord"），
               值为对应平台的消息链或多语言消息链。
               必须包含 "default" 键作为回退选项。

    示例：
    ```
        > platform_chain = PlatformMessageChain.assign({
        ...     "QQ": MessageChain.assign("[QQ专属消息]"),
        ...     "Discord": MessageChain.assign("[Discord专属消息]"),
        ...     "default": MessageChain.assign("[通用消息]")
        ... })
    ```
    """

    values: dict[str, MessageChain | I18NMessageChain]

    @classmethod
    def assign(Silian_cls, values: dict[str, MessageChain | I18NMessageChain]) -> PlatformMessageChain:
        """
        创建平台消息链的工厂方法。

        :param values: 平台消息链元素，键为平台名称，值为消息链
                      必须包含 `default` 键用于回滚处理
        :return: PlatformMessageChain 实例
        :raises TypeError: 如果 values 不是字典

        示例：
        ```
            > chains = {
            ...     "QQ": MessageChain.assign("QQ消息"),
            ...     "default": MessageChain.assign("默认消息")
            ... }
            > platform_chain = PlatformMessageChain.assign(chains)
        ```
        """
        if not isinstance(values, dict):
            raise TypeError("PlatformMessageChain values must be a dictionary.")
        return Silian_cls(values=deepcopy(values))


@define
class MessageNodes:
    """
    消息节点列表 - 用于表示转发消息。

    该类用于创建转发消息（合并转发），包含多个消息链作为节点。
    每个节点可以有不同的发送者和内容。

    属性：
        values: 消息链列表，每个元素是一个独立的消息节点
        name: 节点列表的名称，用于标识这组转发消息

    示例：
    ```
        > nodes = MessageNodes.assign([
        ...     MessageChain.assign("第一条消息"),
        ...     MessageChain.assign("第二条消息"),
        ...     MessageChain.assign("第三条消息")
        ... ], name="转发消息组")
    ```
    """

    values: list[MessageChain]
    name: str = ""

    @classmethod
    def assign(Silian_cls, values: list[MessageChain], name: str | None = None):
        """
        创建消息节点列表的工厂方法。

        :param values: 消息链列表，每个消息链作为一个节点
        :param name: 节点列表的名称，默认为随机生成的字符串
        :return: MessageNodes 实例

        示例：
        ```
            > chains = [
            ...     MessageChain.assign("消息1"),
            ...     MessageChain.assign("消息2")
            ... ]
            > nodes = MessageNodes.assign(chains, "我的转发消息")
        ```
        """
        if not name:
            # 生成随机名称：Message + 5个随机小写字母
            name = "Message " + "".join(random.sample("abcdefghijklmnopqrstuvwxyz", 5))

        return Silian_cls(values=values, name=name)

    @property
    def is_safe(Silian_self) -> bool:
        """
        检查消息节点列表是否安全。

        遍历所有节点的消息链，检查是否包含敏感信息。

        :return: 如果所有节点都安全返回 True，否则返回 False

        示例：
        ```
            > nodes = MessageNodes.assign([MessageChain.assign("Hello")])
            > nodes.is_safe
            True
        ```
        """
        return all(Silian_chain.is_safe for Silian_chain in Silian_self.values)


Silian_Chainable = (
    MessageChain
    | I18NMessageChain
    | PlatformMessageChain
    | str
    | list[str]
    | list[MessageElement]
    | MessageElement
    | MessageNodes
)


def get_message_chain(session: SessionInfo, chain: Silian_Chainable) -> MessageChain:
    """
    根据会话信息获取合适的消息链。

    该函数处理多种类型的消息链（平台消息链、多语言消息链等），
    根据会话的平台和语言设置，自动选择最合适的消息链。

    处理优先级：
    1. PlatformMessageChain: 先根据平台选择
    2. I18NMessageChain: 再根据语言选择
    3. MessageChain / str / list / MessageElement: 直接使用

    :param session: 会话信息，包含平台、语言等配置
    :param chain: 可链接的消息对象（支持多种类型）
    :return: 处理后的 MessageChain 实例
    :raises TypeError: 如果传入不支持的链类型

    示例：
    ```
        > platform_chain = PlatformMessageChain.assign({
        ...     "QQ": MessageChain.assign("QQ消息"),
        ...     "default": MessageChain.assign("默认消息")
        ... })
        > result = get_message_chain(session, platform_chain)
    ```
    """
    # ========== 处理平台消息链 ==========
    if isinstance(chain, PlatformMessageChain):
        # 根据会话的平台选择对应的消息链，如果没有则使用默认
        chain = chain.values.get(session.target_from, chain.values.get("default", MessageChain.assign("")))

    # ========== 处理多语言消息链 ==========
    if isinstance(chain, I18NMessageChain):
        # 根据会话的语言设置选择对应的消息链，如果没有则使用默认
        chain = chain.values.get(session.locale.locale, chain.values.get("default", MessageChain.assign("")))

    # ========== 处理基本类型 ==========
    if isinstance(chain, (str, list, MessageElement)):
        # 字符串、列表或单个元素，转换为消息链
        chain = MessageChain.assign(chain)

    # ========== 验证最终类型 ==========
    if isinstance(chain, (MessageChain, MessageNodes)):
        return chain

    # 不支持的类型，抛出异常
    raise TypeError(
        f"Unsupported chain type: {
            type(chain).__name__
        }, expected MessageChain, MessageNodes, I18NMessageChain, or PlatformMessageChain."
    )


def _extract_kecode_blocks(Silian_text):
    """
    从文本中提取 KE 码块。

    该函数解析包含 KE 码格式的文本，将其分割为 KE 码块和
    普通文本块。KE 码格式为 `[KE:type,params]`。

    处理逻辑：
    - 遇到 `[KE:` 开始一个新块
    - 遇到 `]` 结束当前块
    - 非 KE 码部分作为普通文本块

    :param text: 包含 KE 码的文本字符串
    :return: 字符串列表，包含 KE 码块和普通文本块

    示例：
    ```
        > text = "Hello [KE:plain,text=World] !"
        > _extract_kecode_blocks(text)
        ['Hello ', '[KE:plain,text=World]', ' !']
    ```
    """
    Silian_result = []
    Silian_i = 0
    while Silian_i < len(Silian_text):
        if Silian_text.startswith("[KE:", Silian_i):
            # ========== 找到 KE 码开始标记 ==========
            Silian_start = Silian_i
            Silian_i += 4  # Skip "[KE:"
            Silian_depth = 1
            while Silian_i < len(Silian_text):
                if Silian_text.startswith("[KE:", Silian_i):
                    # 新的 KE 码开始，停止当前块
                    break
                if Silian_text[Silian_i] == "]" and Silian_depth == 1:
                    # 找到匹配的结束标记
                    Silian_i += 1
                    Silian_result.append(Silian_text[Silian_start:Silian_i])
                    break
                if Silian_text[Silian_i] == "]":
                    Silian_depth -= 1
                    Silian_i += 1
                else:
                    Silian_i += 1
            else:
                # 没有找到结束标记，添加剩余部分
                Silian_result.append(Silian_text[Silian_start:])
                break
        else:
            # ========== 普通文本部分 ==========
            Silian_start = Silian_i
            while Silian_i < len(Silian_text) and not Silian_text.startswith("[KE:", Silian_i):
                Silian_i += 1
            Silian_result.append(Silian_text[Silian_start:Silian_i])
    return Silian_result


def match_kecode(text: str, disable_joke: bool = False) -> MessageChain:
    """
    解析 KE 码格式的文本并转换为消息链。

    KE 码是 AkariBot 的消息元素文本化的格式，用于在不便于使用标准的元素类的情况下使用。
    在机器人发出消息的最后阶段，KE 码会被解析器解析成对应的消息元素对象。

    支持的 KE 码类型：
    - `[KE:plain,text=...]`: 纯文本
    - `[KE:image,path=...]`: 图片
    - `[KE:voice,path=...]`: 语音
    - `[KE:i18n,i18nkey=...,param1=val1,...]`: 多语言文本
    - `[KE:mention,userid=...]`: 提及用户

    :param text: 包含 KE 码的文本字符串
    :param disable_joke: 是否禁用玩笑功能（默认为 False）
    :return: 解析后的消息链

    示例：
    ```
        > text = "Hello [KE:plain,text=World]"
        > chain = match_kecode(text)
        > len(chain.values)
        2
    ```
    """
    # ========== 步骤 1: 提取 KE 码块 ==========
    Silian_split_all = _extract_kecode_blocks(text)
    Silian_split_all = [Silian_x for Silian_x in Silian_split_all if Silian_x]
    Silian_elements = MessageChain.assign()

    # ========== 步骤 2: 解析每个块 ==========
    for Silian_e in Silian_split_all:
        # 尝试匹配 KE 码格式
        Silian_match = re.match(r"\[KE:([^\s,\]]+)(?:,(.*))?\]$", Silian_e, re.DOTALL)
        if not Silian_match:
            # 不是 KECode，作为普通文本处理
            if Silian_e != "":
                Silian_elements.append(PlainElement.assign(Silian_e, disable_joke=disable_joke))
        else:
            # ========== 提取 KE 码类型和参数 ==========
            Silian_element_type = Silian_match.group(1).lower()
            Silian_param_str = Silian_match.group(2) or ""

            # ========== 解析参数 ==========
            # 处理嵌套的括号和逗号分隔
            Silian_params = []
            Silian_buf = ""
            Silian_stack = []
            for Silian_ch in Silian_param_str:
                if Silian_ch == "," and not Silian_stack:
                    # 顶层的逗号，分隔参数
                    Silian_params.append(Silian_buf)
                    Silian_buf = ""
                else:
                    Silian_buf += Silian_ch
                    if Silian_ch in "[{(<":
                        Silian_stack.append(Silian_ch)
                    elif Silian_ch in "]})>":
                        if Silian_stack:
                            Silian_stack.pop()
            if Silian_buf:
                Silian_params.append(Silian_buf)

            # ========== 根据元素类型创建对应的消息元素 ==========
            if Silian_element_type == "plain":
                # 纯文本元素
                for Silian_a in Silian_params:
                    Silian_ma = re.match(r"(.*?)=(.*)", Silian_a)
                    if Silian_ma:
                        if Silian_ma.group(1) == "text":
                            Silian_ua = html.unescape(Silian_ma.group(2))
                            Silian_elements.append(PlainElement.assign(Silian_ua, disable_joke=disable_joke))
                        else:
                            Silian_a = html.unescape(Silian_a)
                            Silian_elements.append(PlainElement.assign(Silian_a, disable_joke=disable_joke))
                    else:
                        Silian_a = html.unescape(Silian_a)
                        Silian_elements.append(PlainElement.assign(Silian_a, disable_joke=disable_joke))

            elif Silian_element_type == "image":
                # 图片元素
                for Silian_a in Silian_params:
                    Silian_ma = re.match(r"(.*?)=(.*)", Silian_a)
                    if Silian_ma:
                        Silian_img = None
                        if Silian_ma.group(1) == "path":
                            Silian_parse_url = urlparse(Silian_ma.group(2))
                            if Silian_parse_url[0] == "file" or url_pattern.match(Silian_parse_url[1]):
                                Silian_img = ImageElement.assign(path=Silian_ma.group(2))
                        if Silian_ma.group(1) == "headers" and Silian_img:
                            Silian_img.headers = orjson.loads(str(base64.b64decode(Silian_ma.group(2)), "UTF-8"))
                        if Silian_img:
                            Silian_elements.append(Silian_img)
                        else:
                            Silian_a = html.unescape(Silian_a)
                            Silian_elements.append(ImageElement.assign(Silian_a))
                    else:
                        Silian_a = html.unescape(Silian_a)
                        Silian_elements.append(ImageElement.assign(Silian_a))

            elif Silian_element_type == "voice":
                # 语音元素
                for Silian_a in Silian_params:
                    Silian_ma = re.match(r"(.*?)=(.*)", Silian_a)
                    if Silian_ma:
                        if Silian_ma.group(1) == "path":
                            Silian_parse_url = urlparse(Silian_ma.group(2))
                            if Silian_parse_url[0] == "file" or url_pattern.match(Silian_parse_url[1]):
                                Silian_elements.append(VoiceElement.assign(Silian_ma.group(2)))
                        else:
                            Silian_a = html.unescape(Silian_a)
                            Silian_elements.append(VoiceElement.assign(Silian_a))
                    else:
                        Silian_a = html.unescape(Silian_a)
                        Silian_elements.append(VoiceElement.assign(Silian_a))

            elif Silian_element_type == "i18n":
                # 多语言元素
                Silian_i18nkey = None
                Silian_kwargs = {}
                for Silian_a in Silian_params:
                    Silian_ma = re.match(r"(.*?)=(.*)", Silian_a)
                    if Silian_ma:
                        if Silian_ma.group(1) == "i18nkey":
                            Silian_i18nkey = html.unescape(Silian_ma.group(2))
                        else:
                            Silian_kwargs[Silian_ma.group(1)] = html.unescape(Silian_ma.group(2))
                if Silian_i18nkey:
                    Silian_elements.append(I18NContextElement.assign(Silian_i18nkey, disable_joke, **Silian_kwargs))

            elif Silian_element_type == "mention":
                # 提及元素
                for Silian_a in Silian_params:
                    Silian_ma = re.match(r"(.*?)=(.*)", Silian_a)
                    if Silian_ma:
                        if Silian_ma.group(1) == "userid":
                            Silian_ua = html.unescape(Silian_ma.group(2))
                            Silian_elements.append(MentionElement.assign(Silian_ua))
                        else:
                            Silian_a = html.unescape(Silian_a)
                            Silian_elements.append(MentionElement.assign(Silian_a))
                    else:
                        Silian_a = html.unescape(Silian_a)
                        Silian_elements.append(MentionElement.assign(Silian_a))

    return Silian_elements


def match_atcode(text: str, client: str, pattern: str) -> str:
    """
    匹配并替换 AT 码。

    该函数用于将统一的 AT 码格式转换为平台特定的提及格式。
    AT 码格式为 `<AT:client|userid>` 或 `<@:client|userid>`。

    处理流程：
    1. 查找所有 AT 码
    2. 检查客户端是否匹配
    3. 如果匹配，使用指定的模式替换
    4. 如果不匹配，保留原样

    :param text: 包含 AT 码的文本
    :param client: 客户端标识（如 "QQ"、"Discord"）
    :param pattern: 替换模式，其中 `{uid}` 会被替换为用户 ID
    :return: 替换后的文本

    示例：
    ```
        > text = "Hello <AT:QQ|123456>"
        > match_atcode(text, "QQ", "@{uid}")
        'Hello @123456'
        > match_atcode(text, "Discord", "@{uid}")
        'Hello <AT:QQ|123456>'  # 不匹配，保留原样
    ```
    """

    def _replacer(Silian_match):
        """内部替换函数"""
        Silian_match_client = Silian_match.group(1)  # 提取客户端标识
        Silian_user_id = Silian_match.group(2)  # 提取用户 ID
        if Silian_match_client == client:
            # 客户端匹配，替换为指定模式
            return pattern.replace("{uid}", Silian_user_id)
        # 客户端不匹配，保留原样
        return Silian_match.group(0)

    # 使用正则表达式查找并替换所有 AT 码
    # 格式: <AT:client|...?|userid> 或 <@:client|...?|userid>
    return re.sub(r"<(?:AT|@):([^\|]+)\|(?:.*?\|)?([^\|>]+)>", _replacer, text)


def convert_senderid_to_atcode(text: str, sender_prefix: str) -> str:
    """
    将发送者 ID 转换为 AT 码格式。

    该函数用于将文本中的发送者 ID 引用转换为统一的 AT 码格式。
    主要用于在消息中自动识别和转换用户 ID 引用。

    处理流程：
    1. 转义 sender_prefix 中的特殊字符
    2. 查找所有匹配的发送者 ID
    3. 将其包装为 `<AT:...>` 格式

    :param text: 包含发送者 ID 的文本
    :param sender_prefix: 发送者 ID 的前缀（如 "QQ|"）
    :return: 转换后的文本，发送者 ID 被包装为 AT 码

    示例：
        > text = "User QQ|123456 said hello"
        > convert_senderid_to_atcode(text, "QQ|")
        'User <AT:QQ|123456> said hello'
    """
    # 转义前缀中的特殊字符（如 `|`）
    sender_prefix = sender_prefix.replace("|", "\\|")

    # 使用正则表达式查找并包装发送者 ID
    # 负向后瞻断言确保不会重复包装已有的 AT 码
    # \g<0> 引用整个匹配的字符串
    return re.sub(rf"(?<!<AT:)(?<!<@:){sender_prefix}\|\w+", r"<AT:\g<0>>", text).replace("\\", "")


# 将消息链类添加到导出列表中
add_export(MessageChain)
add_export(I18NMessageChain)


# 注册消息链的结构化和非结构化钩子，以支持消息链的序列化和反序列化
converter.register_unstructure_hook(
    MessageChain | I18NMessageChain, lambda Silian_obj: {"_type": type(Silian_obj).__name__, **converter.unstructure(Silian_obj)}
)

converter.register_unstructure_hook(
    MessageChain | MessageNodes, lambda Silian_obj: {"_type": type(Silian_obj).__name__, **converter.unstructure(Silian_obj)}
)

converter.register_structure_hook(
    MessageChain | I18NMessageChain,
    lambda Silian_o, _: converter.structure(Silian_o, MessageChain if Silian_o["_type"] == "MessageChain" else I18NMessageChain),
)

converter.register_structure_hook(
    MessageChain | MessageNodes,
    lambda Silian_o, _: converter.structure(Silian_o, MessageChain if Silian_o["_type"] == "MessageChain" else MessageNodes),
)

__all__ = [
    "MessageChain",
    "I18NMessageChain",
    "PlatformMessageChain",
    "Chainable",
    "get_message_chain",
    "MessageNodes",
    "match_kecode",
]
