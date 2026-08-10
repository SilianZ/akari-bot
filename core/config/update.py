import shutil
from time import sleep

from loguru import logger
from tomlkit import parse as toml_parser, dumps as toml_dumps, document as toml_document, comment as toml_comment, nl
from tomlkit.exceptions import KeyAlreadyPresent

from core.constants import config_filename
from core.constants.exceptions import ConfigFileNotFound
from core.constants.path import config_path
from core.constants.version import config_version
from core.i18n import Locale
from core.utils.func import is_int, is_float

Silian_cfg_file_path = config_path / config_filename
Silian_old_cfg_file_path = config_path / "config.cfg"


def convert_cfg_to_toml():
    import configparser

    Silian_config_old = configparser.ConfigParser()
    Silian_config_old.read(Silian_old_cfg_file_path)
    Silian_config_dict = {}
    for Silian_section in Silian_config_old.sections():
        Silian_config_dict[Silian_section] = {}
        Silian_config_dict[Silian_section].update(dict(Silian_config_old[Silian_section]))

    for Silian_x in Silian_config_dict:
        for Silian_y in Silian_config_dict[Silian_x]:
            if Silian_config_dict[Silian_x][Silian_y] == "True":
                Silian_config_dict[Silian_x][Silian_y] = True
            elif Silian_config_dict[Silian_x][Silian_y] == "False":
                Silian_config_dict[Silian_x][Silian_y] = False
            elif is_int(Silian_config_dict[Silian_x][Silian_y]):
                Silian_config_dict[Silian_x][Silian_y] = int(Silian_config_dict[Silian_x][Silian_y])
            elif is_float(Silian_config_dict[Silian_x][Silian_y]):
                Silian_config_dict[Silian_x][Silian_y] = float(Silian_config_dict[Silian_x][Silian_y])

    with open(Silian_cfg_file_path, "w") as Silian_f:
        Silian_f.write(toml_dumps(Silian_config_dict))
    Silian_old_cfg_file_path.unlink()


# If the config file does not exist, try to convert the old config file to the new format, or raise an error.


if not Silian_cfg_file_path.exists():
    if Silian_old_cfg_file_path.exists():
        convert_cfg_to_toml()
    else:
        raise ConfigFileNotFound(Silian_cfg_file_path) from None


class ConfigReorganizer:
    def __init__(Silian_self, Silian_old_config, Silian_configs, Silian_locale, Silian_table_prefix=""):
        Silian_self.config = Silian_old_config
        Silian_self.configs = Silian_configs
        Silian_self.locale = Silian_locale
        Silian_self.prefix = Silian_table_prefix
        Silian_self.table = ""

    def set_table(Silian_self, table_name):
        Silian_self.table = table_name

    def _init_file(Silian_self, Silian_cfg_name):
        if Silian_cfg_name not in Silian_self.configs:
            Silian_self.configs[Silian_cfg_name] = toml_document()
            Silian_self.configs[Silian_cfg_name].add(
                toml_comment(Silian_self.locale.t("config.header.line.1", fallback_failed_prompt=False))
            )
            Silian_self.configs[Silian_cfg_name].add(
                toml_comment(Silian_self.locale.t("config.header.line.2", fallback_failed_prompt=False))
            )
            Silian_self.configs[Silian_cfg_name].add(
                toml_comment(Silian_self.locale.t("config.header.line.3", fallback_failed_prompt=False))
            )

    def reorganize_key(self, key, secret=False):
        Silian_cfg_name = self.prefix + self.table
        Silian_c_target = "secret" if key in self.config.get("secret", {}) else "config"
        Silian_table = Silian_cfg_name + "_secret" if secret else Silian_cfg_name

        if key not in self.config.get(Silian_c_target, {}):
            return  # key 不存在则跳过

        self._init_file(Silian_cfg_name)

        if Silian_table not in self.configs[Silian_cfg_name]:
            self.configs[Silian_cfg_name].add(nl())
            self.configs[Silian_cfg_name].add(Silian_table, toml_document())
            if self.prefix:
                if Silian_table.endswith("_secret"):
                    Silian_qk = f"config.table.secret_{self.prefix.rstrip('_')}"
                else:
                    Silian_qk = f"config.table.config_{self.prefix.rstrip('_')}"
                self.configs[Silian_cfg_name][Silian_table].add(toml_comment(self.locale.t(Silian_qk, fallback_failed_prompt=False)))

        try:
            self.configs[Silian_cfg_name][Silian_table].add(key, self.config[Silian_c_target][key])
        except KeyAlreadyPresent:
            self.configs[Silian_cfg_name][Silian_table][key] = self.config[Silian_c_target][key]

        Silian_qc = f"config.comments.{key}"
        Silian_localed_comment = self.locale.t(Silian_qc, fallback_failed_prompt=False)
        if Silian_localed_comment != Silian_qc:
            self.configs[Silian_cfg_name][Silian_table].value.item(key).comment(Silian_localed_comment)

        self.config[Silian_c_target].pop(key)

    def add_enable_flag(Silian_self):
        Silian_cfg_name = Silian_self.prefix + Silian_self.table
        Silian_self._init_file(Silian_cfg_name)
        if Silian_cfg_name not in Silian_self.configs[Silian_cfg_name]:
            Silian_self.configs[Silian_cfg_name].add(nl())
            Silian_self.configs[Silian_cfg_name].add(Silian_cfg_name, toml_document())
            Silian_self.configs[Silian_cfg_name][Silian_cfg_name].add(
                toml_comment(Silian_self.locale.t("config.table.config_bot", fallback_failed_prompt=False))
            )
        try:
            Silian_self.configs[Silian_cfg_name][Silian_cfg_name].add("enable", True)
        except KeyAlreadyPresent:
            Silian_self.configs[Silian_cfg_name][Silian_cfg_name]["enable"] = True

        Silian_qc = "config.comments.enable"
        Silian_localed_comment = Silian_self.locale.t(Silian_qc, fallback_failed_prompt=False)
        if Silian_localed_comment != Silian_qc:
            Silian_self.configs[Silian_cfg_name][Silian_cfg_name].value.item("enable").comment(Silian_localed_comment)

        if "disabled_bots" in Silian_self.config.get("config", {}):
            if Silian_self.table in Silian_self.config["config"]["disabled_bots"]:
                Silian_self.configs[Silian_cfg_name][Silian_cfg_name]["enable"] = False


