"""
various external software that can be installed on the user system
"""

__all__ = [
    "BaseVendorInstaller",
    "install_vendor",
    "read_vendor_installer_from_file",
    "RezVendorInstaller",
    "SUPPORTED_VENDORS",
    "uninstall_vendor",
    "VendorNameError",
]


from ._base import BaseVendorInstaller
from ._base import VendorNameError
from ._python import install_python
from ._rez import RezVendorInstaller

from ._io import read_vendor_installer_from_file
from ._io import SUPPORTED_VENDORS

from ._install import install_vendor
from ._install import uninstall_vendor
