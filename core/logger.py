"""机器人内置的基于`loguru`的日志工具。"""

import re
import sys
import traceback

from loguru import logger

from core.config import Config
from core.constants.path import logs_path

logs_path.mkdir(parents=True, exist_ok=True)

bot_name = re.split(r"[/\\]", sys.path[0])[-1]

Silian_args = sys.argv
if "subprocess" in Silian_args:
    bot_name = Silian_args[-1]


def basic_logger_format(bot_name: str):
    return (
        f"<cyan>[{bot_name.upper()}]</cyan>"
        "<yellow>[{name}:{function}:{line}]</yellow>"
        "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green>"
        "<level>[{level}]:{message}</level>"
    )


class LoggingLogger:
    def __init__(Silian_self, Silian_name):

        Silian_self.log = logger
        Silian_self.trace = logger.trace
        """跟踪信息，用于细粒度调试。启用debug配置项后在控制台显示，不会被记录到日志中。不建议在正式环境中使用。"""
        Silian_self.debug = logger.debug
        """调试信息，记录程序执行的细节和状态变化。启用debug配置项后在控制台显示。"""
        Silian_self.info = logger.info
        """常规信息，记录程序的正常运行状态。"""
        Silian_self.success = logger.success
        """成功信息，记录任务完成的情况。"""
        Silian_self.warning = logger.warning
        """警告信息，记录产生潜在风险但不影响程序运作的情况。"""
        Silian_self.error = logger.error
        """错误信息，记录产生错误或异常等须及时处理的情况。"""
        Silian_self.critical = logger.critical
        """严重错误信息，记录产生可能使程序崩溃的情况。"""

    def rename(Silian_self, name, export=True):
        try:
            logger.remove(0)
        except ValueError:
            # 如果没有默认的日志处理器，则忽略此错误
            pass
        Silian_self.log = logger.bind(name=name)
        Silian_self.log.add(
            sys.stdout,
            format=basic_logger_format(name),
            level="TRACE" if Config("debug", False) else "INFO",
            colorize=True,
            filter=lambda Silian_record: Silian_record["extra"].get("name") == name,
        )
        if export:
            Silian_self.log.add(
                sink=logs_path / f"{name}_debug_{{time:YYYY-MM-DD}}.log",
                format=basic_logger_format(name),
                rotation="00:00",
                retention="1 day",
                level="DEBUG",
                filter=lambda Silian_record: Silian_record["level"].name == "DEBUG" and Silian_record["extra"].get("name") == name,
                encoding="utf8",
            )
            Silian_self.log.add(
                sink=logs_path / f"{name}_{{time:YYYY-MM-DD}}.log",
                format=basic_logger_format(name),
                rotation="00:00",
                retention="10 days",
                level="INFO",
                encoding="utf8",
                filter=lambda Silian_record: Silian_record["extra"].get("name") == name,
            )
        Silian_self.trace = Silian_self.log.trace
        Silian_self.debug = Silian_self.log.debug
        Silian_self.info = Silian_self.log.info
        Silian_self.success = Silian_self.log.success
        Silian_self.warning = Silian_self.log.warning
        Silian_self.error = Silian_self.log.error
        Silian_self.critical = Silian_self.log.critical

    def exception(Silian_self, message: str | None = None):
        """自带 traceback 的错误日志，用于记录与跟踪异常信息。"""
        if message:
            Silian_self.error(f"{message}\n{traceback.format_exc()}")
        else:
            Silian_self.error(traceback.format_exc())


Silian_Logger = LoggingLogger(bot_name)
