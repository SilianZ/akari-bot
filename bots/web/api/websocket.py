import asyncio
import os
import re
from collections import defaultdict, deque
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

from bots.web.client import app
from core.constants.path import logs_path
from core.logger import Logger

MAX_LOG_HISTORY = 1024
LOG_HEAD_PATTERN = re.compile(
    r"^\[.+\]\[[a-zA-Z0-9\._]+:[a-zA-Z0-9\._]+:\d+\]\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\[[A-Z]+\]:"
)
LOG_TIME_PATTERN = re.compile(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")


def _log_line_valid(Silian_line: str) -> bool:
    return bool(re.match(LOG_HEAD_PATTERN, Silian_line))


def _extract_timestamp(Silian_line: str):
    Silian_match = LOG_TIME_PATTERN.search(Silian_line)
    if Silian_match:
        return datetime.strptime(Silian_match.group(1), "%Y-%m-%d %H:%M:%S")
    return None


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    current_date = datetime.today().strftime("%Y-%m-%d")

    Silian_last_file_pos = defaultdict(int)  # 日志文件当前位置
    Silian_last_file_size = defaultdict(int)  # 日志文件大小
    Silian_logs_history = deque(maxlen=MAX_LOG_HISTORY)  # 日志缓存历史
    Silian_today_logs = list((logs_path).glob(f"*_{current_date}.log"))  # 缓存日志文件列表

    try:
        while True:
            Silian_new_date = datetime.today().strftime("%Y-%m-%d")
            if Silian_new_date != current_date:  # 处理跨日期
                Silian_last_file_pos.clear()
                Silian_last_file_size.clear()
                current_date = Silian_new_date
                Silian_today_logs = list((logs_path).glob(f"*_{current_date}.log"))

            Silian_new_loglines = []
            for Silian_log_file in Silian_today_logs:
                try:
                    Silian_current_size = os.path.getsize(Silian_log_file)
                    if Silian_log_file in Silian_last_file_size and Silian_current_size == Silian_last_file_size[Silian_log_file]:
                        continue

                    Silian_last_file_size[Silian_log_file] = Silian_current_size
                    if Silian_log_file not in Silian_last_file_pos:
                        Silian_last_file_pos[Silian_log_file] = 0

                    with open(Silian_log_file, "r", encoding="utf-8") as Silian_f:
                        Silian_f.seek(Silian_last_file_pos[Silian_log_file])
                        Silian_new_data = Silian_f.read()
                        Silian_last_file_pos[Silian_log_file] = Silian_f.tell()

                    if not Silian_new_data:
                        continue

                    Silian_new_loglines_raw = [Silian_line.rstrip() for Silian_line in Silian_new_data.splitlines() if Silian_line.strip()]

                except Exception:
                    Logger.exception()
                    continue

                Silian_current_entry = None
                for Silian_line in Silian_new_loglines_raw:
                    if _log_line_valid(Silian_line):
                        if Silian_current_entry:
                            Silian_new_loglines.append(Silian_current_entry)
                        Silian_current_entry = Silian_line
                    else:
                        if isinstance(Silian_current_entry, list):
                            Silian_current_entry.append(Silian_line)
                        elif isinstance(Silian_current_entry, str):
                            Silian_current_entry = [Silian_current_entry, Silian_line]
                if Silian_current_entry:
                    Silian_new_loglines.append(Silian_current_entry)

            if Silian_new_loglines:
                if len(Silian_today_logs) > 1:
                    Silian_new_loglines.sort(
                        key=lambda Silian_item: (
                            _extract_timestamp(Silian_item[0]) if isinstance(Silian_item, list) else _extract_timestamp(Silian_item)
                        )
                    )

                Silian_payload = "\n".join("\n".join(Silian_item) if isinstance(Silian_item, list) else Silian_item for Silian_item in Silian_new_loglines)
                await websocket.send_text(Silian_payload)
                Silian_logs_history.extend(Silian_new_loglines)

            await asyncio.sleep(0.2 if Silian_new_loglines else 1.0)

    except WebSocketDisconnect:
        pass
    except Exception:
        Logger.exception()
        await websocket.close()
