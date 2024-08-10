"""
various software that can be installed on the user system
"""

__all__ = [
    "create_exe_shortcut",
    "is_hub_up_to_date",
    "install_hub",
    "uninstall_hub",
    "update_hub",
    "HubInstallersList",
    "BaseVendorInstaller",
    "RezVendorInstaller",
    "read_vendor_installers_from_file",
    "SUPPORTED_INSTALLERS",
]

from ._shortcut import create_exe_shortcut

from ._hub import is_hub_up_to_date
from ._hub import install_hub
from ._hub import uninstall_hub
from ._hub import update_hub
from ._hub import HubInstallersList

from ._base import BaseVendorInstaller
from ._rez import RezVendorInstaller

from ._io import read_vendor_installers_from_file
from ._io import SUPPORTED_INSTALLERS
