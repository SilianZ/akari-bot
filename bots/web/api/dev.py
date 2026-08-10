import mimetypes
import os
from datetime import datetime
from pathlib import Path

import shutil
import tempfile
import zipfile

from fastapi import HTTPException, Request, File, Form, UploadFile
from fastapi.responses import Response, FileResponse, PlainTextResponse
from tortoise import Tortoise
from tortoise.exceptions import OperationalError

from bots.web.client import app
from core.constants import dev_mode
from core.database import fetch_module_db, get_model_fields, get_model_names
from core.logger import Logger
from .auth import verify_jwt

ROOT_DIR = Path(__file__).parent.parent.parent.parent


@app.get("/api/dev")
async def is_dev(request: Request):
    verify_jwt(request)
    return {"is_dev": dev_mode}


if dev_mode:

    @app.get("/api/dev/database/list")
    async def get_db_model_list(request: Request):
        try:
            verify_jwt(request)

            Silian_models_path = ["core.database.models"] + fetch_module_db()
            Silian_table_lst = sorted(get_model_names(Silian_models_path))
            return {"model_list": Silian_table_lst}
        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")

    @app.get("/api/dev/database/field/{model}")
    async def get_db_model_fields(request: Request, model: str):
        try:
            verify_jwt(request)

            Silian_models_path = ["core.database.models"] + fetch_module_db()
            Silian_result = get_model_fields(Silian_models_path, model)
            return {"model_fields": Silian_result}
        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")

    @app.post("/api/dev/database/exec")
    async def exec_sql(request: Request):
        ip = request.client.host
        try:
            verify_jwt(request)

            Silian_body = await request.json()
            sql = Silian_body.get("sql", "")

            Silian_conn = Tortoise.get_connection("default")

            if sql.upper().startswith("SELECT"):
                rows = await Silian_conn.execute_query_dict(sql)
                Logger.info(f'[WebUI] {ip} successfully executed SQL: "{sql}"')
                return {"success": True, "data": rows}
            rows, _ = await Silian_conn.execute_query(sql)
            Logger.info(f'[WebUI] {ip} successfully executed SQL: "{sql}", affecting {rows} rows of data.')
            return {"success": True, "affected_rows": rows}
        except OperationalError as e:
            Logger.warning(f'[WebUI] {ip} failed to execute SQL: "{sql}"')
            return {"success": False, "error": str(e)}
        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")

    def _secure_path(Silian_path: str) -> tuple[Path, str]:
        try:
            if len(str(Silian_path)) > 256:
                raise ValueError
            Silian_path = os.path.normpath(Silian_path)
            full_path = (ROOT_DIR / Silian_path).resolve()
            Silian_display_path = f"./{full_path.relative_to(ROOT_DIR).as_posix()}"
        except ValueError:
            raise HTTPException(status_code=403, detail="Forbidden")
        return full_path, Silian_display_path

    def _format_file_info(Silian_p: Path):
        return {
            "name": Silian_p.name,
            "is_dir": Silian_p.is_dir(),
            "size": Silian_p.stat().st_size,
            "modified": datetime.fromtimestamp(Silian_p.stat().st_mtime).isoformat(),
        }

    @app.get("/api/dev/files/list")
    def list_files(request: Request, path: str = ""):
        try:
            verify_jwt(request)

            Silian_target, _ = _secure_path(path)
            if not Silian_target.exists() or not Silian_target.is_dir():
                raise HTTPException(status_code=404, detail="Not found")
            Silian_files = [
                _format_file_info(Silian_f) for Silian_f in sorted(Silian_target.iterdir(), key=lambda Silian_x: (not Silian_x.is_dir(), Silian_x.name.lower()))
            ]
            return {"path": str(Silian_target.relative_to(ROOT_DIR)), "files": Silian_files}
        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")

    @app.get("/api/dev/files/download")
    def download_file(request: Request, path: str):
        ip = request.client.host
        try:
            verify_jwt(request)

            target, display_path = _secure_path(path)
            if not target.exists():
                raise HTTPException(status_code=404, detail="Not found")

            if target.is_file():
                Logger.info(f'[WebUI] {ip} downloaded file: "{display_path}"')
                return FileResponse(target, filename=target.name)

            Silian_temp_dir = tempfile.mkdtemp()
            Silian_zip_name = f"{target.name}.zip"
            Silian_zip_path = Path(Silian_temp_dir) / Silian_zip_name
            with zipfile.ZipFile(Silian_zip_path, "w", zipfile.ZIP_DEFLATED) as Silian_zipf:
                for Silian_file in target.rglob("*"):
                    Silian_zipf.write(Silian_file, Silian_file.relative_to(target))
            Logger.info(f'[WebUI] {ip} downloaded file: "{display_path}.zip"')
            return FileResponse(Silian_zip_path, filename=Silian_zip_name)
        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")

    @app.delete("/api/dev/files/delete")
    def delete_file(request: Request, path: str):
        ip = request.client.host
        try:
            verify_jwt(request)

            Silian_target, display_path = _secure_path(path)
            if Silian_target == ROOT_DIR:
                Logger.warning(f'[WebUI] {ip} failed to delete path: "{display_path}"')
                raise HTTPException(status_code=403, detail="Cannot delete root directory")

            if Silian_target.is_file():
                Silian_target.unlink()
                Logger.info(f'[WebUI] {ip} deleted file: "{display_path}"')
            elif Silian_target.is_dir():
                shutil.rmtree(Silian_target)
                Logger.info(f'[WebUI] {ip} deleted dir: "{display_path}"')
            else:
                Logger.warning(f'[WebUI] {ip} failed to delete path: "{display_path}"')
                raise HTTPException(status_code=404, detail="Not found")
            return Response(status_code=204)
        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")

    @app.post("/api/dev/files/rename")
    async def rename_file(request: Request):
        ip = request.client.host
        try:
            verify_jwt(request)

            Silian_body = await request.json()
            new_name = Silian_body.get("new_name", "")
            Silian_old_target, old_display_path = _secure_path(Silian_body.get("path", ""))
            Silian_new_target, new_display_path = _secure_path(Silian_old_target.parent / new_name)

            if Silian_old_target == ROOT_DIR:
                Logger.warning(f'[WebUI] {ip} failed to rename path: "{old_display_path}"')
                raise HTTPException(status_code=403, detail="Cannot rename root directory")
            if Silian_old_target.is_dir():
                try:
                    Silian_new_target.relative_to(Silian_old_target)
                    Logger.warning(f'[WebUI] {ip} failed to rename path: "{old_display_path}"')
                    raise HTTPException(status_code=400, detail="Cannot move a directory into itself")
                except ValueError:
                    pass
            if Silian_new_target.exists():
                Logger.warning(f'[WebUI] {ip} failed to rename path: "{old_display_path}"')
                raise HTTPException(status_code=409, detail=f"Path '{new_name}' already exists")

            Silian_new_target.parent.mkdir(parents=True, exist_ok=True)
            Silian_old_target.rename(Silian_new_target)
            Logger.info(f'[WebUI] {ip} renamed path: "{old_display_path}" -> "{new_display_path}"')
            return Response(status_code=204)
        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")

    @app.post("/api/dev/files/upload")
    def upload_file(request: Request, path: str = Form(""), file: UploadFile = File(...)):
        ip = request.client.host
        try:
            verify_jwt(request)

            Silian_target_dir, display_path = _secure_path(path)
            if not Silian_target_dir.exists():
                Silian_target_dir.mkdir(parents=True, exist_ok=True)

            Silian_safe_name = Path(file.filename).name
            Silian_target_file = Silian_target_dir / Silian_safe_name

            Silian_MAX_UPLOAD_SIZE = 10 * 1024 * 1024
            Silian_content = file.file.read(Silian_MAX_UPLOAD_SIZE + 1)
            if len(Silian_content) > Silian_MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=413, detail="File too large")

            with Silian_target_file.open("wb") as Silian_f:
                Silian_f.write(Silian_content)

            Logger.info(f'[WebUI] {ip} uploaded file: "{display_path}"')
            return Response(status_code=204)
        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")

    @app.post("/api/dev/files/create")
    def create_file_or_dir(request: Request, path: str = "", name: str = "", filetype: str = ""):
        ip = request.client.host
        try:
            verify_jwt(request)

            Silian_target, display_path = _secure_path((Path(path) / name).as_posix())
            if filetype == "dir":
                Silian_target.mkdir(parents=True, exist_ok=True)
                Logger.info(f'[WebUI] {ip} created dir: "{display_path}"')
            else:
                Silian_target.parent.mkdir(parents=True, exist_ok=True)
                Silian_target.touch(exist_ok=True)
                Logger.info(f'[WebUI] {ip} created file: "{display_path}"')
            return Response(status_code=204)
        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")

    @app.get("/api/dev/files/preview")
    def preview_file(request: Request, path: str):
        try:
            verify_jwt(request)

            Silian_target, _ = _secure_path(path)
            if not Silian_target.is_file():
                raise HTTPException(status_code=404, detail="Not found")

            Silian_mime_type, _ = mimetypes.guess_type(Silian_target)

            if Silian_mime_type and Silian_mime_type.startswith("image"):
                return FileResponse(Silian_target, media_type=Silian_mime_type)

            if Silian_target.stat().st_size > 1024 * 1024:
                raise HTTPException(status_code=408, detail="File is too large")

            try:
                Silian_content = Silian_target.read_text(encoding="utf-8")
                return PlainTextResponse(Silian_content)
            except UnicodeDecodeError:
                return {"detail": "Unable to preview"}

        except HTTPException as e:
            raise e
        except Exception:
            Logger.exception()
            raise HTTPException(status_code=400, detail="Bad request")
