import logging
import os
from pathlib import Path
from typing import Type

from ._base import BaseVendorInstaller
from ._base import VendorNameError
from ._rez import RezVendorInstaller
from knots_hub import serializelib

LOGGER = logging.getLogger(__name__)

SUPPORTED_VENDORS: dict[str, Type[BaseVendorInstaller]] = {
    RezVendorInstaller.name(): RezVendorInstaller,
}
"""
A mapping of vendor software name: associated installer 
"""


def read_vendor_installer_from_file(
    file_path: Path,
) -> list[BaseVendorInstaller]:
    """
    Get the vendor installers serialized in the given file.

    Args:
        file_path: filesystem path to an existing json file.

    Returns:
        list of corresponding instances.
    """
    context = serializelib.UnserializeContext(
        environ=os.environ.copy(),
        parent_dir=file_path.parent,
    )
    serialized: str = file_path.read_text(encoding="utf-8")
    vendors: list[BaseVendorInstaller] = []

    for supported_vendor in SUPPORTED_VENDORS.values():
        try:
            vendor = supported_vendor.unserialize(serialized, context=context)
        except VendorNameError:
            continue
        vendors.append(vendor)

    if not vendors:
        raise ValueError(f"No matching vendor installer found from file '{file_path}'")

    return vendors
