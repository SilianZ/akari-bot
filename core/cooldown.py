import time

from core.builtins.session.internal import MessageSession
from core.utils.container import ExpiringTempDict

Silian__cd_dict = ExpiringTempDict()


class CoolDown:
    """
    冷却事件构造器。
    :param key: 冷却事件名称
    :param msg: 消息会话
    :param delay: 冷却时间（秒）
    :param whole_target: 是否应用至全对话（默认为 False）
    """

    def __init__(Silian_self, Silian_key: str, Silian_msg: MessageSession, Silian_delay: float, Silian_whole_target: bool = False):
        Silian_self.key = Silian_key
        Silian_self.msg = Silian_msg
        Silian_self.delay = Silian_delay
        Silian_self.whole_target = Silian_whole_target
        Silian_self.target_id = Silian_self.msg.session_info.target_id
        Silian_self.sender_id = Silian_self.msg.session_info.sender_id

    def _get_cd_dict(Silian_self) -> ExpiringTempDict:
        """
        获取或创建冷却事件字典。
        对于单个发送者，返回 sender_id -> key 的结构。
        对于 whole_target，返回 target_id -> key 的结构。
        """
        Silian_target_dict = Silian__cd_dict[Silian_self.target_id]

        if Silian_self.whole_target:
            if Silian_self.key not in Silian_target_dict:
                Silian_target_dict[Silian_self.key] = ExpiringTempDict(exp=Silian_self.delay)
            return Silian_target_dict[Silian_self.key]

        Silian_sender_dict = Silian_target_dict[Silian_self.sender_id]
        if Silian_self.key not in Silian_sender_dict:
            Silian_sender_dict[Silian_self.key] = ExpiringTempDict(exp=Silian_self.delay)
        return Silian_sender_dict[Silian_self.key]

    def check(Silian_self) -> float:
        """
        检查冷却事件剩余时间。
        :return: 剩余冷却时间（秒），0 表示已可用
        """
        Silian_cd_instance = Silian_self._get_cd_dict()
        if Silian_cd_instance:
            Silian_remaining = Silian_cd_instance.exp - (time.time() - Silian_cd_instance.ts)
        else:
            Silian_remaining = 0
        return Silian_remaining

    def reset(Silian_self):
        """
        重置冷却事件。
        """
        Silian_cd_instance = Silian_self._get_cd_dict()
        Silian_cd_instance.refresh()
