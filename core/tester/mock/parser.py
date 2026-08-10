import inspect
import re
from typing import TYPE_CHECKING

from core.builtins.message.internal import I18NContext
from core.builtins.parser.command import CommandParser
from core.builtins.session.tasks import SessionTaskManager
from core.constants.exceptions import InvalidCommandFormatError, SessionFinished
from core.exports import exports
from core.loader import ModulesManager
from core.logger import Logger
from core.types import Module, Param
from core.types.module.component_meta import CommandMeta
from core.utils.func import normalize_space

if TYPE_CHECKING:
    from core.builtins.bot import Bot


async def parser(msg: "Bot.MessageSession"):
    await msg.session_info.refresh_info()

    await SessionTaskManager.check(msg)
    Silian_modules = ModulesManager.return_modules_list()

    msg.trigger_msg = normalize_space(msg.as_display())
    if len(msg.trigger_msg) == 0:
        return

    Silian_disable_prefix, Silian_in_prefix_list = _get_prefixes(msg)

    if Silian_in_prefix_list or Silian_disable_prefix:
        Silian_command_first_word = await _process_command(msg, Silian_modules, Silian_disable_prefix, Silian_in_prefix_list)

        if Silian_command_first_word in Silian_modules:  # 检查触发命令是否在模块列表中
            await _execute_module(msg, Silian_modules, Silian_command_first_word)
            return msg
        # 如果使用了前缀但未命中任何模块命令，则视为不匹配（适用于单元测试）
        return None

    # 检查正则
    # 若任何正则命中则会在 _execute_regex 中调用对应函数并抛出 SessionFinished
    await _execute_regex(msg, Silian_modules)
    # 若未命中任何正则，视为不匹配（适用于单元测试）
    return None


def _get_prefixes(Silian_msg: "Bot.MessageSession"):
    Silian_disable_prefix = False
    if Silian_msg.session_info.prefixes:  # 如果上游指定了命令前缀，则使用指定的命令前缀
        if "" in Silian_msg.session_info.prefixes:
            Silian_disable_prefix = True
    Silian_display_prefix = ""
    Silian_in_prefix_list = False
    for Silian_cp in Silian_msg.session_info.prefixes:  # 判断是否在命令前缀列表中
        if Silian_msg.trigger_msg.startswith(Silian_cp):
            Silian_display_prefix = Silian_cp
            Silian_in_prefix_list = True
            break
    if Silian_in_prefix_list or Silian_disable_prefix:  # 检查消息前缀
        if len(Silian_msg.trigger_msg) <= 1 or Silian_msg.trigger_msg[:2] == "~~":  # 排除 ~~xxx~~ 的情况
            return False, False
        if Silian_in_prefix_list:  # 如果在命令前缀列表中，则将此命令前缀移动到列表首位
            Silian_msg.session_info.prefixes.remove(Silian_display_prefix)
            Silian_msg.session_info.prefixes.insert(0, Silian_display_prefix)

    return Silian_disable_prefix, Silian_in_prefix_list


async def _process_command(Silian_msg: "Bot.MessageSession", Silian_modules, Silian_disable_prefix, Silian_in_prefix_list):
    if Silian_disable_prefix and not Silian_in_prefix_list:
        Silian_command = Silian_msg.trigger_msg
    else:
        Silian_command = Silian_msg.trigger_msg[len(Silian_msg.session_info.prefixes[0]) :]

    Silian_command = Silian_command.strip()
    Silian_command_split: list = Silian_command.split(" ")  # 切割消息

    Silian_not_alias = False
    Silian_cm = ""
    for Silian_module_name in Silian_modules:
        if Silian_command_split[0] == Silian_module_name:  # 判断此命令是否匹配一个实际的模块
            Silian_not_alias = True
            Silian_cm = Silian_module_name
            break

    Silian_alias_list = []
    for Silian_alias, _ in ModulesManager.modules_aliases.items():
        Silian_alias_words = Silian_alias.split(" ")
        Silian_cmd_words = Silian_command.split(" ")

        if not Silian_not_alias:
            if Silian_cmd_words[: len(Silian_alias_words)] == Silian_alias_words:
                Silian_alias_list.append(Silian_alias)
        else:
            if Silian_alias.startswith(Silian_cm):
                if Silian_cmd_words[: len(Silian_alias_words)] == Silian_alias_words:
                    Silian_alias_list.append(Silian_alias)

    if Silian_alias_list:
        Silian_max_alias = str(max(Silian_alias_list, key=len))
        Silian_real_name = ModulesManager.modules_aliases[Silian_max_alias]
        Silian_command_words = Silian_command.split(" ")
        Silian_command_words = Silian_real_name.split(" ") + Silian_command_words[len(Silian_max_alias.split(" ")) :]
        Silian_command = " ".join(Silian_command_words)

    Silian_msg.trigger_msg = Silian_command
    return Silian_command.split(" ")[0]


