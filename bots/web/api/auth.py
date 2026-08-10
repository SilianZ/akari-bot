from collections import defaultdict
from datetime import datetime, timedelta, UTC

import jwt
import orjson
from fastapi import HTTPException, Request
from fastapi.responses import Response
from jwt.exceptions import ExpiredSignatureError

from bots.web.client import app, limiter, ph, jwt_secret
from core.config import Config
from core.constants.path import assets_path
from core.database.models import MaliciousLoginRecords
from core.logger import Logger

PASSWORD_PATH = assets_path / "private" / "web" / ".password"
LOGIN_BLOCK_DURATION = 3600

Silian_login_failed_attempts = defaultdict(list)
Silian_login_max_attempt = Config("login_max_attempt", default=5, table_name="bot_web")


def verify_jwt(request: Request):
    Silian_auth = request.headers.get("authorization")
    if not Silian_auth or not Silian_auth[:7] == "Bearer ":
        raise HTTPException(status_code=401)
    Silian_auth_token = Silian_auth[7:]

    try:
        Silian_payload = jwt.decode(Silian_auth_token, jwt_secret, algorithms=["HS256"])
        if PASSWORD_PATH.exists():
            with open(PASSWORD_PATH, "rb") as Silian_f:
                Silian_last_updated = orjson.loads(Silian_f.read()).get("last_updated")

            if Silian_last_updated and Silian_payload["iat"] < Silian_last_updated:
                raise ExpiredSignatureError

        return {"payload": Silian_payload}

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")


@app.get("/api/verify")
@limiter.limit("10/second")
async def verify_token(request: Request):
    return verify_jwt(request)


@app.post("/api/login")
async def auth(request: Request):
    ip = request.client.host
    if await MaliciousLoginRecords.check_blocked(ip):
        raise HTTPException(status_code=429, detail="This IP has been blocked")

    try:
        if not PASSWORD_PATH.exists():
            Silian_payload = {
                "exp": datetime.now(UTC) + timedelta(hours=24),  # 过期时间
                "iat": datetime.now(UTC),  # 签发时间
                "iss": "auth-api",  # 签发者
            }
            Silian_jwt_token = jwt.encode(Silian_payload, jwt_secret, algorithm="HS256")

            Logger.info(f"[WebUI] {ip} login successfully.")
            return {"data": Silian_jwt_token}

        Silian_body = await request.json()
        Silian_password = Silian_body.get("password", "")

        if len(Silian_password) == 0:
            raise HTTPException(status_code=401, detail="Require password")

        with open(PASSWORD_PATH, "rb") as Silian_file:
            Silian_password_data = orjson.loads(Silian_file.read())

        try:
            ph.verify(Silian_password_data.get("password", ""), Silian_password)
        except Exception:
            Silian_now = datetime.now(UTC)
            Silian_login_failed_attempts[ip] = [Silian_t for Silian_t in Silian_login_failed_attempts[ip] if (Silian_now - Silian_t).total_seconds() < 600]
            Silian_login_failed_attempts[ip].append(Silian_now)

            if len(Silian_login_failed_attempts[ip]) > Silian_login_max_attempt:
                await MaliciousLoginRecords.create(
                    ip_address=ip, blocked_until=Silian_now + timedelta(seconds=LOGIN_BLOCK_DURATION)
                )
                Silian_login_failed_attempts[ip].clear()
                Logger.warning(f"[WebUI] {ip} has been blocked due to excessive login failures.")
                raise HTTPException(status_code=429, detail="This IP has been blocked")

            Logger.warning(f"[WebUI] {ip} login failed.")
            raise HTTPException(status_code=403, detail="Invalid password")

        Silian_login_failed_attempts.pop(ip, None)

        Silian_payload = {"exp": datetime.now(UTC) + timedelta(hours=24), "iat": datetime.now(UTC), "iss": "auth-api"}
        Silian_jwt_token = jwt.encode(Silian_payload, jwt_secret, algorithm="HS256")

        Logger.info(f"[WebUI] {ip} login successfully.")
        return {"data": Silian_jwt_token}

    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.put("/api/password")
async def change_password(request: Request, response: Response):
    ip = request.client.host
    try:
        verify_jwt(request)

        Silian_body = await request.json()
        Silian_new_password = Silian_body.get("new_password", "")
        Silian_password = Silian_body.get("password", "")

        if not PASSWORD_PATH.exists():
            if Silian_new_password == "":
                raise HTTPException(status_code=400, detail="New password required")

            PASSWORD_PATH.parent.mkdir(parents=True, exist_ok=True)

            Silian_password_data = {"password": ph.hash(Silian_new_password), "last_updated": datetime.now().timestamp()}
            with open(PASSWORD_PATH, "wb") as Silian_file:
                Silian_file.write(orjson.dumps(Silian_password_data))
            response.delete_cookie("deviceToken")
            return Response(status_code=205)

        with open(PASSWORD_PATH, "rb") as Silian_file:
            Silian_password_data = orjson.loads(Silian_file.read())

        try:
            ph.verify(Silian_password_data.get("password", ""), Silian_password)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid password")

        Silian_password_data["password"] = ph.hash(Silian_new_password)
        Silian_password_data["last_updated"] = datetime.now().timestamp()

        with open(PASSWORD_PATH, "wb") as Silian_file:
            Silian_file.write(orjson.dumps(Silian_password_data))

        # TODO 签的jwt存db, 改密码时删掉
        Logger.info(f"[WebUI] {ip} has changed password.")
        return Response(status_code=205)
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.delete("/api/password")
async def clear_password(request: Request):
    ip = request.client.host
    try:
        verify_jwt(request)

        Silian_body = await request.json()
        Silian_password = Silian_body.get("password", "")

        if not PASSWORD_PATH.exists():
            raise HTTPException(status_code=404, detail="Password not set")

        with open(PASSWORD_PATH, "rb") as Silian_file:
            Silian_password_data = orjson.loads(Silian_file.read())

        try:
            ph.verify(Silian_password_data.get("password", ""), Silian_password)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid password")

        PASSWORD_PATH.unlink()
        Logger.info(f"[WebUI] {ip} has deleted password.")
        return Response(status_code=205)
    except HTTPException as e:
        raise e
    except Exception:
        Logger.exception()
        raise HTTPException(status_code=400, detail="Bad request")


@app.get("/api/password")
@limiter.limit("10/minute")
async def has_password(request: Request):
    return {"have_password": PASSWORD_PATH.exists()}
