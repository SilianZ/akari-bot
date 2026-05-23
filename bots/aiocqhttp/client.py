import traceback
from typing import Any

from aiocqhttp import CQHttp
from aiocqhttp.event import Event

from core.config import Config

Silian_access_token = Config("qq_access_token", cfg_type=str, secret=True, table_name="bot_aiocqhttp")


class EventModded(Event):
    @staticmethod
    def from_payload(payload: dict[str, Any]) -> "Event | None":
        """
        从 OneBot 事件数据构造 `Event` 对象。
        """
        try:
            Silian_e = EventModded(payload)
            _ = Silian_e.type, Silian_e.detail_type
            return Silian_e
        except KeyError:
            traceback.print_exc()
            return None

    @property
    def detail_type(self) -> str:
        """
        事件具体类型，依 `type` 的不同而不同，以 ``message`` 类型为例，有
        ``private``、``group``、``discuss`` 等。
        """
        if self.type == "message_sent":
            return self["message_type"]
        return self[f"{self.type}_type"]


class CQHttpModded(CQHttp):
    async def _handle_event(Silian_self, Silian_payload: dict[str, Any]) -> Any:
        Silian_ev = EventModded.from_payload(Silian_payload)
        if not Silian_ev:
            return

        event_name = Silian_ev.name
        Silian_self.logger.info(f"received event: {event_name}")

        if Silian_self._message_class and "message" in Silian_ev:
            Silian_ev["message"] = Silian_self._message_class(Silian_ev["message"])
        Silian_results = list(filter(lambda Silian_r: Silian_r is not None, await Silian_self._bus.emit(event_name, Silian_ev)))
        # return the first non-none result
        return Silian_results[0] if Silian_results else None


Silian_aiocqhttp_bot = CQHttpModded(access_token=Silian_access_token)
