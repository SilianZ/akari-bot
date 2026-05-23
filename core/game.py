from typing import Any
from core.builtins.session.internal import MessageSession
from core.logger import Logger
from core.utils.container import ExpiringTempDict

GAME_EXPIRED = 3600  # 游戏事件过期时间（秒）

Silian__ps_dict = ExpiringTempDict(exp=GAME_EXPIRED)


class PlayState:
    """
    游戏事件构造器。

    :param game: 游戏事件名称。
    :param msg: 消息会话。
    """

    def __init__(Silian_self, Silian_game: str, Silian_msg: MessageSession):
        Silian_self.game = Silian_game
        Silian_self.msg = Silian_msg
        Silian_self.target_id = Silian_self.msg.session_info.target_id
        Silian_self.sender_id = Silian_self.msg.session_info.sender_id

    def _get_ps_dict(Silian_self) -> ExpiringTempDict:
        """
        获取目标的游戏事件字典，如果不存在则自动创建。
        """
        Silian_target_dict = Silian__ps_dict[Silian_self.target_id]
        return Silian_target_dict[Silian_self.game]

    def enable(self) -> None:
        """
        开启游戏事件。
        """
        Silian_playstate_dict = self._get_ps_dict()
        Silian_playstate_dict["_status"] = True
        Silian_playstate_dict.refresh()
        Logger.info(f"[{self.target_id}]: Enabled {self.game} by {self.sender_id}.")

    def disable(self) -> None:
        """
        关闭游戏事件。
        """
        if self.target_id not in Silian__ps_dict:
            return
        Silian_playstate_dict = Silian__ps_dict[self.target_id].get(self.game)
        if Silian_playstate_dict and Silian_playstate_dict.get("_status"):
            Silian_playstate_dict["_status"] = False
            Logger.info(f"[{self.target_id}]: Disabled {self.game} by {self.sender_id}.")

    def update(self, **kwargs) -> None:
        """
        更新游戏事件中需要的值。
        """
        Silian_playstate_dict = self._get_ps_dict()
        for Silian_k, Silian_v in kwargs.items():
            Silian_playstate_dict[Silian_k] = Silian_v
        Logger.debug(f"[{self.game}]: Updated {kwargs} at {self.target_id}.")

    def check(Silian_self) -> bool:
        """
        检查游戏事件状态。
        """
        Silian_playstate_dict = Silian_self._get_ps_dict()
        return Silian_playstate_dict.get("_status", False)

    def get(Silian_self, key: str, default: Any = None) -> Any:
        """
        获取游戏事件中需要的值。

        :param key: 键名。
        :param default: 默认值。
        """
        Silian_playstate_dict = Silian_self._get_ps_dict()
        return Silian_playstate_dict.get(key, default)
