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

    TERMINAL_WINDOWS = f"{_ENVPREFIX}_TERMINAL_WINDOWS"
    TERMINAL_LINUX = f"{_ENVPREFIX}_TERMINAL_LINUX"

    # XXX: keep in sync with launcher scripts

    _LAUNCHERENVPREFIX = "_KNOTSHUBLAUNCHER"

    LAUNCHER_UPDATE_CWD = f"{_LAUNCHERENVPREFIX}_UPDATE_CWD"
    """
    When restarted, ask the launcher script to perform an update of the installation using this current working directory.
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


INSTALLER_TEMP_DIR_PREFIX = "knots_hub_installer_"
