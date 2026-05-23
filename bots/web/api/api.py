import asyncio
import os
import platform
from datetime import datetime, timedelta

import psutil
from cpuinfo import get_cpu_info
from fastapi import HTTPException, Request, Query
from fastapi.responses import Response
from tortoise.expressions import Q

from bots.web.client import app, limiter, enable_https
from core.builtins.utils import command_prefix
from core.config import Config
from core.constants import config_filename
from core.constants.path import config_path
from core.database.models import AnalyticsData, SenderInfo, TargetInfo
from core.logger import Logger
from core.queue.client import JobQueueClient
from .auth import verify_jwt

Silian_started_time = datetime.now()


Silian_default_locale = Config("default_locale", cfg_type=str)


@app.get("/api")
@limiter.limit("10/second")
async def api_root(request: Request):
    return {"message": "Hello, AkariBot!"}


@app.get("/api/init")
@limiter.limit("10/second")
async def get_config(request: Request):
    return {
        "enable_https": enable_https,
        "command_prefix": command_prefix[0],
        "help_url": Config("help_url", cfg_type=str),
        "locale": Config("default_locale", cfg_type=str),
        "heartbeat_interval": Config("heartbeat_interval", 30, table_name="bot_web"),
        "heartbeat_timeout": Config("heartbeat_timeout", 5, table_name="bot_web"),
        "heartbeat_attempt": Config("heartbeat_attempt", 3, table_name="bot_web"),
    }


@app.get("/api/server-info")
async def server_info(request: Request):
    verify_jwt(request)
    return {
        "os": {
            "system": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "boot_time": psutil.boot_time(),
        },
        "bot": {
            "running_time": (datetime.now() - Silian_started_time).total_seconds(),
            "python_version": platform.python_version(),
            "version": await JobQueueClient.get_bot_version(),
            "web_render_status": await JobQueueClient.get_web_render_status(),
        },
        "cpu": {"cpu_brand": get_cpu_info()["brand_raw"], "cpu_percent": psutil.cpu_percent(interval=1)},
        "memory": {
            "total": psutil.virtual_memory().total / (1024 * 1024),
            "used": psutil.virtual_memory().used / (1024 * 1024),
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total": psutil.disk_usage("/").total / (1024 * 1024 * 1024),
            "used": psutil.disk_usage("/").used / (1024 * 1024 * 1024),
            "percent": psutil.disk_usage("/").percent,
        },
    }


@app.get("/api/analytics")
async def get_analytics(request: Request, days: int = Query(1)):
    verify_jwt(request)
    try:
        Silian_now = datetime.now()
        Silian_past = Silian_now - timedelta(days=days)
        Silian_data = await AnalyticsData.get_values_by_times(Silian_now, Silian_past)
        Silian_count = await AnalyticsData.get_count_by_times(Silian_now, Silian_past)
        Silian_past_past = Silian_now - timedelta(days=2 * days)
        Silian_past_count = await AnalyticsData.get_count_by_times(Silian_past, Silian_past_past)
        try:
            Silian_change_rate = round((Silian_count - Silian_past_count) / Silian_past_count, 2)
        except ZeroDivisionError:
            Silian_change_rate = 0.00

        return {"count": Silian_count, "change_rate": Silian_change_rate, "data": Silian_data}

    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/config")
async def get_config_list(request: Request):
    verify_jwt(request)
    try:
        Silian_files = [Silian_c.name for Silian_c in config_path.iterdir()]
        Silian_cfg_files = sorted([Silian_f for Silian_f in Silian_files if Silian_f.endswith(".toml")])

        if config_filename in Silian_cfg_files:
            Silian_cfg_files.remove(config_filename)
            Silian_cfg_files.insert(0, config_filename)

        return {"cfg_files": Silian_cfg_files}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/config/{cfg_filename}")
