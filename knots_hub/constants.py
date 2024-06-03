import os
import sys
from pathlib import Path

import knots_hub


class Environ:
    _ENVPREFIX = "KNOTSHUB"

    USER_INSTALL_PATH = f"{_ENVPREFIX}_USER_INSTALL_PATH"
    """
    Filesystem path to the location on the user system where the hub is installed.
    """

    INSTALLER_REQUIREMENTS_PATH = f"{_ENVPREFIX}_INSTALLER_REQUIREMENTS_PATH"
    """
    Filesystem path to an existing requirements.txt file that is used to determine the
    dependencies required to keep the hub up-to-date.
    """

    PYTHON_VERSION = f"{_ENVPREFIX}_PYTHON_VERSION"
    """
    Full version of the python interpreter to install for the hub.
    """


class OS:
    """
    Current operating system.
    """

    _current = sys.platform

    def __str__(self) -> str:
        return self.name()

    @classmethod
    def name(cls) -> str:
        return cls._current

    @classmethod
    def is_linux(cls) -> bool:
        return cls._current.startswith("linux")

    @classmethod
    def is_mac(cls) -> bool:
        return cls._current.startswith("darwin")

    @classmethod
    def is_windows(cls) -> bool:
        return cls._current in ("win32", "cygwin")


_MODULE_PATH = Path(knots_hub.__file__).parent


def _LOCAL_ROOT_PATH():
    if OS.is_windows():
        return Path(os.environ["LOCALAPPDATA"]) / "knots_hub"
    else:
        return Path("/etc", "knots_hub")


LOCAL_ROOT_PATH: Path = _LOCAL_ROOT_PATH()
"""
Filesystem path to a directory on the user local system that might be created with 
mkdir and used to store any data needed by the hub.
"""


class LocalRootFilesystem:
    def __init__(self, root: Path):
        self.root = root
        self.log_path = root / "hub.log"
        self.install_dir = root / ".install"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.root})"

    def initialize(self) -> bool:
        """
        Returns:
            True if the filesystem needed tobe initialized else False.
        """
        if not self.root.exists():
            self.root.mkdir()
            return True

        return False


LOCAL_ROOT_FILESYSTEM: LocalRootFilesystem = LocalRootFilesystem(LOCAL_ROOT_PATH)
