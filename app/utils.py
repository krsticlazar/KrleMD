import os
import subprocess
from pathlib import Path


def get_output_path(input_path: str, output_dir: str | None = None) -> str:
    input_file = Path(input_path)
    target_dir = Path(output_dir) if output_dir else input_file.parent
    return str(target_dir / f"{input_file.stem}.md")


def open_file_in_explorer(path: str) -> None:
    target = Path(path).resolve()

    if os.name == "nt":
        if target.is_file():
            subprocess.Popen(["explorer.exe", f"/select,{target}"])
        else:
            folder = target if target.is_dir() else target.parent
            subprocess.Popen(["explorer.exe", str(folder)])
        return

    folder = target.parent if target.is_file() else target
    opener = "open" if os.name == "posix" and os.uname().sysname == "Darwin" else "xdg-open"
    subprocess.Popen([opener, str(folder)])
