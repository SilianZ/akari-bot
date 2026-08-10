"""
服务器队列处理模块。

该模块定义了服务器侧的队列操作接口，以及服务器侧的任务处理器。
服务器通过这个模块向客户端发送各类操作请求，并处理来自客户端的消息和信息。

主要功能：
- 向客户端发送消息、删除消息
- 成员管理操作（限制、踢出、封禁等）
- 消息反应操作（添加/移除emoji反应）
- 上下文管理（保持/释放会话)
- 接收客户端的消息并进行处理
- 获取和管理模块信息
- 调用OneBot标准API
"""

import re
from typing import TYPE_CHECKING

from core.builtins.parser.command import CommandParser
from core.builtins.parser.message import parser
from core.builtins.utils import command_prefix
from core.constants.path import PrivateAssets
from core.utils.bash import run_sys_command
from core.web_render import web_render
from ..alive import Alive
from .base import JobQueueBase
from ..builtins.converter import converter
from ..builtins.message.chain import MessageChain, MessageNodes
from ..builtins.session.info import SessionInfo
from ..database.models import JobQueuesTable
from ..exports import exports, add_export
from ..i18n import Locale
from ..loader import ModulesManager
from ..logger import Logger

if TYPE_CHECKING:
    from core.builtins.bot import Bot


