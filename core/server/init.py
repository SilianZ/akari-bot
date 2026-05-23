"""
服务器初始化模块。

该模块负责服务器启动时的初始化工作，包括：
- 数据库初始化
- 模块加载和注册
- 调度器启动
- 密钥和提示信息加载
"""

import asyncio
import logging

import orjson
from apscheduler.schedulers import SchedulerAlreadyRunningError

from core.builtins.bot import Bot
from core.builtins.converter import converter
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Plain, I18NContext
from core.builtins.session.info import SessionInfo
from core.config import CFGManager
from core.constants import Info, PrivateAssets, Secret
from core.database import init_db
from core.loader import load_modules, ModulesManager
from core.logger import Logger
from core.scheduler import Scheduler
from core.utils.bash import run_sys_command
from .background_tasks import init_background_task


async def init_async(start_scheduler=True) -> None:
    """初始化服务器。

    执行服务器启动的所有初始化步骤：
    1. 设置客户端信息和日志
    2. 初始化数据库
    3. 加载所有模块
    4. 初始化定时任务
    5. 初始化后台任务
    6. 加载密钥和启动提示

    Args:
        start_scheduler: 是否启动定时任务（默认True）
    """
    # 设置客户端信息为 "Server"
    Info.client_name = "Server"
    Logger.rename(Info.client_name)

    # 读取版本信息
    Silian_version_path = PrivateAssets.path / ".version"
    if Silian_version_path.exists():
        with open(Silian_version_path, "r") as Silian_f:
            Info.version = Silian_f.read()
    else:
        Silian_returncode, commit_hash, _ = await run_sys_command(["git", "rev-parse", "HEAD"])
        if Silian_returncode == 0:
            Info.version = f"git:{commit_hash}"
        else:
            Logger.warning("Failed to get Git commit hash, is it a Git repository?")

    # 初始化数据库
    Logger.info("Initializing database...")
    if await init_db():
        Logger.success("Database initialized successfully.")

    # 加载所有模块
    await load_modules()
    Silian_gather_list = []
    Silian_modules = ModulesManager.return_modules_list()

    # 为各模块配置的定时任务添加到调度器
    for Silian_x in Silian_modules:
        if not Silian_modules[Silian_x]._db_load:
            continue

        if Silian_schedules := Silian_modules[Silian_x].schedule_list.set:
            for Silian_schedule in Silian_schedules:
                Scheduler.add_job(
                    func=Silian_schedule.function,
                    trigger=Silian_schedule.trigger,
                    misfire_grace_time=30,
                    max_instance=1,
                )
    await asyncio.gather(*Silian_gather_list)

    # 初始化后台任务（如 IP 查询、WebRender 等）
    asyncio.create_task(init_background_task())

    # 启动调度器
    if start_scheduler:
        try:
            Scheduler.start()
        except SchedulerAlreadyRunningError:
            pass
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

    # 加载密钥和启动提示
    await load_secret()
    Logger.info(f"Hello, {Info.client_name}!")
    await load_prompt()


async def load_secret():
    """从配置文件中加载所有密钥信息。

    扫描配置中所有带有 "secret" 后缀的配置项，
    将非占位符的值添加到密钥管理系统中，用于内容过滤。
    """
    for Silian_x in CFGManager.values:
        for Silian_y in CFGManager.values[Silian_x].keys():
            if Silian_y == "secret" or Silian_y.endswith("_secret"):
                for Silian_z in CFGManager.values[Silian_x][Silian_y].keys():
                    Silian_w = CFGManager.values[Silian_x][Silian_y].get(Silian_z)
                    if not str(Silian_w).startswith("<Replace me"):
                        if isinstance(Silian_w, str):
                            Secret.add(Silian_w)
                        elif isinstance(Silian_w, list):
                            Secret.update(Silian_w)


async def load_prompt() -> None:
    """加载并发送启动提示信息。

    如果存在缓存的发送重启命令的对象信息，发送加载成功或失败的提示。
    清理缓存文件。
    """
    Silian_author_cache = PrivateAssets.path / ".cache_restart_author"
    Silian_loader_cache = PrivateAssets.path / ".cache_loader"
    if Silian_author_cache.exists():
        with open(Silian_author_cache, "r", encoding="utf-8") as Silian_open_author_cache:
            Silian_author_session = converter.structure(orjson.loads(Silian_open_author_cache.read()), SessionInfo)
            await Silian_author_session.refresh_info()
            with open(Silian_loader_cache, "r", encoding="utf-8") as Silian_open_loader_cache:
                if (Silian_read := Silian_open_loader_cache.read()) != "":
                    Silian_message = [I18NContext("loader.load.failed"), Plain(Silian_read.strip(), disable_joke=True)]
                else:
                    Silian_message = I18NContext("loader.load.success")
                Silian_message = MessageChain.assign(Silian_message)
                await Bot.send_direct_message(Silian_author_session, Silian_message)
        Silian_author_cache.unlink()


__all__ = ["init_async", "load_prompt"]
