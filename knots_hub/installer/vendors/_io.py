import json
import logging
from pathlib import Path
from typing import Type

from ._base import BaseVendorInstaller
from ._rez import RezVendorInstaller
from knots_hub._utils import expand_envvars

LOGGER = logging.getLogger(__name__)

SUPPORTED_INSTALLERS: dict[str, Type[BaseVendorInstaller]] = {
    RezVendorInstaller.name(): RezVendorInstaller,
}
"""
A mapping of vendor software name: installer that can be installed
"""

SUPPORTED_INSTALLERS_DOCUMENTATION = {
    RezVendorInstaller: [
        "Installer for `rez <https://github.com/AcademySoftwareFoundation/rez>`_.",
        "",
        "Expect the following arguments:",
        "",
        "- ``version`` `(int)`: an arbitrary integer that must be incremented on every other argument change to trigger updates on the user system.",
        "- ",
        "  ``install_dir`` `(str)`: filesystem path to a directory that may exists. "
        "  The parent directory must exist (use the ``dirs_to_make`` if the parent may not exist yet). The path can contains environment variable"
        "  like *$ENVAR/foo* where the ``$`` can be escaped by doubling it like ``$$``.",
        "- ",
        "  ``dirs_to_make`` `(list[str])`: optional list of filesystem path to directories that may exists. "
        "  Each directory will be created on install if it doesn't exist but each of their parent directory must exist. "
        "  The path can contains environment variable"
        "  like *$ENVAR/foo* where the ``$`` can be escaped by doubling it like ``$$``.",
        "- ``python_version`` `(str)`: a full valid python version to install rez with.",
        "- ``rez_version`` `(str)`: a full valid rez version to install from the official GitHub repo.",
        # note that `install_dir` is provided by `read_vendor_installers_from_file`
    ]
}


def read_vendor_installers_from_file(
    file_path: Path,
) -> list[BaseVendorInstaller]:
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

        # we can only verify the parameters of ``BaseVendorInstaller``

        if not installer_params.get("version"):
            raise KeyError(f"Missing 'version' key in {installer_params}")
        if not installer_params.get("install_dir"):
            raise KeyError(f"Missing 'install_dir' key in {installer_params}")

        if not isinstance(installer_params["version"], int):
            raise TypeError(
                f"'version' param must be an integer, not {installer_params['version']!r}"
            )

        installer_params["install_dir"] = Path(
            expand_envvars(installer_params["install_dir"])
        )

        dirs_to_make = installer_params.get("dirs_to_make")
        if dirs_to_make:
            if not isinstance(dirs_to_make, list):
                raise TypeError(
                    f"'dirs_to_make' param must be a list of paths, not {dirs_to_make!r}"
                )

            installer_params["dirs_to_make"] = [
                Path(expand_envvars(path)) for path in dirs_to_make
            ]

        installer = installer_class(**installer_params)
        installers.append(installer)

    return installers
