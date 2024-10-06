"""
Variables that are constants through the app runtime.
"""

import re
import sys
from pathlib import Path

import knots_hub


class Environ:
    """
    Global list of supported environment variables.
    """

    _ENVPREFIX = "KNOTSHUB"

    USER_INSTALL_PATH = f"{_ENVPREFIX}_USER_INSTALL_PATH"
    """
    Filesystem path to the location on the user system where the hub is installed.
    """

    INSTALLER = f"{_ENVPREFIX}_INSTALLER"
    """
    Expression like 'version=path' indicating configuration for installing the hub.
    """

    VENDOR_INSTALLER_CONFIG_PATHS = f"{_ENVPREFIX}_VENDOR_INSTALLER_CONFIG_PATHS"
    """
    List of filesystem path to existing json files used to specify which 
    external program to install with which version. The list of path is separated
    by the system path separator character.
    """

    DISABLE_LOCAL_CHECK = f"{_ENVPREFIX}_DISABLE_LOCAL_CHECK"
    """
    Disable the check verifying if the app is directly launched from 
    the server or locally.
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

    @classmethod
    def raise_unsupported(cls):
        raise OSError(f"Unsupported operating system '{cls}'")


EXECUTABLE_NAME = f"{knots_hub.__name__}-v{knots_hub.__version__}"
"""
Name to give to the packaged executable, without the file extension.
"""

EXECUTABLE_NAME_REGEX = re.compile(rf"{knots_hub.__name__}-v[\d.]+")
"""
An expression that must match wen a string is a potential EXECUTABLE_NAME
"""

SHORTCUT_NAME = "knots-hub"
"""
Name of the shortcut to the last executable, without the file extension.

Changing this could have unplanned consequences.
"""

# https://nuitka.net/user-documentation/tips.html#detecting-nuitka-at-run-time
_IS_PACKAGED_NUITKA = hasattr(knots_hub, "__compiled__")

IS_APP_FROZEN = _IS_PACKAGED_NUITKA
"""
Find if the current runtime is a packaged executable.
"""


# XXX: the if condition is because the nuitka compiled app seems to return
#  'python.exe' in 'sys.executable' which doesn't exist on disk.
INTERPRETER_PATH: Path = Path(sys.argv[0]) if IS_APP_FROZEN else Path(sys.executable)
"""
Filesystem path to the python interpeter or executable running the current code.
"""