class JobQueueServer(JobQueueBase):
    """服务器队列处理类。

    提供服务器向客户端发送各类操作请求的接口方法。这些方法将任务添加到队列，
    由客户端处理后将结果返回给服务器。
    """

    @classmethod
    async def client_send_message(
        Silian_cls,
        session_info: SessionInfo,
        message: MessageChain | MessageNodes,
        quote: bool = True,
        wait=True,
        enable_parse_message: bool = True,
        enable_split_image: bool = True,
    ):
        """向客户端发送消息。

        通过队列系统向指定的客户端发送消息。支持引用、消息解析和图片分割等功能。

        :param session_info: 目标会话信息，指定消息发送到哪个频道/用户
        :param message: 要发送的消息链对象
        :param quote: 是否引用原消息（默认 True）
        :param wait: 是否等待消息发送完成（默认 True）
        :param enable_parse_message: 是否解析消息中的特殊标记（默认 True）
        :param enable_split_image: 是否将大图片拆分成多条消息发送（默认 True）

        :return wait=True: 返回发送结果字典（包含 message_id 等）
        :return wait=False: 返回任务 ID
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "send_message",
            {
                "session_info": converter.unstructure(session_info),
                "message": converter.unstructure(message, MessageChain | MessageNodes),
                "quote": quote,
                "enable_parse_message": enable_parse_message,
                "enable_split_image": enable_split_image,
            },
            wait=wait,
        )
        return Silian_value

    @classmethod
    async def client_delete_message(
        Silian_cls, session_info: SessionInfo, message_id: str | list[str], reason: str | None = None
    ):
        """删除客户端的消息。

        通过队列系统删除指定的消息。这是一个非阻塞操作。

        :param session_info: 消息所在的会话信息
        :param message_id: 要删除的消息ID或ID列表
        :param reason: 删除原因（可选）

        :return: 任务 ID 或返回值（通常不会被等待）
        """
        if isinstance(message_id, str):
            message_id = [message_id]
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "delete_message",
            {"session_info": converter.unstructure(session_info), "message_id": message_id, "reason": reason},
            wait=False,
        )
        return Silian_value

    @classmethod
    async def client_restrict_member(
        Silian_cls, session_info: SessionInfo, user_id: str | list[str], duration: int | None = None, reason: str | None = None
    ):
        """限制群组成员（禁言）。

        通过队列系统对指定的成员进行禁言处理。这是一个非阻塞操作。

        :param session_info: 目标群组 / 频道的会话信息
        :param user_id: 要限制的成员 ID 或 ID 列表
        :param duration: 限制时长（秒），None 表示永久
        :param reason: 限制原因（可选）

        :return: 任务 ID 或返回值
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "restrict_member",
            {
                "session_info": converter.unstructure(session_info),
                "user_id": user_id,
                "duration": duration,
                "reason": reason,
            },
            wait=False,
        )
        return Silian_value

    @classmethod
    async def client_unrestrict_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str]):
        """解除成员限制（解除禁言）。

        通过队列系统取消之前对成员的限制。这是一个非阻塞操作。

        :param session_info: 目标群组 / 频道的会话信息
        :param user_id: 要解除限制的成员 ID 或 ID 列表

        :return: 任务ID或返回值
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "unrestrict_member",
            {"session_info": converter.unstructure(session_info), "user_id": user_id},
            wait=False,
        )
        return Silian_value

    @classmethod
    async def client_kick_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str], reason: str | None = None):
        """踢出群组成员。

        通过队列系统将指定的成员从群组 / 频道中踢出。这是一个非阻塞操作。

        :param session_info: 目标群组 / 频道的会话信息
        :param user_id: 要踢出的成员 ID 或 ID 列表
        :param reason: 踢出原因（可选）

        :return: 任务 ID 或返回值
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "kick_member",
            {"session_info": converter.unstructure(session_info), "user_id": user_id, "reason": reason},
            wait=False,
        )
        return Silian_value

    @classmethod
    async def client_ban_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str], reason: str | None = None):
        """永久封禁群组成员。

        通过队列系统永久封禁指定的成员。这是一个非阻塞操作。

        :param session_info: 目标群组 / 频道的会话信息
        :param user_id: 要封禁的成员 ID 或 ID 列表
        :param reason: 封禁原因（可选）

        :return: 任务 ID 或返回值
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "ban_member",
            {"session_info": converter.unstructure(session_info), "user_id": user_id, "reason": reason},
            wait=False,
        )
        return Silian_value

    @classmethod
    async def client_unban_member(Silian_cls, session_info: SessionInfo, user_id: str | list[str]):
        """解除成员封禁。

        通过队列系统取消之前对成员的永久封禁。这是一个非阻塞操作。

        :param session_info: 目标群组 / 频道的会话信息
        :param user_id: 要解除封禁的成员 ID 或 ID 列表

        :return: 任务 ID 或返回值
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "unban_member",
            {"session_info": converter.unstructure(session_info), "user_id": user_id},
            wait=False,
        )
        return Silian_value

    @classmethod
    async def client_add_reaction(Silian_cls, session_info: SessionInfo, message_id: str | list[str], emoji: str):
        """向消息添加反应。

        通过队列系统在指定的消息上添加表情反应。

        :param session_info: 消息所在的会话信息
        :param message_id: 目标消息 ID 或 ID 列表
        :param emoji: 要添加的表情代码

        :return: 任务结果字典
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "add_reaction",
            {"session_info": converter.unstructure(session_info), "message_id": message_id, "emoji": emoji},
        )
        return Silian_value

    @classmethod
    async def client_remove_reaction(Silian_cls, session_info: SessionInfo, message_id: str | list[str], emoji: str):
        """从消息移除反应。

        通过队列系统移除指定消息上的表情反应。

        :param session_info: 消息所在的会话信息
        :param message_id: 目标消息 ID 或 ID 列表
        :param emoji: 要添加的表情代码

        :return: 任务结果字典
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "remove_reaction",
            {"session_info": converter.unstructure(session_info), "message_id": message_id, "emoji": emoji},
        )
        return Silian_value

    @classmethod
    async def client_start_typing_signal(Silian_cls, session_info: SessionInfo):
        """发送“正在输入……”信号。

        通过队列系统向指定会话发送“正在输入……”的状态指示。

        :param session_info: 目标会话信息
        :return: 任务结果字典
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name, "start_typing", {"session_info": converter.unstructure(session_info)}
        )
        return Silian_value

    @classmethod
    async def client_end_typing_signal(Silian_cls, session_info: SessionInfo):
        """隐藏“正在输入……”信号。

        通过队列系统隐藏指定会话的“正在输入……”状态指示。

        :param session_info: 目标会话信息
        :return: 任务结果字典
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name, "end_typing", {"session_info": converter.unstructure(session_info)}
        )
        return Silian_value

    @classmethod
    async def client_error_signal(Silian_cls, session_info: SessionInfo):
        """发送错误信号。

        通过队列系统向指定会话发送错误通知。这是一个非阻塞操作。

        :param session_info: 目标会话信息
        :return: 任务ID或返回值
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name, "error_signal", {"session_info": converter.unstructure(session_info)}, wait=False
        )
        return Silian_value

    @classmethod
    async def client_check_native_permission(Silian_cls, session_info: SessionInfo):
        """检查客户端会话的原生权限。

        通过队列系统检查指定会话是否拥有原生权限（如管理员权限等）。

        :param session_info: 目标会话信息
        :return: 布尔值，表示是否拥有权限
        """
        Silian_v = await Silian_cls.add_job(
            session_info.client_name,
            "check_session_native_permission",
            {"session_info": converter.unstructure(session_info)},
        )
        return Silian_v["value"]

    @classmethod
    async def client_hold_context(Silian_cls, session_info: SessionInfo):
        """保持会话上下文。

        通过队列系统保持指定会话的上下文，防止其被自动清理。

        :param session_info: 目标会话信息
        :return: 任务结果字典
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name, "hold_context", {"session_info": converter.unstructure(session_info)}
        )
        return Silian_value

    @classmethod
    async def client_release_context(Silian_cls, session_info: SessionInfo):
        """释放会话上下文。

        通过队列系统释放之前保持的会话上下文，允许其被自动清理。

        :param session_info: 目标会话信息
        :return: 任务结果字典
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name, "release_context", {"session_info": converter.unstructure(session_info)}
        )
        return Silian_value

    @classmethod
    async def call_onebot_api(Silian_cls, session_info: SessionInfo, api_name: str, **kwargs: dict):
        """调用 OneBot 标准 API。

        通过队列系统在客户端调用 OneBot 标准 API（如获取群信息、获取群成员列表等）。

        :param session_info: 目标会话信息
        :param api_name: OneBot API 名称
        :param **kwargs: 传递给 API 的参数

        :return: API 调用的结果字典
        """
        Silian_value = await Silian_cls.add_job(
            session_info.client_name,
            "call_onebot_api",
            {"session_info": converter.unstructure(session_info), "api_name": api_name, "args": kwargs},
        )
        return Silian_value


@JobQueueServer.action("receive_message_from_client")
async def receive_message_from_client(tsk: JobQueuesTable, args: dict):
    """接收来自客户端的消息并进行处理。

    这是服务器端的主要消息入口。当客户端接收到用户消息时，会通过队列
    系统将消息转发到服务器，由该处理器进行解析和分发处理。

    :param tsk: 任务对象（未使用）
    :param args: 操作参数，包含 session_info

    :return: 包含 success 标志的字典
    """
    await parser(
        await exports["Bot"].MessageSession.from_session_info(converter.structure(args["session_info"], SessionInfo))
    )
    return {"success": True}


@JobQueueServer.action("client_keepalive")
async def client_keepalive(tsk: JobQueuesTable, args: dict):
    """处理客户端的保活信号。

    刷新客户端的存活状态，确保其被认为在线。同时更新可接收消息的前缀列表。

    :param tsk: 任务对象
    :param args: 操作参数（未使用，使用tsk.args代替）

    :return: 包含 success 标志的字典
    """
    Alive.refresh_alive(
        tsk.args["client_name"],
        target_prefix_list=tsk.args.get("target_prefix_list"),
        sender_prefix_list=tsk.args.get("sender_prefix_list"),
    )
    return {"success": True}


@JobQueueServer.action("trigger_hook")
async def _(Silian_tsk: JobQueuesTable, args: dict):
    """触发钩子函数处理器。

    在服务器上执行指定的钩子函数，并返回其执行结果。这允许客户端远程触发服务器上的事件和逻辑。

    :param tsk: 任务对象
    :param args: 操作参数，包含 module_or_hook_name、session_info 和 args

    :return: 包含 result 的字典，其中 result 是钩子函数的返回值
    """
    Silian_bot: "Bot" = exports["Bot"]
    Silian_session_info: SessionInfo | None = None
    if args["session_info"]:
        Silian_session_info = converter.structure(args["session_info"], SessionInfo)
        await Silian_session_info.refresh_info()
    _val = await Silian_bot.Hook.trigger(args["module_or_hook_name"], session_info=Silian_session_info, args=args["args"])
    Logger.trace(
        f"Trigger hook {args['module_or_hook_name']} with args {args['args']}, result: {_val}, type: {type(_val)}"
    )
    await JobQueueServer.return_val(Silian_tsk, {"result": _val})


@JobQueueServer.action("client_direct_message")
async def client_direct_message(tsk: JobQueuesTable, args: dict):
    """发送直接消息处理器。

    服务器通过客户端向用户直接发送消息（不通过消息队列）。

    :param tsk: 任务对象（未使用）
    :param args: 操作参数，包含 session_info、message 等

    :return: 包含 success 标志的字典
    """
    Silian_bot: "Bot" = exports["Bot"]
    Silian_session_info = converter.structure(args["session_info"], SessionInfo)
    await Silian_session_info.refresh_info()
    Silian_message = converter.structure(args["message"], MessageChain | MessageNodes)
    await Silian_bot.send_direct_message(
        Silian_session_info,
        Silian_message,
        disable_secret_check=args["disable_secret_check"],
        enable_parse_message=args["enable_parse_message"],
    )
    return {"success": True}


@JobQueueServer.action("get_bot_version")
async def get_bot_version(tsk: JobQueuesTable, args: dict):
    """获取机器人版本信息处理器。

    返回机器人的版本号。如果本地有版本文件则读取，否则尝试从git获取提交哈希。

    :param tsk: 任务对象（未使用）
    :param args: 操作参数操作参数（未使用）

    :return: 包含 version 的字典，version 为版本字符串
    """
    Silian_version = None
    Silian_version_path = PrivateAssets.path / ".version"
    if Silian_version_path.exists():
        with open(Silian_version_path, "r") as Silian_f:
            Silian_version = Silian_f.read()
    else:
        Silian_returncode, commit_hash, _ = await run_sys_command(["git", "rev-parse", "HEAD"])
        if Silian_returncode == 0:
            Silian_version = f"git:{commit_hash}"

    return {"version": Silian_version}


@JobQueueServer.action("get_web_render_status")
async def get_web_render_status(tsk: JobQueuesTable, args: dict):
    """获取 WebRender 服务状态处理器。

    检查 WebRender 服务是否正常运行。

    :param tsk: 任务对象（未使用）
    :param args: 操作参数（未使用）

    :return: 包含 web_render_status 的字典
    """
    return {"web_render_status": await web_render.browser.check_status()}


@JobQueueServer.action("get_modules_list")
async def get_module_list(tsk: JobQueuesTable, args: dict):
    """获取模块列表处理器。

    获取所有已加载且启用的模块名称列表（不包括基础模块）。

    :param tsk: 任务对象（未使用）
    :param args: 操作参数（未使用）

    :return: 包含 modules_list 的字典
    """
    Silian_modules = {Silian_k: Silian_v.to_dict() for Silian_k, Silian_v in ModulesManager.return_modules_list(use_cache=False).items()}
    Silian_modules = {Silian_k: Silian_v for Silian_k, Silian_v in Silian_modules.items() if Silian_v.get("load", True) and not Silian_v.get("base", False)}
    Silian_module_list = []
    for Silian_module in Silian_modules.values():
        Silian_module_list.append(Silian_module["module_name"])
    return {"modules_list": Silian_module_list}


@JobQueueServer.action("get_modules_info")
async def get_modules_info(tsk: JobQueuesTable, args: dict):
    """获取所有模块的详细信息处理器。

    获取所有模块的信息并按指定语言进行本地化处理。

    :param tsk: 任务对象（未使用）
    :param args: 操作参数，包含 locale（本地化语言）

    :return: 包含 modules 的字典，modules 为模块信息字典
    """
    Silian_modules = {Silian_k: Silian_v.to_dict() for Silian_k, Silian_v in ModulesManager.return_modules_list(use_cache=False).items()}
    Silian_modules = {Silian_k: Silian_v for Silian_k, Silian_v in Silian_modules.items() if Silian_v.get("load", True)}

    for Silian_module in Silian_modules.values():
        if "desc" in Silian_module and Silian_module.get("desc"):
            Silian_module["desc"] = Locale(args["locale"]).t_str(Silian_module["desc"])

    return {"modules": Silian_modules}


@JobQueueServer.action("get_module_helpdoc")
async def get_module_helpdoc(tsk: JobQueuesTable, args: dict):
    """获取模块帮助文档处理器。

    获取指定模块的详细帮助文档，包括所有命令和正则表达式规则，
    并按指定语言进行本地化。

    :param tsk: 任务对象（未使用）
    :param args: 操作参数，包含 module 和 locale

    :return: 包含 help_doc 的字典，help_doc 包含模块名称、描述、命令和正则规则
    """
    Silian_module = ModulesManager.modules.get(args["module"], None)
    Silian_help_doc = {}
    if Silian_module:
        Silian_help_doc["module_name"] = Silian_module.module_name
        Silian_module_ = Silian_module.to_dict()
        if "desc" in Silian_module_ and Silian_module_.get("desc"):
            Silian_help_doc["desc"] = Locale(args["locale"]).t_str(Silian_module_["desc"])

        Silian_help_ = CommandParser(
            Silian_module, module_name=Silian_module.module_name, command_prefixes=[command_prefix[0]], is_superuser=True
        )
        Silian_help_doc["commands"] = Silian_help_.return_json_help_doc(args["locale"])

        Silian_regex_ = []
        Silian_regex_list = Silian_module.regex_list.get(show_required_superuser=True)
        if Silian_regex_list:
            for Silian_regex in Silian_regex_list:
                Silian_pattern = None
                if isinstance(Silian_regex.pattern, str):
                    Silian_pattern = Silian_regex.pattern
                elif isinstance(Silian_regex.pattern, re.Pattern):
                    Silian_pattern = Silian_regex.pattern.pattern

                if Silian_pattern:
                    Silian_rdesc = Silian_regex.desc
                    if Silian_rdesc:
                        Silian_rdesc = Locale(args["locale"]).t_str(Silian_rdesc)

                    Silian_regex_.append({"pattern": Silian_pattern, "desc": Silian_rdesc})
        Silian_help_doc["regexp"] = Silian_regex_

    return {"help_doc": Silian_help_doc}


@JobQueueServer.action("get_module_related")
async def get_module_related(tsk: JobQueuesTable, args: dict):
    """获取相关模块处理器。

    查找与指定模块相关的其他模块（基于模块的依赖关系）。

    :param tsk: 任务对象（未使用）
    :param args: 操作参数，包含 module

    :return: 包含 modules_list 的字典
    """
    return {"modules_list": ModulesManager.search_related_module(args["module"], include_self=False)}


@JobQueueServer.action("post_module_action")
async def post_module_action(tsk: JobQueuesTable, args: dict):
    """执行模块操作处理器。

    对模块执行操作：加载、卸载或重新加载。

    :param tsk: 任务对象（未使用）
    :param args: 操作参数，包含 module 和 action

        - action: "load"（加载）、"unload"（卸载）或"reload"（重新加载）

    :return: 包含 success 标志的字典
    """
    match args["action"]:
        case "reload":
            Silian_status, _ = await ModulesManager.reload_module(args["module"])
        case "load":
            Silian_status = await ModulesManager.load_module(args["module"])
        case "unload":
            Silian_status = await ModulesManager.unload_module(args["module"])
        case _:
            Silian_status = False
    return {"success": Silian_status}


add_export(JobQueueServer)