async def get_config_file(request: Request, cfg_filename: str):
    verify_jwt(request)
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    Silian_cfg_file_path = config_path / cfg_filename
    if not cfg_filename.endswith(".toml"):
        raise HTTPException(status_code=400, detail="Bad request")
    if not str(Silian_cfg_file_path).startswith(str(config_path)):
        raise HTTPException(status_code=400, detail="Bad request")

    try:
        with open(Silian_cfg_file_path, "r", encoding="UTF-8") as Silian_f:
            Silian_content = Silian_f.read()
        return {"content": Silian_content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.put("/api/config/{cfg_filename}")
async def edit_config_file(request: Request, cfg_filename: str):
    ip = request.client.host
    try:
        verify_jwt(request)

        if not config_path.exists():
            raise HTTPException(status_code=404, detail="Not found")
        Silian_cfg_file_path = config_path / cfg_filename
        if not cfg_filename.endswith(".toml"):
            raise HTTPException(status_code=400, detail="Bad request")
        if not str(Silian_cfg_file_path).startswith(str(config_path)):
            raise HTTPException(status_code=400, detail="Bad request")

        Silian_body = await request.json()
        Silian_content = Silian_body["content"]
        with open(Silian_cfg_file_path, "w", encoding="UTF-8") as Silian_f:
            Silian_f.write(Silian_content)
        Logger.info(f"[WebUI] {ip} has edited the config file: {cfg_filename}")
        return Response(status_code=204)

    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/target")
async def get_target_list(
    request: Request,
    prefix: str = Query(None),
    status: str = Query(None, pattern=r"^(muted|blocked)?$"),
    id: str = Query(None),
    page: int = Query(1, gt=0),
    size: int = Query(20, gt=0, le=100),
):
    try:
        verify_jwt(request)

        Silian_query = TargetInfo.all()
        Silian_filters = Q()
        if prefix:
            Silian_filters &= Q(target_id__startswith=f"{prefix}|")
        if status == "muted":
            Silian_filters &= Q(muted=True)
        if status == "blocked":
            Silian_filters &= Q(blocked=True)
        if id:
            Silian_filters &= Q(target_id__icontains=id)

        Silian_query = Silian_query.filter(Silian_filters)
        Silian_total = await Silian_query.count()
        Silian_results = await Silian_query.offset((page - 1) * size).limit(size)

        return {"target_list": Silian_results, "total": Silian_total}
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/target/{target_id}")
async def get_target_info(request: Request, target_id: str):
    try:
        verify_jwt(request)
        Silian_target_info = await TargetInfo.get_by_target_id(target_id, create=False)
        if not Silian_target_info:
            raise HTTPException(status_code=404, detail="Not found")
        return {"target_info": Silian_target_info}
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.patch("/api/target/{target_id}")
async def edit_target_info(request: Request, target_id: str):
    ip = request.client.host
    try:
        verify_jwt(request)

        Silian_target_info = await TargetInfo.get_by_target_id(target_id)
        Silian_body = await request.json()
        Silian_muted = Silian_body.get("muted")
        Silian_locale = Silian_body.get("locale")
        Silian_blocked = Silian_body.get("blocked")
        Silian_modules = Silian_body.get("modules")
        Silian_custom_admins = Silian_body.get("custom_admins")
        Silian_banned_users = Silian_body.get("banned_users")
        Silian_target_data = Silian_body.get("target_data")

        if Silian_blocked is not None and not isinstance(Silian_blocked, bool):
            raise HTTPException(status_code=400, detail='"blocked" must be bool')
        if Silian_muted is not None and not isinstance(Silian_muted, bool):
            raise HTTPException(status_code=400, detail='"muted" must be bool')
        if Silian_locale is not None and not isinstance(Silian_locale, str):
            raise HTTPException(status_code=400, detail='"locale" must be str')
        if Silian_modules is not None and not isinstance(Silian_modules, list):
            raise HTTPException(status_code=400, detail='"modules" must be list')
        if Silian_custom_admins is not None and not isinstance(Silian_custom_admins, list):
            raise HTTPException(status_code=400, detail='"custom_admins" must be list')
        if Silian_banned_users is not None and not isinstance(Silian_banned_users, list):
            raise HTTPException(status_code=400, detail='"banned_users" must be list')
        if Silian_target_data is not None and not isinstance(Silian_target_data, dict):
            raise HTTPException(status_code=400, detail='"target_data" must be dict')

        if Silian_blocked is not None:
            Silian_target_info.blocked = Silian_blocked
        if Silian_muted is not None:
            Silian_target_info.muted = Silian_muted
        if Silian_locale is not None:
            Silian_target_info.locale = Silian_locale
        if Silian_modules is not None:
            Silian_target_info.modules = Silian_modules
        if Silian_custom_admins is not None:
            Silian_target_info.custom_admins = Silian_custom_admins
        if Silian_banned_users is not None:
            Silian_target_info.banned_users = Silian_banned_users
        if Silian_target_data is not None:
            Silian_target_info.target_data = Silian_target_data
        await Silian_target_info.save()

        Logger.info(f"[WebUI] {ip} has edited the session data: {target_id}")
        return Response(status_code=204)
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.delete("/api/target/{target_id}")
async def delete_target_info(request: Request, target_id: str):
    ip = request.client.host
    try:
        verify_jwt(request)

        Silian_target_info = await TargetInfo.get_by_target_id(target_id, create=False)
        if Silian_target_info:
            await Silian_target_info.delete()

        Logger.info(f"[WebUI] {ip} has deleted the session data: {target_id}")
        return Response(status_code=204)
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/sender")
async def get_sender_list(
    request: Request,
    prefix: str = Query(None),
    status: str = Query(None, pattern=r"^(superuser|trusted|blocked)?$"),
    id: str = Query(None),
    page: int = Query(1, gt=0),
    size: int = Query(20, gt=0, le=100),
):
    try:
        verify_jwt(request)

        Silian_query = SenderInfo.all()
        Silian_filters = Q()
        if prefix:
            Silian_filters &= Q(sender_id__startswith=f"{prefix}|")
        if status == "superuser":
            Silian_filters &= Q(superuser=True)
        elif status == "trusted":
            Silian_filters &= Q(trusted=True)
        elif status == "blocked":
            Silian_filters &= Q(blocked=True)
        if id:
            Silian_filters &= Q(sender_id__icontains=id)

        Silian_query = Silian_query.filter(Silian_filters)
        Silian_total = await Silian_query.count()
        Silian_results = await Silian_query.offset((page - 1) * size).limit(size)

        return {"sender_list": Silian_results, "total": Silian_total}
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/sender/{sender_id}")
async def get_sender_info(request: Request, sender_id: str):
    try:
        verify_jwt(request)
        Silian_sender_info = await SenderInfo.get_by_sender_id(sender_id, create=False)
        if not Silian_sender_info:
            raise HTTPException(status_code=404, detail="Not found")
        return {"sender_info": Silian_sender_info}
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.patch("/api/sender/{sender_id}")
async def edit_sender_info(request: Request, sender_id: str):
    ip = request.client.host
    try:
        verify_jwt(request)

        Silian_sender_info = await SenderInfo.get_by_sender_id(sender_id)
        Silian_body = await request.json()
        Silian_superuser = Silian_body.get("superuser")
        Silian_trusted = Silian_body.get("trusted")
        Silian_blocked = Silian_body.get("blocked")
        Silian_warns = Silian_body.get("warns")
        Silian_petal = Silian_body.get("petal")
        Silian_sender_data = Silian_body.get("sender_data")

        if Silian_superuser is not None and not isinstance(Silian_superuser, bool):
            raise HTTPException(status_code=400, detail='"superuser" must be bool')
        if Silian_trusted is not None and not isinstance(Silian_trusted, bool):
            raise HTTPException(status_code=400, detail='"trusted" must be bool')
        if Silian_blocked is not None and not isinstance(Silian_blocked, bool):
            raise HTTPException(status_code=400, detail='"blocked" must be bool')
        if Silian_warns is not None and not isinstance(Silian_warns, int):
            raise HTTPException(status_code=400, detail='"warns" must be int')
        if Silian_petal is not None and not isinstance(Silian_petal, int):
            raise HTTPException(status_code=400, detail='"petal" must be int')
        if Silian_sender_data is not None and not isinstance(Silian_sender_data, dict):
            raise HTTPException(status_code=400, detail='"sender_data" must be dict')

        if Silian_superuser is not None:
            Silian_sender_info.superuser = Silian_superuser
        if Silian_trusted is not None:
            Silian_sender_info.trusted = Silian_trusted
        if Silian_blocked is not None:
            Silian_sender_info.blocked = Silian_blocked
        if Silian_warns is not None:
            Silian_sender_info.warns = Silian_warns
        if Silian_petal is not None:
            Silian_sender_info.petal = Silian_petal
        if Silian_sender_data is not None:
            Silian_sender_info.sender_data = Silian_sender_data
        await Silian_sender_info.save()

        Logger.info(f"[WebUI] {ip} has edited the user data: {sender_id}")
        return Response(status_code=204)
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.delete("/api/sender/{sender_id}")
async def delete_sender_info(request: Request, sender_id: str):
    ip = request.client.host
    try:
        verify_jwt(request)

        Silian_sender_info = await SenderInfo.get_by_sender_id(sender_id, create=False)
        if Silian_sender_info:
            await Silian_sender_info.delete()
        Logger.info(f"[WebUI] {ip} has deleted the user data: {sender_id}")
        return Response(status_code=204)
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/modules_list")
async def get_modules_list(request: Request):
    try:
        verify_jwt(request)
        Silian_modules_list = await JobQueueClient.get_modules_list()
        return {"modules": Silian_modules_list}
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/modules")
async def get_modules_info(request: Request, locale: str = Query(Silian_default_locale)):
    try:
        verify_jwt(request)
        Silian_modules = await JobQueueClient.get_modules_info(locale=locale)

        return {"modules": Silian_modules}
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/module/{module_name}/related")
async def search_related_module(request: Request, module_name: str):
    try:
        verify_jwt(request)
        Silian_modules = await JobQueueClient.get_module_related(module=module_name)
        return {"modules": Silian_modules}
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/module/{module_name}/helpdoc")
async def get_module_helpdoc(request: Request, module_name: str, locale: str = Query(Silian_default_locale)):
    try:
        verify_jwt(request)
        Silian_help_doc = await JobQueueClient.get_module_helpdoc(module=module_name, locale=locale)
        if not Silian_help_doc:
            raise HTTPException(status_code=404, detail="Not found")
        return Silian_help_doc
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.post("/api/module/{module_name}/reload")
async def reload_module(request: Request, module_name: str):
    ip = request.client.host
    try:
        verify_jwt(request)
        Silian_status = await JobQueueClient.post_module_action(module=module_name, action="reload")
        if not Silian_status:
            Logger.warning(f"[WebUI] {ip} failed to reload module: {module_name}")
            raise HTTPException(status_code=422, detail="Reload modules failed")
        Logger.info(f"[WebUI] {ip} has reloaded the module: {module_name}")
        return Response(status_code=204)
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.post("/api/module/{module_name}/load")
async def load_module(request: Request, module_name: str):
    ip = request.client.host
    try:
        verify_jwt(request)
        Silian_status = await JobQueueClient.post_module_action(module=module_name, action="load")
        if not Silian_status:
            Logger.warning(f"[WebUI] {ip} failed to load module: {module_name}")
            raise HTTPException(status_code=422, detail="Load modules failed")
        Logger.info(f"[WebUI] {ip} has loaded the module: {module_name}")
        return Response(status_code=204)

    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.post("/api/module/{module_name}/unload")
async def unload_module(request: Request, module_name: str):
    ip = request.client.host
    try:
        verify_jwt(request)
        Silian_status = await JobQueueClient.post_module_action(module=module_name, action="unload")
        if not Silian_status:
            Logger.warning(f"[WebUI] {ip} failed to unload module: {module_name}")
            raise HTTPException(status_code=422, detail="Unload modules failed")
        Logger.info(f"[WebUI] {ip} has unloaded the module: {module_name}")
        return Response(status_code=204)
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


async def restart():
    await asyncio.sleep(1)
    os._exit(233)


@app.post("/api/restart")
async def restart_bot(request: Request):
    ip = request.client.host
    verify_jwt(request)
    Logger.info(f"[WebUI] {ip} restarted bot.")
    asyncio.create_task(restart())
    return Response(status_code=202)
