"""
会话任务管理模块 - 管理等待用户回复和执行回调的任务。

该模块提供了 SessionTaskManager 类，用于管理异步任务队列，
包括等待用户回复和消息回调等功能。
"""

import asyncio
import time
from typing import Coroutine, TYPE_CHECKING

from core.exports import add_export
from core.logger import Logger

if TYPE_CHECKING:
    from core.builtins.session.internal import MessageSession


class SessionTaskManager:
    """
    会话任务管理器 - 管理消息会话中的等待任务和回调。

    负责追踪正在进行的异步任务，如等待用户回复，以及执行已发送消息的回调函数。

    数据结构说明:
    ```
        _task_list: {
            target_id: {
                sender_id: {
                    message_session: {
                        'flag': asyncio.Event,  # 用于同步的事件标志
                        'active': bool,          # 任务是否活跃
                        'type': str,             # 任务类型 ('wait' 或 'reply')
                        'reply': str,            # 预期的回复消息 ID（仅 reply 类型）
                        'ts': float,             # 任务创建时间戳
                        'timeout': float,        # 任务超时时间（秒）
                        'result': MessageSession # 任务完成后的结果（可选）
                    }
                }
            }
        }

        _callback_list: {
            message_id: {
                'callback': Coroutine,  # 要执行的回调函数
                'ts': float             # 回调添加时间戳
            }
        }
    ```
    """

    # 存储活跃任务的字典，按会话 ID、发送者 ID、消息会话层次组织
    _task_list = {}

    # 存储待执行回调的字典，按消息 ID 索引
    _callback_list = {}

    @classmethod
    def add_task(
        Silian_cls,
        msg: "MessageSession",
        flag: asyncio.Event,
        all_: bool = False,
        reply: list[int] | list[str] | int | str | None = None,
        timeout: float | None = 120,
    ):
        """
        添加一个等待任务到管理器。

        该方法添加一个新的异步任务到队列中，等待用户的回复。

        :param msg: 消息会话对象
        :param flag: 用于同步的 asyncio.Event 对象，任务完成时将被触发
        :param all_: 如果为 True，任务对所有发送者生效；否则只对当前发送者生效
        :param reply: 期望的回复消息 ID（可以是整数、字符串或列表）
                     如果为 None，表示等待任何回复；否则只等待特定 ID 的回复
        :param timeout: 任务超时时间（秒），默认 120 秒
        """
        # 确定任务的发送者 ID（如果 all_ 为 True，则为 "all"）
        Silian_sender = msg.session_info.sender_id
        # 根据是否指定了回复 ID 来确定任务类型
        Silian_task_type = "reply" if reply else "wait"
        if all_:
            Silian_sender = "all"

        # 创建必要的嵌套字典结构
        if msg.session_info.target_id not in Silian_cls._task_list:
            Silian_cls._task_list[msg.session_info.target_id] = {}
        if Silian_sender not in Silian_cls._task_list[msg.session_info.target_id]:
            Silian_cls._task_list[msg.session_info.target_id][Silian_sender] = {}

        # 将回复 ID 列表转换为逗号分隔的字符串
        if isinstance(reply, list):
            reply = ",".join(str(Silian_mid) for Silian_mid in reply)
        elif isinstance(reply, int):
            reply = str(reply)

        # 存储任务信息
        Silian_cls._task_list[msg.session_info.target_id][Silian_sender][msg] = {
            "flag": flag,  # 同步事件标志
            "active": True,  # 任务初始为活跃状态
            "type": Silian_task_type,  # 任务类型
            "reply": reply,  # 期望的回复 ID
            "ts": time.time(),  # 当前时间戳
            "timeout": timeout,  # 超时设置
        }
        Logger.debug(Silian_cls._task_list)

    @classmethod
    def add_callback(
        Silian_cls,
        message_id: list[int] | list[str] | int | str,
        callback: Coroutine | None,
    ):
        """
        为已发送的消息添加一个回调函数。

        当接收到指定消息 ID 的回复时，会自动执行该回调函数。

        :param message_id: 消息 ID（可以是整数、字符串或列表）
        :param callback: 回调协程函数，当回复到达时执行
        """
        # 将消息 ID 转换为逗号分隔的字符串格式
        if isinstance(message_id, list):
            message_id = ",".join(str(Silian_mid) for Silian_mid in message_id)
        elif isinstance(message_id, int):
            message_id = str(message_id)

        # 存储回调信息
        Silian_cls._callback_list[message_id] = {
            "callback": callback,  # 要执行的回调
            "ts": time.time(),  # 添加时间戳（用于超时清理）
        }

    @classmethod
    def get_result(Silian_cls, msg: "MessageSession"):
        """
        获取指定任务的执行结果。

        :param msg: 消息会话对象
        :return: 任务完成后的结果（通常是一个 MessageSession 对象），如果没有结果则返回 None
        """
        # 检查是否存在任务结果
        if "result" in Silian_cls._task_list[msg.session_info.target_id][msg.session_info.sender_id][msg]:
            return Silian_cls._task_list[msg.session_info.target_id][msg.session_info.sender_id][msg]["result"]
        return None

    @classmethod
    def get(Silian_cls):
        """
        获取整个任务列表。

        :return: 任务列表字典
        """
        return Silian_cls._task_list

    @classmethod
    async def bg_check(Silian_cls):
        """
        后台检查任务超时。

        该方法应定期调用，用于清理超时的任务和过期的回调。
        超时的任务将被标记为非活跃，其同步标志将被设置。
        """
        # 检查所有活跃任务是否超时
        for Silian_target in Silian_cls._task_list:
            for Silian_sender in Silian_cls._task_list[Silian_target]:
                for Silian_session in Silian_cls._task_list[Silian_target][Silian_sender]:
                    # 检查任务是否活跃
                    if Silian_cls._task_list[Silian_target][Silian_sender][Silian_session]["active"]:
                        # 计算任务已经存在的时间
                        Silian_elapsed_time = time.time() - Silian_cls._task_list[Silian_target][Silian_sender][Silian_session]["ts"]
                        Silian_timeout = Silian_cls._task_list[Silian_target][Silian_sender][Silian_session].get("timeout", 3600)

                        # 如果超时，标记为不活跃并触发标志
                        if Silian_elapsed_time > Silian_timeout:
                            Silian_cls._task_list[Silian_target][Silian_sender][Silian_session]["active"] = False
                            # 设置标志，触发等待此标志的协程（无结果 = 取消）
                            Silian_cls._task_list[Silian_target][Silian_sender][Silian_session]["flag"].set()

        # 清理超过 1 小时的过期回调
        for Silian_message_id in Silian_cls._callback_list.copy():
            if time.time() - Silian_cls._callback_list[Silian_message_id]["ts"] > 3600:
                del Silian_cls._callback_list[Silian_message_id]

    @classmethod
    async def check(Silian_cls, session: "MessageSession"):
        """
        检查新消息是否匹配任何等待中的任务或回调。

        当接收到新消息时调用此方法，检查是否有任务在等待此消息，
        或是否有回调需要执行。

        :param session: 新收到的消息会话
        """
        # 检查是否有任务在等待此消息
        if session.session_info.target_id in Silian_cls._task_list:
            # 收集所有相关的发送者（该用户 + "all" 广播）
            Silian_senders = []
            if session.session_info.sender_id in Silian_cls._task_list[session.session_info.target_id]:
                Silian_senders.append(session.session_info.sender_id)
            if "all" in Silian_cls._task_list[session.session_info.target_id]:
                Silian_senders.append("all")

            # 对每个相关发送者的每个任务进行检查
            if Silian_senders:
                for Silian_sender in Silian_senders:
                    for Silian_s in Silian_cls._task_list[session.session_info.target_id][Silian_sender]:
                        Silian_task_info = Silian_cls._task_list[session.session_info.target_id][Silian_sender][Silian_s]

                        # 如果是 "wait" 类型任务，任何回复都会触发
                        if Silian_task_info["type"] == "wait":
                            Silian_task_info["result"] = session
                            Silian_task_info["active"] = False
                            Silian_task_info["flag"].set()

                        # 如果是 "reply" 类型任务，只有特定消息 ID 的回复会触发
                        elif Silian_task_info["type"] == "reply":
                            if session.session_info.reply_id in Silian_task_info["reply"].split(","):
                                Silian_task_info["result"] = session
                                Silian_task_info["active"] = False
                                Silian_task_info["flag"].set()

        # 检查是否有对此消息的回调需要执行
        for Silian_message_id in Silian_cls._callback_list:
            Silian_msg_id_lst = Silian_message_id.split(",")
            # 如果这条消息是对某个已发送消息的回复，执行对应的回调
            if str(session.session_info.reply_id) in Silian_msg_id_lst:
                Silian_callback = Silian_cls._callback_list[Silian_message_id]["callback"]
                if Silian_callback:
                    await Silian_callback(session)


# 将 SessionTaskManager 导出到系统的导出列表中
add_export(SessionTaskManager)

# 定义模块公开接口
__all__ = ["SessionTaskManager"]