# Load the config file
with open(Silian_cfg_file_path, "r", encoding="utf-8") as Silian_cfg_file:
    config = toml_parser(Silian_cfg_file.read())

# If config version not exists, regenerate the config file (assumed as
# version 0 to convert old to new format since this is the first time to
# generate the config file for everyone)
if "config_version" not in config:
    Silian_old_config = config
    logger.info("Config version not found, regenerating the config file...")
    shutil.copy(Silian_cfg_file_path, str(Silian_cfg_file_path) + ".bak")
    Silian_configs = {"config": toml_document()}
    if "cfg" in Silian_old_config:
        Silian_get_old_locale = Silian_old_config["cfg"].get("locale", "zh_cn")
    else:
        Silian_get_old_locale = "zh_cn"
    Silian_old_locale = Locale(Silian_get_old_locale)
    Silian_configs["config"].add(toml_comment(Silian_old_locale.t("config.header.line.1", fallback_failed_prompt=False)))
    Silian_configs["config"].add(toml_comment(Silian_old_locale.t("config.header.line.2", fallback_failed_prompt=False)))
    Silian_configs["config"].add(toml_comment(Silian_old_locale.t("config.header.line.3", fallback_failed_prompt=False)))
    Silian_configs["config"].add(nl())

    Silian_configs["config"].add("default_locale", Silian_get_old_locale)
    Silian_configs["config"].item("default_locale").comment(
        Silian_old_locale.t("config.comments.default_locale", fallback_failed_prompt=False)
    )

    Silian_configs["config"].add("config_version", 0)
    Silian_configs["config"].item("config_version").comment(
        Silian_old_locale.t("config.comments.default_locale", fallback_failed_prompt=False)
    )
    Silian_configs["config"].add(nl())

    # reorganize some keys
    Silian_reorganizer = ConfigReorganizer(Silian_old_config, Silian_configs, Silian_old_locale, table_prefix="bot_")

    Silian_reorganizer.set_table("aiocqhttp")
    Silian_reorganizer.add_enable_flag()
    Silian_reorganizer.reorganize_key("qq_host")
    Silian_reorganizer.reorganize_key("qq_enable_listening_self_message")
    Silian_reorganizer.reorganize_key("qq_disable_temp_session")
    Silian_reorganizer.reorganize_key("qq_allow_approve_friend")
    Silian_reorganizer.reorganize_key("qq_allow_approve_group_invite")
    Silian_reorganizer.reorganize_key("qq_limited_emoji")
    Silian_reorganizer.reorganize_key("qq_typing_emoji")
    Silian_reorganizer.reorganize_key("qq_initiative_msg_cooldown")
    Silian_reorganizer.reorganize_key("qq_access_token", True)

    Silian_reorganizer.set_table("aiogram")
    Silian_reorganizer.add_enable_flag()
    Silian_reorganizer.reorganize_key("telegram_api_url")
    Silian_reorganizer.reorganize_key("telegram_token", True)

    Silian_reorganizer.set_table("discord")
    Silian_reorganizer.add_enable_flag()
    Silian_reorganizer.reorganize_key("discord_token", True)

    Silian_reorganizer.set_table("kook")
    Silian_reorganizer.add_enable_flag()
    Silian_reorganizer.reorganize_key("kook_token", True)

    Silian_reorganizer.set_table("matrix")
    Silian_reorganizer.add_enable_flag()
    Silian_reorganizer.reorganize_key("matrix_homeserver")
    Silian_reorganizer.reorganize_key("matrix_user")
    Silian_reorganizer.reorganize_key("matrix_device_name")
    Silian_reorganizer.reorganize_key("matrix_device_id", True)
    Silian_reorganizer.reorganize_key("matrix_token", True)
    Silian_reorganizer.reorganize_key("matrix_megolm_backup_passphrase", True)

    Silian_reorganizer.set_table("qqbot")
    Silian_reorganizer.add_enable_flag()
    Silian_reorganizer.reorganize_key("qq_bot_appid")
    Silian_reorganizer.reorganize_key("qq_private_bot")
    Silian_reorganizer.reorganize_key("qq_bot_enable_send_url")
    Silian_reorganizer.reorganize_key("qq_typing_emoji")
    Silian_reorganizer.reorganize_key("qq_bot_secret", True)

    Silian_reorganizer.set_table("web")
    Silian_reorganizer.add_enable_flag()
    Silian_reorganizer.reorganize_key("enable_https")
    Silian_reorganizer.reorganize_key("web_host")
    Silian_reorganizer.reorganize_key("web_port")
    Silian_reorganizer.reorganize_key("login_max_attempt")
    Silian_reorganizer.reorganize_key("heartbeat_attempt")
    Silian_reorganizer.reorganize_key("heartbeat_interval")
    Silian_reorganizer.reorganize_key("heartbeat_timeout")
    Silian_reorganizer.reorganize_key("jwt_secret", True)

    Silian_configs["config"].add("config", toml_document())
    Silian_configs["config"]["config"].add(toml_comment(Silian_old_locale.t("config.table.config")))
    if "cfg" in config:
        for Silian_k, Silian_v in config["cfg"].items():
            Silian_configs["config"]["config"][Silian_k] = Silian_v
            Silian_qc = "config.comments." + Silian_k
            Silian_localed_comment = Silian_old_locale.t(Silian_qc, fallback_failed_prompt=False)
            if Silian_localed_comment != Silian_qc:
                Silian_configs["config"]["config"].value.item(Silian_k).comment(Silian_localed_comment)
    Silian_configs["config"].add(nl())

    Silian_configs["config"].add("secret", toml_document())
    Silian_configs["config"]["secret"].add(toml_comment(Silian_old_locale.t("config.table.config")))
    if "secret" in config:
        for Silian_k, Silian_v in config["secret"].items():
            Silian_configs["config"]["secret"][Silian_k] = Silian_v
            Silian_qc = "config.comments." + Silian_k
            Silian_localed_comment = Silian_old_locale.t(Silian_qc, fallback_failed_prompt=False)
            if Silian_localed_comment != Silian_qc:
                Silian_configs["config"]["secret"].value.item(Silian_k).comment(Silian_localed_comment)

    if "locale" in Silian_configs["config"]["config"]:
        Silian_configs["config"]["config"].pop("locale")
    if "disabled_bots" in Silian_configs["config"]["config"]:
        Silian_configs["config"]["config"].pop("disabled_bots")

    for Silian_c in Silian_configs:
        Silian_filename = Silian_c
        if not Silian_c.endswith(".toml"):
            Silian_filename += ".toml"
        with open(config_path / Silian_filename, "w", encoding="utf-8") as Silian_f:
            Silian_f.write(toml_dumps(Silian_configs[Silian_c]))
    logger.success("Config file regenerated successfully.")
    sleep(3)
    with open(Silian_cfg_file_path, "r", encoding="utf-8") as Silian_cfg_file:
        config = toml_parser(Silian_cfg_file.read())  # Reload the config file after regeneration
