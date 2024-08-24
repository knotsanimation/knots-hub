import json
import logging
import time
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import pythonning.filesystem

from knots_hub.filesystem import HubLocalFilesystem
from knots_hub.filesystem import find_hub_executable
from knots_hub.installer import HubInstallFile
from knots_hub.installer.vendors import BaseVendorInstaller

LOGGER = logging.getLogger(__name__)


class HubInstallersList:
    """
    A mapping of "hub version": "hub filesystem path" listing all the "installer" available.

    Each path can either be a directory to copy or a zip file to extract.

    The user is reponsible of ensuring the paths submitted are valid hub installation,
    i.e. packaged as self-isolated executable.
    """

    def __init__(self, content: List[Tuple[str, Path]]):
        self._content = content

    @property
    def last_version(self) -> str:
        return self._content[-1][0]

    @property
    def last_path(self) -> Path:
        """
        Returns:
            filesystem path to a directory or existing zip file that should exist.
        """
        return self._content[-1][1]

    @classmethod
    def from_file(cls, path: Path) -> "HubInstallersList":
        """
        Get an instance from a serialized json file.

        Args:
            path: filesystem path to an existing json file.
        """

        def _sort_key(k):
            return k[0].split(".")

        def _pathify(pathlike: str) -> Path:
            pathed = Path(pathlike)
            if not pathed.is_absolute():
                # path are considered relative to json dir
                pathed = path.parent / pathed
            return pathed.absolute().resolve()

        with path.open("r", encoding="utf-8") as file:
            raw_content: Dict[str, str] = json.load(file)

        # ensure versions are always sorted with the latest version last in the list
        content = sorted(raw_content.items(), key=_sort_key)
        content = [(item[0], _pathify(item[1])) for item in content]
        return cls(content)

    def get_path(self, version: str) -> Path:
        """
        Get the installer path matching the given version.
        """
        filtered = [item for item in self._content if item[0] == version]
        return filtered[0][1]


def is_hub_up_to_date(
    installer_list: Optional[HubInstallersList],
    filesystem: HubLocalFilesystem,
) -> bool:
    """
    Return True if the current hub version doesn't need update.

    Args:
        installer_list: collection of hub installers to chekc against
        filesystem: collection of paths for storing runtime data
    """
    hubinstall_path = filesystem.hubinstallfile_path
    if not installer_list or not hubinstall_path.exists():
        return True

    hubinstall = HubInstallFile.read_from_disk(hubinstall_path)
    return hubinstall.installed_version == installer_list.last_version


def get_hub_local_executable(filesystem: HubLocalFilesystem) -> Optional[Path]:
    """
    Find the filesystem path to the locally installed hub executable file.

    Args:
        filesystem: collection of paths for storing runtime data

    Returns:
        filesystem path to an existing file or None if not found.
    """
    hubinstall_path = filesystem.hubinstallfile_path
    if not hubinstall_path.exists():
        return None
    hubinstall = HubInstallFile.read_from_disk(hubinstall_path)
    install_dir = hubinstall.installed_path
    return find_hub_executable(install_dir)


def install_hub(
    install_src_path: Path,
    install_dst_path: Path,
    installed_version: str,
    filesystem: HubLocalFilesystem,
) -> Path:
    """
    Args:
        install_src_path:
            filesystem path to a directory which correspond to the new hub to install.
        install_dst_path:
            filesystem path to the directory location to install the hub to.
        installed_version: the hub version that is being installed
        filesystem: collection of paths for storing runtime data

    Returns:
        filesystem path to the installed hub executable
    """
    pythonning.filesystem.copy_path_to(install_src_path, install_dst_path)
    hubinstallfile = HubInstallFile(
        installed_time=time.time(),
        installed_version=installed_version,
        installed_path=install_dst_path,
    )
    hubinstallfile_path = filesystem.hubinstallfile_path
    hubinstallfile.update_disk(hubinstallfile_path)
    return find_hub_executable(install_dst_path)


def install_vendors(
    vendors: list[BaseVendorInstaller],
    filesystem: HubLocalFilesystem,
) -> list[Path]:
    """
    Install OR update the vendor as configured by the user.

    Args:
        vendors: list of vendor software to install/update.
        filesystem: collection of paths for storing runtime data

    Returns:
        list of existing filesystem paths that have been created for the installation.
        those paths can be removed to uninstall the software.
    """
    installed_paths = []

    # install vendors
    for vendor_installer in vendors:
        if vendor_installer.version_installed == vendor_installer.version:
            LOGGER.debug(f"{vendor_installer} is up-to-date")
            continue

        if vendor_installer.is_installed:
            # we uninstall so we can install the latest version
            LOGGER.info(f"uninstalling {vendor_installer}")
            vendor_installer.uninstall()

        LOGGER.info(f"installing {vendor_installer}")
        vendor_installer.install()

        installed_paths.append(vendor_installer.install_dir)
        installed_paths += vendor_installer.dirs_to_make

    if not installed_paths:
        # all vendors were up-to-date
        return []

    hubinstallfile = HubInstallFile(
        additional_paths=installed_paths,
    )
    hubinstallfile_path = filesystem.hubinstallfile_path
    hubinstallfile.update_disk(hubinstallfile_path)

    return installed_paths
