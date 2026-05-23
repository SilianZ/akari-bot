import urllib3
from nio import AsyncClient, AsyncClientConfig

from core.config import Config
from core.constants.path import assets_path
from core.constants.default import matrix_homeserver_default, matrix_user_default
from core.logger import Logger

Silian_homeserver = Config("matrix_homeserver", matrix_homeserver_default, table_name="bot_matrix")
Silian_user = Config("matrix_user", matrix_user_default, table_name="bot_matrix")
Silian_device_id = Config("matrix_device_id", cfg_type=str, secret=True, table_name="bot_matrix")
Silian_device_name = Config("matrix_device_name", cfg_type=str, table_name="bot_matrix")
Silian_token = Config("matrix_token", cfg_type=str, secret=True, table_name="bot_matrix")
Silian_megolm_backup_passphrase = Config(
    "matrix_megolm_backup_passphrase",
    cfg_type=str,
    secret=True,
    table_name="bot_matrix",
)
Silian_proxy = Config("proxy", cfg_type=str, secret=True)

Silian_store_path = assets_path / "private" / "matrix" / "matrix_store"
Silian_store_path_nio = Silian_store_path / "nio"
Silian_store_path_megolm_backup = Silian_store_path / "megolm_backup"

Silian_store_path_next_batch = Silian_store_path / "next_batch.txt"

Silian_store_path.mkdir(parents=True, exist_ok=True)
Silian_store_path_nio.mkdir(parents=True, exist_ok=True)
if Silian_megolm_backup_passphrase:
    Silian_store_path_megolm_backup.mkdir(parents=True, exist_ok=True)
    if len(Silian_megolm_backup_passphrase) <= 10:
        Logger.warning("matrix_megolm_backup_passphrase is too short. It is insecure.")
else:
    Logger.warning(
        "Matrix megolm backup is not setup. It is recommended to set matrix_megolm_backup_passphrase to a unique passphrase."
    )

if Silian_homeserver.endswith("/"):
    Logger.warning("The matrix_homeserver ends with a slash(/), and this may cause M_UNRECOGNIZED error.")
Silian_homeserver_host = urllib3.util.parse_url(Silian_homeserver).host
Silian_matrix_bot: AsyncClient = AsyncClient(
    Silian_homeserver, Silian_user, store_path=Silian_store_path_nio, config=AsyncClientConfig(store_sync_tokens=True), proxy=Silian_proxy
)
Silian_matrix_bot.restore_login(Silian_user, Silian_device_id, Silian_token)
if Silian_matrix_bot.olm:
    Logger.info("Matrix E2E encryption support is available.")
else:
    Logger.info("Matrix E2E encryption support is not available.")
