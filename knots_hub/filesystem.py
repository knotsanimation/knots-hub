import logging
from pathlib import Path
from typing import Optional

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
        # XXX: some paths are used by the launcher scripts, kept them synced !
        self.venv_dir = root / ".venv"
        self.python_dir = root / "python"
        self.updating_dir = root / "__newupdate__"
        # note: logs are rotated so there might be multiple of those
        self.log_path = root / "hub.log"
        self.launcher_win_path = root / "hub-launcher.ps1"
        self.launcher_linux_path = root / "hub-launcher.sh"
        self.python_version_path = root / ".pythonversion"
        self.hubinstall_path = root / ".hubinstall"
        self.requirements_path = root / "resolved-requirements.txt"

    @property
    def updating_filesystem(self) -> "HubInstallFilesystem":
        """
        Filesystem for the new update.

        Ensure there is a new update existing before using this property.
        """
        return HubInstallFilesystem(self.updating_dir)

    @property
    def launcher_path(self) -> Path:
        """
        Path to the launcher script depending on the current OS.
        """
        if OS.is_windows():
            return self.launcher_win_path
        else:
            return self.launcher_linux_path

    @property
    def python_bin_path(self) -> Path:
        """
        Path of the python interepeter executable depending on the current OS.
        """
        if OS.is_windows():
            return self.python_dir / "python.exe"
        else:
            return self.python_dir / "bin" / "python"

    @property
    def python_version(self) -> str:
        """
        The full python version of the python interpeter installed.
        """
        return self.python_version_path.read_text("utf-8")

    @property
    def is_updating(self) -> bool:
        """
        Returns:
            True if the hub is being updated with new a new python environment.
        """
        return self.updating_filesystem.root.exists()

    @property
    def installed_time(self) -> Optional[float]:
        """
        Returns:
            time in seconds since the Epoch at which the hub was installed for the first time.
        """
        if not self.hubinstall_path.exists():
            return None
        return float(self.hubinstall_path.read_text("utf-8"))
