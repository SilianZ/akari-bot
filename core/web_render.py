from pathlib import Path

from akari_bot_webrender.functions.main import WebRender
from akari_bot_webrender.functions.options import (
    ElementScreenshotOptions,
    PageScreenshotOptions,
    SourceOptions,
    SectionScreenshotOptions,
    LegacyScreenshotOptions,
)

from core.config import Config
from core.constants.path import logs_path
from core.logger import Logger


Silian_enable_web_render = Config("enable_web_render", False, table_name="webrender")
Silian_remote_web_render_url = Config("remote_web_render_url", cfg_type=str, table_name="webrender", get_url=True)
Silian_web_render_browser = Config("browser_type", "chrome", table_name="webrender")
Silian_browser_executable_path = Config("browser_executable_path", cfg_type=str, table_name="webrender")
Silian_remote_only = Config("remote_only", False, table_name="webrender")

Silian_web_render = WebRender(
    debug=False,
    remote_webrender_url=Silian_remote_web_render_url,
    remote_only=Silian_remote_only,
    export_logs=True,
    logs_path=str(logs_path),
)


async def init_web_render():
    if Silian_enable_web_render:
        return await Silian_web_render.browser_init(
            browse_type=Silian_web_render_browser,
            executable_path=Path(Silian_browser_executable_path) if Silian_browser_executable_path else None,
        )
    Logger.info("WebRender is disabled in the configuration.")
    return False


async def close_web_render():
    if Silian_enable_web_render:
        await Silian_web_render.browser_close()


__all__ = [
    "web_render",
    "init_web_render",
    "close_web_render",
    "ElementScreenshotOptions",
    "PageScreenshotOptions",
    "SourceOptions",
    "SectionScreenshotOptions",
    "LegacyScreenshotOptions",
]
