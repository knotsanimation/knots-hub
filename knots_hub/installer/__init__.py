"""
various software that can be installed on the user system
"""

__all__ = [
    "create_exe_shortcut",
    "get_hub_local_executable",
    "is_hub_up_to_date",
    "install_hub",
    "install_vendor",
    "HubInstallersList",
    "HubInstallFile",
    "BaseVendorInstaller",
    "RezVendorInstaller",
    "read_vendor_installer_from_file",
    "SUPPORTED_VENDORS",
    "uninstall_vendor",
    "vendors",
    "VendorInstallRecord",
]

from ._shortcut import create_exe_shortcut

from ._hubinstallfile import HubInstallFile
from ._vendorrecord import VendorInstallRecord

from ._hub import HubInstallersList
from ._hub import is_hub_up_to_date
from ._hub import get_hub_local_executable
from ._hub import install_hub


from . import vendors
from .vendors import install_vendor
from .vendors import uninstall_vendor
from .vendors import BaseVendorInstaller
from .vendors import RezVendorInstaller
from .vendors import read_vendor_installer_from_file
from .vendors import SUPPORTED_VENDORS