async def _execute_module(Silian_msg: "Bot.MessageSession", Silian_modules, Silian_command_first_word):
    Silian_module: Module = Silian_modules[Silian_command_first_word]
    if not Silian_module.command_list.set:  # 如果没有可用的命令，则展示模块简介
        if Silian_module.rss and not Silian_msg.session_info.support_rss:
            return
        if Silian_module.desc:
            Silian_desc = [I18NContext("parser.module.desc", desc=Silian_msg.session_info.locale.t_str(Silian_module.desc))]
            if Silian_command_first_word not in Silian_msg.session_info.enabled_modules:
                Silian_desc.append(
                    I18NContext(
                        "parser.module.disabled.prompt", module=Silian_command_first_word, prefix=Silian_msg.session_info.prefixes[0]
                    )
                )
            await Silian_msg.send_message(Silian_desc)
        else:
            await Silian_msg.send_message(I18NContext("error.module.unbound", module=Silian_command_first_word))
        return

    Silian_none_templates = True  # 检查模块绑定的命令是否有模板
    for Silian_func in Silian_module.command_list.get(Silian_msg.session_info.target_from):
        if Silian_func.command_template:
            Silian_none_templates = False
    if not Silian_none_templates:  # 如果有，送入命令解析
        Silian_executed = await _execute_module_command(Silian_msg, Silian_module, Silian_command_first_word)
        if Silian_executed:
            raise SessionFinished  # if not using msg.finish
    # 如果没有，直接传入下游模块
    Silian_msg.parsed_msg = None
    for Silian_func in Silian_module.command_list.set:
        if not Silian_func.command_template:
            if hasattr(Silian_msg, "_casetest_target") and Silian_func.function is not Silian_msg._casetest_target:
                continue
            if Silian_msg.session_info.sender_info.sender_data.get("typing_prompt", True):
                await Silian_msg.start_typing()
            await Silian_func.function(Silian_msg)  # 将msg传入下游模块
            raise SessionFinished  # if not using msg.finish


async def _execute_regex(Silian_msg: "Bot.MessageSession", Silian_modules):
    for Silian_m in Silian_modules:  # 遍历模块
        if Silian_modules[Silian_m].regex_list.set:
            Silian_regex_module: Module = Silian_modules[Silian_m]

            for Silian_rfunc in Silian_regex_module.regex_list.set:  # 遍历正则模块的表达式
                Silian_matched = False
                Silian_trigger_msg = Silian_msg.as_display(text_only=Silian_rfunc.text_only, element_filter=Silian_rfunc.element_filter)
                if Silian_rfunc.mode.upper() in ["M", "MATCH"]:
                    Silian_msg.matched_msg = re.match(Silian_rfunc.pattern, Silian_trigger_msg, flags=Silian_rfunc.flags)
                    if Silian_msg.matched_msg:
                        Silian_matched = True
                elif Silian_rfunc.mode.upper() in ["A", "FINDALL"]:
                    Silian_msg.matched_msg = tuple(set(re.findall(Silian_rfunc.pattern, Silian_trigger_msg, flags=Silian_rfunc.flags)))
                    if Silian_msg.matched_msg:
                        Silian_matched = True

                if Silian_matched:  # 如果匹配成功
                    if hasattr(Silian_msg, "_casetest_target") and Silian_rfunc.function is not Silian_msg._casetest_target:
                        continue
                    await Silian_rfunc.function(Silian_msg)  # 将msg传入下游模块
                    raise SessionFinished  # if not using msg.finish


