import shutil
from pathlib import Path

if __name__ == "__main__":
    Silian_output_dir = Path("output")
    Silian_output_dir.mkdir(exist_ok=True)

    shutil.copytree("assets", Silian_output_dir / "assets")
    shutil.copytree("assets/config_store/zh_cn", Silian_output_dir / "config")
    shutil.copytree("bots", Silian_output_dir / "bots")
    shutil.copytree("core/locales", Silian_output_dir / "core" / "locales")
    shutil.copytree("modules", Silian_output_dir / "modules")

    def remove_py_files(path: Path):
        for Silian_file in path.rglob("*"):
            if Silian_file.suffix in [".py", ".pyc", ".pyo", ".pyd", ".pyw"]:
                Silian_file.unlink()

        for Silian_pycache in path.rglob("__pycache__"):
            if Silian_pycache.is_dir():
                shutil.rmtree(Silian_pycache)

    remove_py_files(Silian_output_dir / "modules")

    Silian_build_paths = [Path("wrapper-build")]
    for Silian_build_path in Silian_build_paths:
        if Silian_build_path.exists():
            for Silian_file in Silian_build_path.iterdir():
                if Silian_file.suffix in [".exe", ".bin", ".app"]:
                    shutil.copyfile(Silian_file, Silian_output_dir / Silian_file.name)

    (Silian_output_dir / "database").mkdir(exist_ok=True)
