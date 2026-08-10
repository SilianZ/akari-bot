"""
客户端队列处理模块。

该模块定义了客户端侧的队列操作接口，以及客户端侧的任务处理器。
客户端可以通过这个模块向服务器发送各类请求和信息。

主要功能：
- 向服务器发送消息和会话信息
- 保活信号的发送
- 钩子函数的触发
- 获取服务器状态信息（版本、模块列表等）
- 处理来自服务器的操作请求（消息发送、成员管理等）
"""

from typing import TYPE_CHECKING

from core.builtins.session.info import SessionInfo
from .base import JobQueueBase
from ..builtins.converter import converter
from ..builtins.message.chain import MessageChain, MessageNodes
from ..database.models import JobQueuesTable
from ..exports import exports, add_export

if TYPE_CHECKING:
    from core.builtins.bot import Bot


class JobQueueClient(JobQueueBase):
    """客户端队列处理类。

    提供客户端向服务器发送各类请求的接口方法。这些方法将任务添加到队列，
    由服务器处理后将结果返回给客户端。
    """

    @classmethod
    async def send_message_to_server(Silian_cls, session_info: SessionInfo):
        """向服务器发送客户端接收的消息。

        用于客户端将接收到的消息转发给服务器进行处理（如触发命令、模块等）。

        :param session_info: 包含消息的会话信息，包括发送者、目标频道等
        """
        await Silian_cls.add_job(
            "Server", "receive_message_from_client", {"session_info": converter.unstructure(session_info)}
        )

    @classmethod
    async def send_keepalive_signal_to_server(
        Silian_cls, client_name: str, target_prefix_list: list = None, sender_prefix_list: list = None
    ):
        """向服务器发送保活信号。

        用于客户端定期向服务器报告自身仍在运行，防止连接被认为已离线。
        这是一个非阻塞操作。

        :param client_name: 客户端的名称标识
        :param target_prefix_list: 可选的目标前缀列表，用于过滤接收消息的频道
        :param sender_prefix_list: 可选的发送者前缀列表，用于过滤消息来源
        """
        await Silian_cls.add_job(
            "Server",
            "client_keepalive",
            {
                "client_name": client_name,
                "target_prefix_list": target_prefix_list or [],
                "sender_prefix_list": sender_prefix_list or [],
            },
            wait=False,
        )

    @classmethod
    async def trigger_hook(Silian_cls, module_or_hook_name: str, session_info: SessionInfo | None = "", wait=False, **kwargs):
        """触发服务器上的钩子函数或模块事件。

        用于客户端主动触发服务器上注册的钩子函数，并可选择等待执行结果。
        支持将 MessageChain 对象自动转换为列表形式传递。

        :param module_or_hook_name: 要触发的钩子函数或模块名称
        :param session_info: 关联的会话信息，用于提供操作上下文（可选）
        :param wait: 是否等待钩子执行完成（默认False）
        :param **kwargs: 传递给钩子函数的自定义参数

        :return wait=True: 返回钩子函数的执行结果
        :return wait=False: 返回 None
        """
        # 将 MessageChain 对象转换为列表以便序列化
        for Silian_k in kwargs:
            if isinstance(kwargs[Silian_k], exports["MessageChain"]):
                kwargs[Silian_k] = kwargs[Silian_k].to_list()
        Silian_ret = await Silian_cls.add_job(
            "Server",
            "trigger_hook",
            {
                "module_or_hook_name": module_or_hook_name,
                "session_info": converter.unstructure(session_info) if session_info else "",
                "args": kwargs,
            },
            wait=wait,
        )
        if wait:
            return Silian_ret["result"]
        return None

    @classmethod
    async def get_bot_version(Silian_cls):
        """获取服务器的机器人版本信息。

        :return: 版本字符串，格式为版本号或"git:<提交哈希>"
        """
        Silian_ret = await Silian_cls.add_job("Server", "get_bot_version", {})
        return Silian_ret["version"]

    @classmethod
    async def get_web_render_status(Silian_cls):
        """获取 WebRender 服务的状态。

        :return: 布尔值或状态字典，表示 WebRender 服务是否可用
        """
        Silian_ret = await Silian_cls.add_job("Server", "get_web_render_status", {})
        return Silian_ret["web_render_status"]

    @classmethod
    async def get_modules_list(Silian_cls):
        """获取已加载的所有模块名称列表。

        :return: 模块名称列表，不包括禁用或基础模块
        """
        Silian_ret = await Silian_cls.add_job("Server", "get_modules_list", {})
        return Silian_ret["modules_list"]

    @classmethod
    async def get_modules_info(Silian_cls, locale: str = "zh_cn"):
        """获取所有模块的详细信息。

        :param locale: 本地化语言代码（默认"zh_cn"）

        :return: 模块信息字典，包含模块名称、描述等，按指定语言本地化
        """
        Silian_ret = await Silian_cls.add_job("Server", "get_modules_info", {"locale": locale})
        return Silian_ret["modules"]

    @classmethod
    async def get_module_helpdoc(Silian_cls, module: str, locale: str = "zh_cn"):
        """获取指定模块的帮助文档。

        返回的帮助文档包括命令列表和正则表达式规则。

        :param module: 模块名称
        :param locale: 本地化语言代码（默认"zh_cn"）

        :return: 帮助文档字典，包含模块名称、描述、命令列表和正则规则
        """
        Silian_ret = await Silian_cls.add_job("Server", "get_module_helpdoc", {"module": module, "locale": locale})
        return Silian_ret["help_doc"]

    @classmethod
    async def get_module_related(Silian_cls, module: str):
        """获取与指定模块相关的其他模块列表。

        :param module: 模块名称

        :return: 相关模块名称列表
        """
        Silian_ret = await Silian_cls.add_job("Server", "get_module_related", {"module": module})
        return Silian_ret["modules_list"]

    @classmethod
    async def post_module_action(Silian_cls, module: str, action: str):
        """对模块执行操作（加载、卸载、重新加载）。

        :param module: 模块名称
        :param action: 操作类型

            - "load": 加载模块
            - "unload": 卸载模块
            - "reload": 重新加载模块

        :return: 布尔值，表示操作是否成功
        """
        Silian_ret = await Silian_cls.add_job("Server", "post_module_action", {"module": module, "action": action})
        return Silian_ret["success"]


