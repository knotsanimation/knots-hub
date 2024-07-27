import json
import logging
from pathlib import Path
from typing import Dict
from typing import List
from typing import Type

from ._base import BaseVendorInstaller
from ._rez import RezVendorInstaller

LOGGER = logging.getLogger(__name__)

SUPPORTED_INSTALLERS: Dict[str, Type[BaseVendorInstaller]] = {
    RezVendorInstaller.name(): RezVendorInstaller,
}
"""
A mapping of vendor software name: installer that can be installed
"""


def read_vendor_installers_from_file(
    file_path: Path,
    install_root_path: Path,
) -> List[BaseVendorInstaller]:
    """
    Get a list of installer from a serialized representation.

    The representation is a simple dict::

        {
            "installerName": {
                "version": 1,
                "firstInstallerKwarg": "3.10.11",
                "secondInstallerKwarg": "2.109.0",
                ...
            },
            ...
        }

    Args:
        file_path: filesystem path to an existing json file.
        install_root_path:
            filesystem path to a directory where each installer can create its necessary
            files. The directory must be existing.

    Returns:
        list of unique installer instances (no subclass duplicates).
    """
    with file_path.open(encoding="utf-8") as file:
        raw_content = json.load(file)

    installers = []

    for installer_name, installer_params in raw_content.items():
        installer_class = SUPPORTED_INSTALLERS.get(installer_name)
        if not installer_class:
            raise ValueError(
                f"Unsupported installer name '{installer_name}'. "
                f"Pick one out of {SUPPORTED_INSTALLERS.keys()}."
            )
        install_dir = install_root_path / installer_name

        if not installer_params.get("version"):
            raise KeyError(f"Missing 'version' key in {installer_params}")

        if not isinstance(installer_params["version"], int):
            raise TypeError(
                f"'version' param must be an integer, not {installer_params['version']!r}"
            )

        installer_params["install_dir"] = install_dir
        installer = installer_class(**installer_params)
        installers.append(installer)

    return installers
