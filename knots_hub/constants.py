"""
Variables that are constants through the app runtime.
"""

import re
import sys

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

    INSTALLER_LIST_PATH = f"{_ENVPREFIX}_INSTALLER_LIST"
    """
    Filesystem path to an existing json file which list all the hub version available
    with an associated path for download.
    """

    VENDOR_INSTALLERS_CONFIG_PATH = f"{_ENVPREFIX}_VENDOR_INSTALLERS_CONFIG"
    """
    Filesystem path to an existing json file used to specify which 
    external program to install with which version.
    """

    VENDOR_INSTALL_PATH = f"{_ENVPREFIX}_VENDOR_INSTALL_PATH"
    """
    Filesystem path to a directory that may exist which is used as root for installing
    all vendor programs specified in the vendor installers config.
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
