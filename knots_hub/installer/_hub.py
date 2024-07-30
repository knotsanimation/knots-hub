import json
import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import pythonning.filesystem

import knots_hub
from knots_hub import OS
from knots_hub.filesystem import HubInstallFilesystem


LOGGER = logging.getLogger(__name__)


class HubInstallersList:
    """
    A mapping of "hub version": "hub filesystem path" listing all the "installer" available.

    Each path can either be a directory to copy or a zip file to extract.

    The user is reponsible of ensuring the paths submitted are valid hub installation,
    i.e. packaged as self-isolated executable.
    """

    def __init__(self, content: List[Tuple[str, Path]]):
        self._content = content

    @property
    def last_version(self) -> str:
        return self._content[-1][0]

    @property
    def last_path(self) -> Path:
        """
        Returns:
            filesystem path to a directory or existing zip file that should exist.
        """
        return self._content[-1][1]

    @classmethod
    def from_file(cls, path: Path) -> "HubInstallersList":
        """
        Get an instance from a serialized json file.

        Args:
            path: filesystem path to an existing json file.
        """

        def _sort_key(k):
            return k[0].split(".")

        def _pathify(pathlike: str) -> Path:
            pathed = Path(pathlike)
            if not pathed.is_absolute():
                # path are considered relative to json dir
                pathed = path.parent / pathed
            return pathed.absolute().resolve()

        with path.open("r", encoding="utf-8") as file:
            raw_content: Dict[str, str] = json.load(file)

        # ensure versions are always sorted with the latest version last in the list
        content = sorted(raw_content.items(), key=_sort_key)
        content = [(item[0], _pathify(item[1])) for item in content]
        return cls(content)

    def get_path(self, version: str) -> Path:
        """
        Get the installer path matching the given version.
        """
        filtered = [item for item in self._content if item[0] == version]
        return filtered[0][1]


def is_hub_up_to_date(installer_list: Optional[HubInstallersList]) -> bool:
    """
    Return True if the current hub version doesn't need update.
    """
    if not installer_list:
        return True

    return knots_hub.__version__ == installer_list.last_version


def install_hub(
    install_src_path: Path,
    filesystem: HubInstallFilesystem,
) -> Path:
    """
    Args:
        install_src_path: filesystem path to an existing directory or existing zip file.
        filesystem: determine where to install

    Returns:
        filesystem path to the installed hub executable
    """
    filesystem.root.mkdir(exist_ok=True)
    pythonning.filesystem.copy_path_to(install_src_path, filesystem.install_src_dir)
    if install_src_path.is_file():
        installed_file = filesystem.install_src_dir / install_src_path.name
        LOGGER.debug(f"extracting zip archive '{installed_file}'")
        pythonning.filesystem.extract_zip(installed_file)

    filesystem.hubinstall_path.write_text(str(time.time()))
    return filesystem.current_exe_src


def uninstall_hub(filesystem: HubInstallFilesystem):
    """
    Exit the hub and uninstall it from the filesystem.

    Args:
        filesystem: determine what filesystem data to uninstall
    """
    prefix = f"{knots_hub.__name__}_uninstall"

    # we will let the system automatically delete the tmp directory
    uninstall_dir = Path(tempfile.mkdtemp(prefix=f"{prefix}_"))

    if OS.is_windows():
        script_path = uninstall_dir / "uninstall.bat"
        script_path.write_text(f'RMDIR /S /Q "{filesystem.root}"', encoding="utf-8")
        exe = str(script_path)
        argv = [exe]
    else:
        script_path = uninstall_dir / "uninstall.sh"
        bash_path = shutil.which("bash")
        script_path.write_text(f'rmdir -rf "{filesystem.root}"', encoding="utf-8")
        exe = str(bash_path)
        # TODO: not sure we need the prefix
        argv = [prefix, str(script_path)]

    LOGGER.debug(f"os.execv({exe}, {argv})")

    # we copy the logs to help debugging potential uninstalling issues
    if filesystem.log_path.exists():
        shutil.copy(filesystem.log_path, uninstall_dir)

    sys.exit(os.execv(exe, argv))


def update_hub(
    update_src_path: Path,
    filesystem: HubInstallFilesystem,
) -> Path:
    """
    Args:
        update_src_path: filesystem path to an existing directory or existing zip file.
        filesystem: determine where to update

    Returns:
        filesystem path to the updated hub executable
    """
    pythonning.filesystem.copy_path_to(update_src_path, filesystem.install_new_dir)
    if update_src_path.is_file():
        installed_file = filesystem.install_src_dir / update_src_path.name
        LOGGER.debug(f"extracting zip archive '{installed_file}'")
        pythonning.filesystem.extract_zip(installed_file)

    return filesystem.current_exe_new