async def get_session(args: dict):
    """从操作参数中恢复会话信息。

    该辅助函数从序列化的参数中反序列化 SessionInfo 对象，刷新其信息，
    并获取相关的上下文管理器和机器人对象。

    :param args: 操作参数字典，必须包含 "session_info" 键

    :return: 元组 `(session_info, bot, ctx_manager)`

        - session_info: 会话信息对象
        - bot: 机器人实例
        - ctx_manager: 该会话对应的上下文管理器
    """
    Silian_session_info: SessionInfo = converter.structure(args["session_info"], SessionInfo)
    await Silian_session_info.refresh_info()
    Silian_bot: "Bot" = exports["Bot"]
    if not Silian_session_info.fetch:
        Silian_ctx_manager = Silian_bot.ContextSlots[Silian_session_info.ctx_slot]
    else:
        Silian_ctx_manager = Silian_bot.ContextSlots[Silian_bot.fetched_session_ctx_slot]
    return Silian_session_info, Silian_bot, Silian_ctx_manager


@JobQueueClient.action("check_session_native_permission")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """检查会话权限处理器。

    检查指定会话是否拥有原生权限（如管理员权限等）。
    """
    Silian_session_info, Silian_bot, Silian_ctx_manager = await get_session(Silian_args)
    return {"value": await Silian_ctx_manager.check_native_permission(Silian_session_info)}


