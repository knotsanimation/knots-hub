import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

import knots_hub
from knots_hub import HubLocalFilesystem
from knots_hub import OS
from knots_hub.filesystem import rmtree
from knots_hub.installer import HubInstallFile

LOGGER = logging.getLogger(__name__)


def uninstall_paths(paths: list[Path]):
    """
    Exit the hub and remove anything file related to knots-hub from the filesystem.

    Args:
        paths: list of existing filesystem path to remove
    """
    prefix = f"{knots_hub.__name__}_uninstall"

    # we will let the system automatically delete the tmp directory
    uninstall_dir = Path(tempfile.mkdtemp(prefix=f"{prefix}_"))

    if OS.is_windows():
        script_path = uninstall_dir / "uninstall.bat"
        content = [
            f'{"RMDIR" if path.is_dir() else "DEL"} /S /Q "{path}"' for path in paths
        ]
        content += [
            f'start /b "" cmd /C RMDIR /S /Q "{uninstall_dir}"',
        ]
        script_path.write_text("\n".join(content), encoding="utf-8")
        exe = str(script_path)
        argv = [exe]
    else:
        script_path = uninstall_dir / "uninstall.sh"
        bash_path = shutil.which("bash")
        content = [f'rm -rf "{path}"' for path in paths]
        script_path.write_text("\n".join(content), encoding="utf-8")
        exe = str(bash_path)
        # TODO: not sure we need the prefix
        argv = [prefix, str(script_path)]

    LOGGER.debug(f"os.execv({exe}, {argv})")

    sys.exit(os.execv(exe, argv))


def get_paths_to_uninstall(filesystem: HubLocalFilesystem) -> list[Path]:
    """
    Get all the paths that need to be removed to fully delete the hub from the local user system.

    Args:
        filesystem: collection of paths for storing runtime data

    Returns:
        list of existing filesystem path (files or directories).
    """
    to_uninstall = []

    hubinstall_path = filesystem.hubinstallfile_path
    hubinstall = HubInstallFile.read_from_disk(hubinstall_path)
    paths = (
        [hubinstall.installed_path]
        + hubinstall.additional_paths
        + [filesystem.root_dir]
    )

    for path in paths:
        if not path.exists():
            continue
        to_uninstall.append(path)

    return to_uninstall


def uninstall_hub_only(hubinstall_file: HubInstallFile):
    """
    Only uninstall the hub but not the vendors or additional paths.
    """
    installed_path = hubinstall_file.installed_path
    LOGGER.debug(f"rmtree('{installed_path}')")
    rmtree(installed_path)