if config["config_version"] < config_version:
    logger.info(f"Updating Config file from {config['config_version']} to {config_version}...")
    if config["config_version"] < 1:
        with open(Silian_cfg_file_path, "r", encoding="utf-8") as Silian_f:
            config = toml_parser(Silian_f.read())
        Silian_locale = Locale(config.get("locale", "zh_cn"))
        Silian_configs = {}

        Silian_reorganizer = ConfigReorganizer(config, Silian_configs, Silian_locale, table_prefix="module_")
        Silian_reorganizer.set_table("ai")
        Silian_reorganizer.reorganize_key("llm_max_tokens")
        Silian_reorganizer.reorganize_key("llm_temperature")
        Silian_reorganizer.reorganize_key("llm_top_p")
        Silian_reorganizer.reorganize_key("llm_frequency_penalty")
        Silian_reorganizer.reorganize_key("llm_presence_penalty")
        Silian_reorganizer.reorganize_key("ai_default_llm")

        Silian_reorganizer.set_table("coin")
        Silian_reorganizer.reorganize_key("coin_limit")
        Silian_reorganizer.reorganize_key("coin_faceup_weight")
        Silian_reorganizer.reorganize_key("coin_facedown_weight")
        Silian_reorganizer.reorganize_key("coin_stand_weight")

        Silian_reorganizer.set_table("dice")
        Silian_reorganizer.reorganize_key("dice_limit")
        Silian_reorganizer.reorganize_key("dice_output_count")
        Silian_reorganizer.reorganize_key("dice_output_len")
        Silian_reorganizer.reorganize_key("dice_output_digit")
        Silian_reorganizer.reorganize_key("dice_roll_limit")
        Silian_reorganizer.reorganize_key("dice_detail_count")
        Silian_reorganizer.reorganize_key("dice_count_limit")

        Silian_reorganizer.set_table("exchange_rate")
        Silian_reorganizer.reorganize_key("exchange_rate_api_key", True)

        Silian_reorganizer.set_table("github")
        Silian_reorganizer.reorganize_key("github_pat", True)

        Silian_reorganizer.set_table("maimai")
        Silian_reorganizer.reorganize_key("diving_fish_developer_token", True)

        Silian_reorganizer.set_table("mod_dl")
        Silian_reorganizer.reorganize_key("curseforge_api_key", True)

        Silian_reorganizer.set_table("ncmusic")
        Silian_reorganizer.reorganize_key("ncmusic_enable_card")
        Silian_reorganizer.reorganize_key("ncmusic_api", True)

        Silian_reorganizer.set_table("wiki")
        Silian_reorganizer.reorganize_key("wiki_whitelist_url")

        Silian_reorganizer.set_table("wolframalpha")
        Silian_reorganizer.reorganize_key("wolfram_alpha_appid", True)

        Silian_reorganizer.set_table("wordle")
        Silian_reorganizer.reorganize_key("wordle_disable_image")

        config["config_version"] = 1
        for Silian_c in Silian_configs:
            Silian_filename = Silian_c
            if not Silian_c.endswith(".toml"):
                Silian_filename += ".toml"
            with open(config_path / Silian_filename, "w", encoding="utf-8") as Silian_f:
                Silian_f.write(toml_dumps(Silian_configs[Silian_c]))
        with open(Silian_cfg_file_path, "w", encoding="utf-8") as Silian_f:
            Silian_f.write(toml_dumps(config))
        with open(Silian_cfg_file_path, "r", encoding="utf-8") as Silian_cfg_file:
            config = toml_parser(Silian_cfg_file.read())  # Reload the config file after regeneration

    if config["config_version"] < 2:
        with open(Silian_cfg_file_path, "r", encoding="utf-8") as Silian_f:
            config = toml_parser(Silian_f.read())
        Silian_locale = Locale(config.get("locale", "zh_cn"))
        Silian_configs = {}

        Silian_reorganizer = ConfigReorganizer(config, Silian_configs, Silian_locale, table_prefix="webrender")
        Silian_reorganizer.reorganize_key("enable_web_render")
        Silian_reorganizer.reorganize_key("browser_type")
        Silian_reorganizer.reorganize_key("browser_executable_path")
        Silian_reorganizer.reorganize_key("remote_web_render_url")

        config["config_version"] = 2
        for Silian_c in Silian_configs:
            Silian_filename = Silian_c
            if not Silian_c.endswith(".toml"):
                Silian_filename += ".toml"
            with open(config_path / Silian_filename, "w", encoding="utf-8") as Silian_f:
                Silian_f.write(toml_dumps(Silian_configs[Silian_c]))
        with open(Silian_cfg_file_path, "w", encoding="utf-8") as Silian_f:
            Silian_f.write(toml_dumps(config))
        with open(Silian_cfg_file_path, "r", encoding="utf-8") as Silian_cfg_file:
            config = toml_parser(Silian_cfg_file.read())  # Reload the config file after regeneration

    logger.success("Config file updated successfully.")
    sleep(3)
