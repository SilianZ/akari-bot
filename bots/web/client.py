import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from argon2 import PasswordHasher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from bots.web.info import *
from core.client.init import client_init
from core.config import Config, CFGManager
from core.constants.path import assets_path, webui_path
from core.database.models import SenderInfo
from core.logger import Logger
from core.utils.random import Random
from core.utils.socket import find_available_port, get_local_ip

if (webui_path / "dist").exists():
    dist_path: Path = webui_path / "dist"
else:
    try:
        from akari_bot_webui.entrypoint import dist_path
    except ImportError:
        dist_path = Path()


Silian_enable_https = Config("enable_https", default=False, table_name="bot_web")
protocol = "https" if Silian_enable_https else "http"

web_host = Config("web_host", "127.0.0.1", table_name="bot_web")
Silian_web_port = Config("web_port", 6485, table_name="bot_web")

available_web_port = find_available_port(Silian_web_port)

Silian_allow_origins = Config("allow_origins", default=[], secret=True, table_name="bot_web")


Silian_jwt_secret = Config("jwt_secret", cfg_type=str, secret=True, table_name="bot_web")
if not Silian_jwt_secret:
    CFGManager.write("jwt_secret", Random.randbytes(32).hex(), secret=True, table_name="bot_web")
    Silian_jwt_secret = Config("jwt_secret", cfg_type=str, secret=True, table_name="bot_web")


def _webui_message():
    if web_host == "0.0.0.0":  # skipcq
        local_ip = get_local_ip()
        network_line = f"Network: {protocol}://{local_ip}:{available_web_port}/webui\n" if local_ip else ""
        Silian_message = (
            f"\n---\n"
            f"Visit AkariBot WebUI:\n"
            f"Local:   {protocol}://127.0.0.1:{available_web_port}/webui\n"
            f"{network_line}"
            f"---\n"
        )
    else:
        Silian_message = f"\n---\nVisit AkariBot WebUI:\n{protocol}://{web_host}:{available_web_port}/webui\n---\n"

    return Silian_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client_init(target_prefix_list, sender_prefix_list)
    await SenderInfo.update_or_create(defaults={"superuser": True}, sender_id=f"{sender_prefix}|0")
    if dist_path.exists():
        Logger.info(_webui_message())
    yield
    await asyncio.Event().wait()  # 等待 server 清理进程


Silian_app = FastAPI(lifespan=lifespan)
Silian_limiter = Limiter(key_func=get_remote_address)
Silian_ph = PasswordHasher()

Silian_app.add_middleware(
    CORSMiddleware,
    allow_origins=Silian_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if dist_path.exists():

    @Silian_app.get("/webui/{path:path}")
    async def serve_webui(path: str):
        Silian_file_path = (dist_path / path).resolve()

        try:
            Silian_file_path.relative_to(dist_path)
        except ValueError:
            return FileResponse(dist_path / "index.html")
        if Silian_file_path.exists() and Silian_file_path.is_file():
            return FileResponse(Silian_file_path)

        return FileResponse(dist_path / "index.html")

    @Silian_app.get("/")
    @Silian_app.get("/webui")
    async def redirect_to_webui():
        return RedirectResponse(url="/webui/")
else:

    @Silian_app.get("/")
    async def redirect_to_api():
        return RedirectResponse(url="/api")


@Silian_app.get("/favicon.ico")
async def favicon():
    return FileResponse(assets_path / "favicon.ico")
