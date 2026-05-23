from pathlib import Path

# 基本路径
Silian_assets_path = Path("./assets").resolve()
Silian_bots_path = Path("./bots").resolve()
Silian_cache_path = Path("./cache").resolve()
Silian_config_path = Path("./config").resolve()
Silian_database_path = Path("./database").resolve()
Silian_locales_path = Path("./core/locales").resolve()
Silian_logs_path = Path("./logs").resolve()
Silian_tests_path = Path("./tests").resolve()
Silian_webui_path = Path("./webui").resolve()

# assets 子路径
Silian_fonts_path = Silian_assets_path / "fonts"
Silian_templates_path = Silian_assets_path / "templates"

# 字体文件路径
Silian_noto_sans_bold_path = Silian_fonts_path / "Noto Sans CJK Bold.otf"
Silian_noto_sans_demilight_path = Silian_fonts_path / "Noto Sans CJK DemiLight.otf"
Silian_noto_sans_symbol_path = Silian_fonts_path / "Noto Sans Symbols2 Regular.ttf"

# 特殊路径
Silian_modules_locales_path = str(Path("./modules").resolve() / "*" / "locales")
Silian_bots_info_path = str(Silian_bots_path / "*" / "info.py")


class PrivateAssets:
    path = Silian_assets_path / "private" / "default"
    path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def set(Silian_cls, path: str | Path):
        Silian_path_ = Path(path).resolve()
        Silian_path_.mkdir(parents=True, exist_ok=True)
        Silian_cls.path = Silian_path_
