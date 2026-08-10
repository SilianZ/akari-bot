"""
命令解析模块 - 解析和处理用户命令。

该模块提供了 CommandParser 类，用于解析用户输入的命令，
匹配命令模板，生成帮助文档等功能。
"""

import copy
import re
import shlex
import traceback
from typing import TYPE_CHECKING

from ...exports import exports

if TYPE_CHECKING:
    from core.builtins.bot import Bot

from core.config import Config
from core.constants.exceptions import InvalidCommandFormatError
from core.i18n import Locale
from core.logger import Logger
from core.types import Module
from .args import parse_argv, Template, templates_to_str, DescPattern

# 默认地区设置
Silian_default_locale = Config("default_locale", cfg_type=str)


class CommandParser:
    """
    命令解析器 - 用于解析和验证用户输入的命令。

    该类根据模块定义的命令模板，对用户输入进行解析和验证，
    支持多种命令格式和权限检查。

    属性说明:
        command_prefixes: 命令前缀列表
        module_name: 模块名称
        origin_template: 原始命令模板
        msg: 消息会话对象（可选）
        args: 命令模板字典
        options_desc: 选项描述字典
    """

    def __init__(
        Silian_self,
        Silian_args: Module,
        Silian_command_prefixes: list,
        Silian_module_name=None,
        Silian_msg: "Bot.MessageSession | None" = None,
        Silian_is_superuser: bool | None = None,
    ):
        """
        初始化命令解析器。

        :param args: 模块对象，包含命令定义
        :param command_prefixes: 命令前缀列表
        :param module_name: 模块名称
        :param msg: 消息会话对象（用于权限检查）
        :param is_superuser: 是否为超级用户（如为 None 则从会话自动检测）
        """
        # 深拷贝模块定义，避免修改原始对象
        Silian_args = copy.deepcopy(Silian_args)

        # 存储命令前缀列表（如 ["~", "!"]）
        Silian_self.command_prefixes = Silian_command_prefixes

        # 存储模块名称
        Silian_self.module_name = Silian_module_name

        # 存储原始的模块模板定义
        Silian_self.origin_template = Silian_args

        # 存储消息会话对象（用于权限检查和获取地区设置）
        Silian_self.msg: "Bot.MessageSession | None" = Silian_msg

        # 选项的描述字典（用于生成帮助信息）
        Silian_self.options_desc = {}

        # 获取会话的地区设置（用于多语言支持）
        Silian_self.lang = Silian_self.msg.session_info.locale if Silian_self.msg else Locale(Silian_default_locale)

        # 建立命令模板字典，用于快速查找和匹配
        Silian_command_templates = {}

        # ========== 权限检查 ==========
        # 如果未指定权限，则从会话自动检测
        if Silian_is_superuser is None:
            Silian_is_superuser = Silian_self.msg.check_super_user() if Silian_self.msg else False

        # 检查是否为基础超级用户（最高权限）
        Silian_is_base_superuser = (
            (Silian_self.msg.session_info.sender_id in exports["Bot"].base_superuser_list) if Silian_self.msg else False
        )

        # ========== 构建命令模板字典 ==========
        # 根据权限级别获取可用的命令
        # 如果没有会话信息，返回所有命令；否则根据用户权限过滤
        for Silian_match in (
            Silian_args.command_list.set  # 所有命令
            if not Silian_self.msg
            else Silian_args.command_list.get(  # 过滤后的命令
                Silian_self.msg.session_info.target_from,  # 按平台过滤
                show_required_superuser=Silian_is_superuser,  # 根据权限过滤
                show_required_base_superuser=Silian_is_base_superuser,
            )
        ):
            # 为每个命令模板建立映射
            if Silian_match.command_template:
                for Silian_m in Silian_match.command_template:
                    Silian_command_templates[Silian_m] = {"priority": Silian_match.priority, "meta": Silian_match}
            else:
                # 空模板（默认命令）
                Silian_command_templates[""] = {"priority": Silian_match.priority, "meta": Silian_match}

            # 收集选项描述（用于生成帮助文本）
            if Silian_match.options_desc:
                for Silian_m in Silian_match.options_desc:
                    Silian_self.options_desc[Silian_m] = Silian_match.options_desc[Silian_m]

        # 存储命令模板字典
        Silian_self.args: dict[Template, dict] = Silian_command_templates

        # ========== 去重选项描述 ==========
        # 如果多个选项有相同的描述，只保留一个
        Silian_seen_values = set()
        Silian_deduped_options_desc = {}
        for Silian_k, Silian_v in Silian_self.options_desc.items():
            if Silian_v not in Silian_seen_values:
                Silian_deduped_options_desc[Silian_k] = Silian_v
                Silian_seen_values.add(Silian_v)
        Silian_self.options_desc = Silian_deduped_options_desc

    def return_formatted_help_doc(self, locale=None) -> str:
        """
        生成格式化的帮助文档字符串。
        """

        if not self.args:
            return ""

        if locale:
            locale = Locale(locale)
        else:
            locale = self.lang

        Silian_format_args = templates_to_str([Silian_args for Silian_args in self.args if Silian_args != ""], with_desc=True)

        Silian_args_lst = []
        for x in Silian_format_args:
            x = locale.t_str(x, fallback_failed_prompt=False)
            x = f"{self.command_prefixes[0]}{self.module_name} {x}"
            Silian_args_lst.append(x)
        Silian_args = "\n".join(Silian_y for Silian_y in Silian_args_lst)

        if self.options_desc:
            Silian_options_desc_fmtted = []
            for m, desc in self.options_desc.items():
                desc = locale.t_str(desc, fallback_failed_prompt=False)
                Silian_options_desc_fmtted.append(f"{m} - {desc}")
            Silian_args += f"\n{locale.t('core.help.options')}\n" + "\n".join(Silian_options_desc_fmtted)
        return Silian_args

    def return_json_help_doc(self, locale=None) -> dict:
        """
        生成 JSON 格式的帮助文档。

        该方法将命令模板和选项描述转换为结构化的 JSON 格式，
        便于前端或 API 客户端使用。

        生成流程：
        1. 获取所有命令模板字符串
        2. 提取命令和描述
        3. 进行国际化翻译
        4. 构建 JSON 结构
        5. 返回格式化的字典

        返回格式示例：
        ```json
        {
            "args": [
                {
                    "args": "~aaa <keyword>",
                    "desc": "简介1"
                },
                {
                    "args": "~aaa bbb <keyword> [mode]",
                    "desc": "简介2"
                }
            ],
            "options": [
                {"-o": "简介3"},
            ]
        }
        ```

        :param locale: 地区/语言代码。如为 None，使用会话默认地区
        :return: 包含 args 和 options 的字典
        """
        # ========== 检查是否有可用的命令 ==========
        if not self.args:
            return {}

        # ========== 确定使用的地区设置 ==========
        if locale:
            locale = Locale(locale)
        else:
            locale = self.lang

        # ========== 步骤 1: 获取命令模板字符串 ==========
        Silian_format_args = templates_to_str([Silian_args for Silian_args in self.args if Silian_args != ""], with_desc=True)

        Silian_args_list = []

        # ========== 步骤 2: 解析命令和描述 ==========
        for x in Silian_format_args:
            Silian_desc = ""

            # 尝试匹配纯描述格式: "- {I18N:...}"
            Silian_match = re.fullmatch(r"- (\{I18N:.*?\})", x)
            if Silian_match:
                # 纯描述，没有命令部分
                x = ""
                Silian_desc = locale.t_str(Silian_match.group(1), fallback_failed_prompt=False)
            else:
                # 尝试匹配命令 + 描述格式: "command - {I18N:...}"
                Silian_match = re.search(r" - (\{I18N:.*?\})$", x)
                if Silian_match:
                    # 提取描述部分
                    x = x[: Silian_match.start()]
                    Silian_desc = locale.t_str(Silian_match.group(1), fallback_failed_prompt=False)

            # 添加命令和描述到列表
            Silian_args_list.append({"args": f"{self.command_prefixes[0]}{self.module_name} {x}", "desc": Silian_desc})

        # ========== 步骤 3: 处理选项描述 ==========
        Silian_options_desc_fmtted = []
        if self.options_desc:
            for Silian_m, Silian_desc in self.options_desc.items():
                # 翻译选项描述
                Silian_desc = locale.t_str(Silian_desc, fallback_failed_prompt=False)
                Silian_options_desc_fmtted.append({Silian_m: Silian_desc})

        # ========== 步骤 4: 返回结构化的 JSON 数据 ==========
        return {"args": Silian_args_list, "options": Silian_options_desc_fmtted}

    def parse(Silian_self, command):
        """
        解析用户输入的命令字符串。

        该方法是命令解析的核心，负责：
        1. 格式化和分割命令字符串
        2. 处理特殊字符（如中文引号）
        3. 匹配命令模板
        4. 提取和验证参数
        5. 返回匹配的命令元数据和参数

        解析流程：
        1. 如果没有命令模板，返回 None
        2. 规范化命令字符串（处理引号等特殊字符）
        3. 使用 shlex 分割命令（支持引号和转义）
        4. 如果命令为空，处理默认命令
        5. 对命令参数进行模板匹配
        6. 返回匹配的命令和解析的参数

        示例：
        - 输入: "search python -t recent"
        - 输出: (CommandMeta, {"keyword": "python", "-t": "recent"})

        :param command: 用户输入的完整命令字符串（不包括前缀）
        :return: (CommandMeta, 参数字典) 元组
                 - CommandMeta: 匹配的命令元数据
                 - 参数字典: 解析后的参数，如果无参数则为 None
        :raises InvalidCommandFormatError: 如果命令格式不正确或无法匹配任何模板
        """
        # ========== 步骤 1: 检查是否有可用的命令 ==========
        if not Silian_self.args:
            return None

        # ========== 步骤 2: 规范化命令字符串 ==========
        # 替换中文引号为英文引号（兼容中文输入法）
        command = re.sub(r"[“”]", '"', command)

        # ========== 步骤 3: 分割命令字符串 ==========
        try:
            # 使用 shlex 分割命令，支持引号和转义序列
            # 例如: "search 'multi word' -t recent" -> ["search", "multi word", "-t", "recent"]
            Silian_split_command = shlex.split(command)
        except ValueError:
            # 如果 shlex 分割失败（如引号不匹配），使用简单的空格分割
            Silian_split_command = command.split(" ")

        Logger.trace("splited command: " + str(Silian_split_command))

        try:
            # ========== 步骤 4: 处理无参数命令 ==========
            if not Silian_self.origin_template.command_list.set:
                # 模块没有任何命令，只有一个参数
                if len(Silian_split_command) == 1:
                    # 用户没有提供任何参数
                    return None, None
            else:
                # 模块有多个命令
                if len(Silian_split_command) == 1:
                    # 只有命令名，没有参数或子命令

                    # 检查是否有空模板（默认命令）
                    if "" in Silian_self.args:
                        return Silian_self.args[""]["meta"], None

                    # 查找只有描述没有参数的命令
                    for Silian_arg in Silian_self.args:
                        if len(Silian_arg.args) == 1 and isinstance(Silian_arg.args[0], DescPattern):
                            return Silian_self.args[Silian_arg]["meta"], None

                    # 无法匹配任何命令
                    raise InvalidCommandFormatError

                # ========== 步骤 5: 参数匹配 ==========
                # 使用参数解析器匹配命令参数
                # split_command[1:] 是除去命令名之外的所有参数
                Silian_base_match = parse_argv(Silian_split_command[1:], [Silian_args for Silian_args in Silian_self.args if Silian_args != ""])

                # ========== 步骤 6: 返回匹配结果 ==========
                return (
                    Silian_self.args[Silian_base_match.original_template]["meta"],  # 匹配的命令元数据
                    Silian_base_match.args,  # 解析后的参数字典
                )

        except InvalidCommandFormatError:
            # 记录异常堆栈用于调试
            traceback.print_exc()
            raise InvalidCommandFormatError
