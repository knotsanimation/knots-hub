"""
manipulate the filesystem
"""

import logging
from pathlib import Path
from typing import Optional

from knots_hub import OS
from knots_hub.constants import EXECUTABLE_NAME
from knots_hub.constants import EXECUTABLE_NAME_REGEX

LOGGER = logging.getLogger(__name__)


def find_hub_executable(directory: Path) -> Optional[Path]:
    """
    Get the path of the hub executable stored in the given directory.

    Args:
        directory: filesystem path to an existing directory

    Returns:
        filesystem path to an existing file or None if not found
    """
    for filepath in directory.glob("*"):
        if filepath.is_dir():
            continue
        if EXECUTABLE_NAME_REGEX.search(filepath.name):
            return filepath
    return None


def get_expected_hub_executable(directory: Path) -> Path:
    """
    Get the path of the expected hub executable for this library version.

    Note a previous version might be installed locally so this is why this path might
    exist or not.

    Args:
        directory: filesystem path to a directory that may exist

    Returns:
        filesystem path to a file that might exist or not.
    """
    if OS.is_windows():
        return directory / f"{EXECUTABLE_NAME}.exe"
    return directory / EXECUTABLE_NAME


class HubInstallFilesystem:
    """
    Represent the filesystem structure of a hub installation.

    NOT all paths are guaranteed to exist depending on the state of the installation.

    THe dintinction between "expected" and "current" for executable path is caused
    by the possibility of having a local instance that is at an older version than
    the current runtime (which may have been started from the server executable that
    is not installe dyet but is about to).

    Args:
        root: filesystem path to a directory that may not exist yet.
    """

    def __init__(self, root: Path):
        self.root = root
        """
        filesystem path to a root directory that may not exist yet.
        """

        self.install_old_dir = root / "install-old"
        """
        filesystem path to the location to store the "old" install step
        """

        self.install_src_dir = root / "install-src"
        """
        filesystem path to the location to store the "src" install step
        """

        self.install_new_dir = root / "install-new"
        """
        filesystem path to the location to store the "new" install step
        """

        # note: logs are rotated so there might be multiple of those
        self.log_path = root / "hub.log"
        """
        filesystem path to the location to store disk logs
        """

        self.hubinstall_path = root / ".hubinstall"
        """
        filesystem path to the location to the file indicating the directectory is a root hub install.
        """

    @property
    def current_exe_src(self) -> Optional[Path]:
        """
        Returns:
            filesystem path to an existing executable or None if not found
        """
        return find_hub_executable(self.install_src_dir)

    @property
    def current_exe_old(self) -> Optional[Path]:
        """
        Returns:
            filesystem path to an existing executable or None if not found
        """
        return find_hub_executable(self.install_old_dir)

    @property
    def current_exe_new(self) -> Optional[Path]:
        """
        Returns:
            filesystem path to an existing executable or None if not found
        """
        return find_hub_executable(self.install_new_dir)

    @property
    def expected_exe_src(self) -> Path:
        """
        Returns:
            filesystem path to an executable that may exist
        """
        return get_expected_hub_executable(self.install_src_dir)

    @property
    def expected_exe_old(self) -> Path:
        """
        Returns:
            filesystem path to an executable that may exist
        """
        return get_expected_hub_executable(self.install_old_dir)

    @property
    def expected_exe_new(self) -> Path:
        """
        Returns:
            filesystem path to an executable that may exist
        """
        return get_expected_hub_executable(self.install_new_dir)

    @property
    def is_installed(self) -> bool:
        return self.hubinstall_path.exists()

    @property
    def installed_time(self) -> Optional[float]:
        """
        Returns:
            time in seconds since the Epoch at which the hub was installed for the first time.
        """
        if not self.hubinstall_path.exists():
            return None
        return float(self.hubinstall_path.read_text("utf-8"))

    @property
    def last_executable(self) -> Optional[Path]:
        """
        Filesystem path to the last locally installed executable (that may still need update steps).

        Note the executable might be of a previous version than the current runtime.
        """
        if self.current_exe_new:
            return self.current_exe_new
        if self.current_exe_src:
            return self.current_exe_src
        if self.current_exe_old:
            return self.current_exe_old
        return None
