"""
various external software that can be installed on the user system
"""

__all__ = [
    "BaseVendorInstaller",
    "read_vendor_installers_from_file",
    "RezVendorInstaller",
    "SUPPORTED_INSTALLERS",
    "SUPPORTED_INSTALLERS_DOCUMENTATION",
]


from ._base import BaseVendorInstaller
from ._python import install_python
from ._rez import RezVendorInstaller

from ._io import read_vendor_installers_from_file
from ._io import SUPPORTED_INSTALLERS
from ._io import SUPPORTED_INSTALLERS_DOCUMENTATION
