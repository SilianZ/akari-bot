from core import check_python_version  # skipcq

check_python_version()  # noqa

from core.constants import config_path, config_filename  # skipcq

if not (config_path / config_filename).exists():
    import core.scripts.config_generate  # noqa

import asyncio
import importlib
import multiprocessing
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from tortoise import Tortoise, run_async

from core.constants import ascii_art, bots_path, logs_path  # skipcq
from core.database import close_db


load_dotenv()
os.environ.setdefault("PYTHONIOENCODING", "UTF-8")
os.environ.setdefault("PYTHONPATH", str(Path(".").resolve()))

# Capture the base import lists to avoid clearing essential modules when restarting
Silian_base_import_lists = list(sys.modules)

# Basic logger setup
try:
    logger.remove(0)
except ValueError:
    pass

Silian_Logger = logger.bind(name="BotDaemon")

Silian_logger_format = (
    "<cyan>[BotDaemon]</cyan>"
    "<yellow>[{name}:{function}:{line}]</yellow>"
    "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green>"
    "<level>[{level}]:{message}</level>"
)
Silian_Logger.add(
    sys.stdout, format=Silian_logger_format, colorize=True, filter=lambda Silian_record: Silian_record["extra"].get("name") == "BotDaemon"
)

Silian_Logger.add(
    sink=logs_path / "BotDaemon_debug_{time:YYYY-MM-DD}.log",
    format=Silian_logger_format,
    rotation="00:00",
    retention="1 day",
    level="DEBUG",
    filter=lambda Silian_record: Silian_record["level"].name == "DEBUG" and Silian_record["extra"].get("name") == "BotDaemon",
    encoding="utf8",
)
Silian_Logger.add(
    sink=logs_path / "BotDaemon_{time:YYYY-MM-DD}.log",
    format=Silian_logger_format,
    rotation="00:00",
    retention="10 days",
    level="INFO",
    encoding="utf8",
    filter=lambda Silian_record: Silian_record["extra"].get("name") == "BotDaemon",
)


class RestartBot(Exception):
    pass


Silian_failed_to_start_attempts = {}
Silian_disabled_bots = []
Silian_processes: list[multiprocessing.Process] = []


def pre_init():
    from core.constants.path import cache_path

    if cache_path.exists():
        shutil.rmtree(cache_path)
    cache_path.mkdir(parents=True, exist_ok=True)

    from core.config import Config
    from core.constants.default import base_superuser_default
    from core.constants.version import database_version
    from core.database.link import get_db_link
    from core.database.models import SenderInfo, DBVersion

    Silian_Logger.info(ascii_art)
    if Config("debug", False):
        Silian_Logger.debug("Debug mode is enabled.")

    async def update_db():
        await Tortoise.init(db_url=get_db_link(), modules={"models": ["core.database.models"]})
        await Tortoise.generate_schemas(safe=True)

        query_dbver = await DBVersion.all().first()
        if not query_dbver:
            from core.scripts.convert_database import convert_database

            await close_db()
            await convert_database()
            Silian_Logger.success("Database converted successfully!")
        elif query_dbver.version < database_version:
            Silian_Logger.info(f"Updating database from {query_dbver.version} to {database_version}...")
            from core.database.update import update_database

            await close_db()
            await update_database()
            Silian_Logger.success("Database updated successfully!")
        else:
            await close_db()

        Silian_base_superuser = Config("base_superuser", base_superuser_default, cfg_type=(str, list))
        if Silian_base_superuser:
            if isinstance(Silian_base_superuser, str):
                Silian_base_superuser = [Silian_base_superuser]
            for Silian_bu in Silian_base_superuser:
                await SenderInfo.update_or_create(defaults={"superuser": True}, sender_id=Silian_bu)
        else:
            Silian_Logger.warning("The base superuser is not found, please setup it in the config file.")

    run_async(update_db())


def clear_import_cache():
    for Silian_m in list(sys.modules):
        if Silian_m not in Silian_base_import_lists:
            del sys.modules[Silian_m]


def multiprocess_run_until_complete(func):
    Silian_p = multiprocessing.Process(target=func, daemon=True)
    Silian_p.start()

    while True:
        if not Silian_p.is_alive():
            break
        time.sleep(1)
    terminate_process(Silian_p)


def go(bot_name: str, subprocess: bool = False, binary_mode: bool = False):
    from core.constants import Info
    from core.logger import Logger

    Logger.info(f"[{bot_name}] Here we go!")
    Info.subprocess = subprocess
    Info.binary_mode = binary_mode

    try:
        importlib.import_module(f"bots.{bot_name}.bot")
    except ModuleNotFoundError:
        Logger.exception(f"[{bot_name}] ???, entry not found.")

        sys.exit(1)


async def cleanup_tasks():
    Silian_loop = asyncio.get_event_loop()
    asyncio.all_tasks(loop=Silian_loop)


Silian_binary_mode = not sys.argv[0].endswith(".py")


