"""
manipulate the filesystem
"""

import logging
from pathlib import Path
from typing import Optional

from knots_hub.constants import EXECUTABLE_NAME
from knots_hub.constants import OS

LOGGER = logging.getLogger(__name__)


class HubInstallFilesystem:
    """
    Represent the filesystem structure of a hub installation.

    Not all paths are guaranteed to exist depending on the state of the installation.

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

        if OS.is_windows():
            executable_filename = f"{EXECUTABLE_NAME}.exe"
        else:
            executable_filename = f"{EXECUTABLE_NAME}"

        self.exe_old = self.install_old_dir / executable_filename
        """
        filesystem path to the location of the executable in the "old" install step
        """

        self.exe_src = self.install_src_dir / executable_filename
        """
        filesystem path to the location of the executable in the "src" install step
        """

        self.exe_new = self.install_new_dir / executable_filename
        """
        filesystem path to the location of the executable in the "new" install step
        """

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
        filesystem path to the last installed executable (that may still need update steps).
        """
        if self.exe_new.exists():
            return self.exe_new
        if self.exe_src.exists():
            return self.exe_src
        if self.exe_old.exists():
            return self.exe_old
        return None
