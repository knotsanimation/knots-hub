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
        self.install_old_dir = root / "install-old"
        self.install_src_dir = root / "install-src"
        self.install_new_dir = root / "install-new"
        # note: logs are rotated so there might be multiple of those
        self.log_path = root / "hub.log"
        self.hubinstall_path = root / ".hubinstall"

        if OS.is_windows():
            executable_filename = f"{EXECUTABLE_NAME}.exe"
        else:
            executable_filename = f"{EXECUTABLE_NAME}"

        self.exe_old = self.install_old_dir / executable_filename
        self.exe_src = self.install_src_dir / executable_filename
        self.exe_new = self.install_new_dir / executable_filename

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
