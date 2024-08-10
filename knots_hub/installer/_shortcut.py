import logging
import os
import subprocess
from pathlib import Path

import knots_hub.constants
from knots_hub import OS

LOGGER = logging.getLogger(__name__)

THIS_DIR = Path(__file__).parent

WINDOWS_SHORTCUT_SCRIPT = THIS_DIR / "create-windows-shortcut.ps1"
assert WINDOWS_SHORTCUT_SCRIPT.exists(), WINDOWS_SHORTCUT_SCRIPT


def create_exe_shortcut(
    shortcut_dir: Path,
    exe_path: Path,
    dry_run: bool = False,
) -> Path:
    """
    Create a file that link to the given executable.

    Args:
        shortcut_dir: filesystem path to an existing directory.
        exe_path: executable file the shortcut links to.
        dry_run: just return without actually creating files on disk
    """
    shortcut_name = knots_hub.constants.SHORTCUT_NAME
    if OS.is_windows():
        shortcut_path = shortcut_dir / f"{shortcut_name}.lnk"
        command = [
            "powershell.exe",
            "-NonInteractive",
            "-NoProfile",
            str(WINDOWS_SHORTCUT_SCRIPT),
            str(shortcut_path),
            str(exe_path),
            "-iconPath",
            str(exe_path),
        ]
        LOGGER.debug(f"subprocess.run('{command}')")
        if not dry_run:
            if shortcut_path.exists():
                os.unlink(shortcut_path)
            subprocess.run(command)
    else:
        shortcut_path = shortcut_dir / f"{shortcut_name}{exe_path.suffix}"
        LOGGER.debug(f"os.symlink('{exe_path}', '{shortcut_path}')")
        if not dry_run:
            if shortcut_path.exists():
                os.unlink(shortcut_path)
            os.symlink(exe_path, shortcut_path)

    return shortcut_path