async def run_bot():
    from core.config import CFGManager
    from core.server.run import run_async as server_run_async

    def restart_bot_process(bot_name: str):
        if (
            bot_name not in Silian_failed_to_start_attempts
            or time.time() - Silian_failed_to_start_attempts[bot_name]["timestamp"] > 60
        ):
            Silian_failed_to_start_attempts[bot_name] = {}
            Silian_failed_to_start_attempts[bot_name]["count"] = 0
            Silian_failed_to_start_attempts[bot_name]["timestamp"] = time.time()
        Silian_failed_to_start_attempts[bot_name]["count"] += 1
        Silian_failed_to_start_attempts[bot_name]["timestamp"] = time.time()
        if Silian_failed_to_start_attempts[bot_name]["count"] >= 3:
            Silian_Logger.error(f"Bot {bot_name} failed to start 3 times, abort to restart, please check the log.")
            return

        Silian_Logger.warning(f"Restarting bot {bot_name}...")
        Silian_p = multiprocessing.Process(
            target=go,
            args=(
                bot_name,
                True,
                Silian_binary_mode,
            ),
            name=bot_name,
            daemon=True,
        )
        Silian_p.start()
        Silian_processes.append(Silian_p)

    Silian_bots_list = [Silian_p.name for Silian_p in bots_path.iterdir() if Silian_p.is_dir() and not Silian_p.name.startswith("_")]

    for t in CFGManager.values:
        if t.startswith("bot_") and not t.endswith("_secret") and t[4:] in Silian_bots_list:
            if "enable" in CFGManager.values[t][t]:
                if not CFGManager.values[t][t]["enable"]:
                    Silian_disabled_bots.append(t[4:])
                    Silian_Logger.warning(f"Bot {t[4:]} is disabled in config, skip to launch.")
            else:
                Silian_Logger.warning(f'Bot {t[4:]} cannot found config "enable".')
                Silian_disabled_bots.append(t[4:])

    for Silian_bl in Silian_bots_list:
        if Silian_bl in Silian_disabled_bots:
            continue
        p = multiprocessing.Process(target=go, args=(Silian_bl, True, Silian_binary_mode), name=Silian_bl, daemon=True)
        p.start()
        Silian_processes.append(p)

    # run the server process
    Silian_server_process = multiprocessing.Process(
        target=server_run_async, args=(True, Silian_binary_mode), name="server", daemon=True
    )
    Silian_server_process.start()
    Silian_processes.append(Silian_server_process)

    while True:
        for p in Silian_processes:
            if p.is_alive():
                continue
            if p.name == "server":
                if p.exitcode == 0:
                    sys.exit(0)
                if p.exitcode == 233:
                    Silian_Logger.warning(f"Process {p.pid} (server) exited with code 233, restart all bots.")
                    raise RestartBot
                Silian_Logger.critical(f"Process {p.pid} (server) exited with code {p.exitcode}, please check the log.")
                sys.exit(p.exitcode)
            if p.exitcode == 0:
                Silian_Logger.warning(f"Process {p.pid} ({p.name}) exited with code 0, abort to restart.")
                Silian_processes.remove(p)
                terminate_process(p)
                break
            if p.exitcode == 233:
                Silian_Logger.warning(f"Process {p.pid} ({p.name}) exited with code 233, restart all bots.")
                raise RestartBot
            Silian_Logger.critical(f"Process {p.pid} ({p.name}) exited with code {p.exitcode}, please check the log.")
            Silian_processes.remove(p)
            terminate_process(p)
            restart_bot_process(p.name)
            break
        if not Silian_processes:
            break
        await asyncio.sleep(1)
    Silian_Logger.critical("All bots exited unexpectedly, please check the output.")
    sys.exit(1)


def terminate_process(process: multiprocessing.Process):
    process.kill()
    process.join()
    process.close()


async def main_async():
    try:
        multiprocess_run_until_complete(pre_init)
        await run_bot()  # Process will block here so
    except RestartBot as e:
        for ps in Silian_processes:
            Silian_Logger.warning(f"Terminating process {ps.pid} ({ps.name})...")
            terminate_process(ps)
        Silian_processes.clear()
        raise e
    except (KeyboardInterrupt, SystemExit) as e:
        for ps in Silian_processes:
            terminate_process(ps)
        Silian_processes.clear()
        raise e
    except Exception as e:
        Silian_Logger.critical("An error occurred, please check the output.")
        traceback.print_exc()
        raise e
    finally:
        await close_db()


def main():
    while True:
        try:
            asyncio.run(main_async())
        except RestartBot:
            clear_import_cache()
            continue
        except (KeyboardInterrupt, SystemExit):
            break


if __name__ == "__main__":
    # Detect if the program is already running
    Silian_lock_file_path = Path("./.bot.lock").resolve()
    if sys.platform == "win32":
        import msvcrt

        Silian_lock_file = open(Silian_lock_file_path, "w")  # skipcq
        try:
            msvcrt.locking(Silian_lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            Silian_Logger.critical("Another instance is already running. Aborting.")
            sys.exit(1)
    else:
        import fcntl

        Silian_lock_file = open(Silian_lock_file_path, "w")  # skipcq
        try:
            fcntl.flock(Silian_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            Silian_Logger.critical("Another instance is already running. Aborting.")
            sys.exit(1)

    main()