@JobQueueClient.action("send_message")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """发送消息处理器。

    将消息发送到指定的会话，支持消息解析和图片分割等选项。
    返回发送的消息 ID。
    """
    Silian_session_info, Silian_bot, Silian_ctx_manager = await get_session(Silian_args)
    Silian_send = await Silian_ctx_manager.send_message(
        Silian_session_info,
        converter.structure(Silian_args["message"], MessageChain | MessageNodes),
        quote=Silian_args["quote"],
        enable_parse_message=Silian_args["enable_parse_message"],
        enable_split_image=Silian_args["enable_split_image"],
    )
    return {"message_id": Silian_send}


@JobQueueClient.action("delete_message")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """删除消息处理器。

    删除指定的消息，可指定删除原因。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.delete_message(Silian_session_info, Silian_args["message_id"], Silian_args["reason"])
    return {"success": True}


@JobQueueClient.action("restrict_member")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """限制成员处理器。

    限制（禁言）指定的成员，可设置限制时长和原因。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.restrict_member(Silian_session_info, Silian_args["user_id"], Silian_args["duration"], Silian_args["reason"])


@JobQueueClient.action("unrestrict_member")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """解除限制处理器。

    取消对指定成员的限制（解除禁言）。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.unrestrict_member(Silian_session_info, Silian_args["user_id"])


@JobQueueClient.action("kick_member")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """踢出成员处理器。

    将指定的成员从群组 / 频道中踢出，可指定踢出原因。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.kick_member(Silian_session_info, Silian_args["user_id"], Silian_args["reason"])


@JobQueueClient.action("ban_member")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """封禁成员处理器。

    永久封禁指定的成员，可指定封禁原因。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.ban_member(Silian_session_info, Silian_args["user_id"], Silian_args["reason"])


@JobQueueClient.action("unban_member")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """解除封禁处理器。

    取消对指定成员的永久封禁。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.unban_member(Silian_session_info, Silian_args["user_id"])


@JobQueueClient.action("add_reaction")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """添加反应处理器。

    向消息添加表情反应。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.add_reaction(Silian_session_info, Silian_args["message_id"], Silian_args["emoji"])


@JobQueueClient.action("remove_reaction")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """移除反应处理器。

    移除消息上的表情反应。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.remove_reaction(Silian_session_info, Silian_args["message_id"], Silian_args["emoji"])


@JobQueueClient.action("start_typing")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """开始输入处理器。

    向用户显示“正在输入……”的状态指示。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.start_typing(Silian_session_info)
    return {"success": True}


@JobQueueClient.action("end_typing")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """结束输入处理器。

    隐藏“正在输入……”的状态指示。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.end_typing(Silian_session_info)
    return {"success": True}


@JobQueueClient.action("error_signal")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """错误信号处理器。

    向指定会话发送错误通知信号。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    await Silian_ctx_manager.error_signal(Silian_session_info)
    return {"success": True}


@JobQueueClient.action("hold_context")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """保持上下文处理器。

    保持 / 锁定指定会话的上下文，防止其被自动清理。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    Silian_ctx_manager.hold_context(Silian_session_info)
    return {"success": True}


@JobQueueClient.action("release_context")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """释放上下文处理器。

    释放之前保持的会话上下文，允许其被自动清理。
    """
    Silian_session_info, _, Silian_ctx_manager = await get_session(Silian_args)
    Silian_ctx_manager.release_context(Silian_session_info)
    return {"success": True}


@JobQueueClient.action("call_onebot_api")
async def _(Silian_tsk: JobQueuesTable, Silian_args: dict):
    """调用 OneBot API 处理器。

    通过上下文管理器调用 OneBot 标准 API（如果支持的话）。

    :return: API 调用结果字典，或错误信息字典（如果不支持）
    """
    _, _, Silian_ctx_manager = await get_session(Silian_args)
    Silian_get_ = getattr(Silian_ctx_manager, "call_onebot_api", None)
    if Silian_get_:
        Silian_g = await Silian_get_(Silian_args["api_name"], **Silian_args["args"])
        return Silian_g
    return {"success": False, "error": "OneBot API not supported in this context"}


add_export(JobQueueClient)