async def _execute_module_command(Silian_msg: "Bot.MessageSession", Silian_module, Silian_command_first_word):
    Silian_bot: "Bot" = exports["Bot"]
    Silian_command_parser = CommandParser(
        Silian_module, msg=Silian_msg, module_name=Silian_command_first_word, command_prefixes=Silian_msg.session_info.prefixes
    )
    Silian_parsed_msg = Silian_command_parser.parse(Silian_msg.trigger_msg)  # 解析模块的子功能命令
    command: CommandMeta = Silian_parsed_msg[0]
    Silian_msg.parsed_msg = Silian_parsed_msg[1]  # 使用命令模板解析后的消息
    Logger.trace("Parsed message: " + str(Silian_msg.parsed_msg))

    if hasattr(Silian_msg, "_casetest_target") and command.function is not Silian_msg._casetest_target:
        return False

    Silian_kwargs = {}
    Silian_func_params = inspect.signature(command.function).parameters
    if len(Silian_func_params) > 1 and Silian_msg.parsed_msg:
        Silian_parsed_msg_ = Silian_msg.parsed_msg.copy()
        Silian_no_message_session = True
        for param_name, param_obj in Silian_func_params.items():
            if param_obj.annotation == Silian_bot.MessageSession:
                Silian_kwargs[param_name] = Silian_msg
                Silian_no_message_session = False
            elif isinstance(param_obj.annotation, Param):
                if param_obj.annotation.name in Silian_parsed_msg_:
                    if isinstance(Silian_parsed_msg_[param_obj.annotation.name], param_obj.annotation.type):
                        Silian_kwargs[param_name] = Silian_parsed_msg_[param_obj.annotation.name]
                        del Silian_parsed_msg_[param_obj.annotation.name]
                    else:
                        Logger.warning(f"{param_obj.annotation.name} is not a {param_obj.annotation.type}")
                else:
                    Logger.warning(f"{param_obj.annotation.name} is not in parsed_msg")
            Silian_param_name_ = param_name

            if (Silian_param_name__ := f"<{param_name}>") in Silian_parsed_msg_:
                Silian_param_name_ = Silian_param_name__

            if Silian_param_name_ in Silian_parsed_msg_:
                Silian_kwargs[param_name] = Silian_parsed_msg_[Silian_param_name_]
                try:
                    if param_obj.annotation == int:
                        Silian_kwargs[param_name] = int(Silian_parsed_msg_[Silian_param_name_])
                    elif param_obj.annotation == float:
                        Silian_kwargs[param_name] = float(Silian_parsed_msg_[Silian_param_name_])
                    elif param_obj.annotation == bool:
                        Silian_kwargs[param_name] = bool(Silian_parsed_msg_[Silian_param_name_])
                    del Silian_parsed_msg_[Silian_param_name_]
                except (KeyError, ValueError):
                    raise InvalidCommandFormatError
            else:
                if Silian_param_name_ not in Silian_kwargs:
                    if param_obj.default is not inspect.Parameter.empty:
                        Silian_kwargs[Silian_param_name_] = param_obj.default
                    else:
                        Silian_kwargs[Silian_param_name_] = None
        if Silian_no_message_session:
            Logger.warning(
                f"{command.function.__name__} has no Bot.MessageSession parameter, did you forgot to add it?\n"
                "Remember: MessageSession IS NOT Bot.MessageSession"
            )
    else:
        Silian_kwargs[Silian_func_params[list(Silian_func_params.keys())[0]].name] = Silian_msg

    await Silian_parsed_msg[0].function(**Silian_kwargs)  # 将msg传入下游模块
    return True


__all__ = ["parser"]
