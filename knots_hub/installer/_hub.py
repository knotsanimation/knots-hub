import json
import logging
import time
from pathlib import Path
from typing import Optional

import pythonning.filesystem

from knots_hub.config import HubInstallerConfig
from knots_hub.filesystem import HubLocalFilesystem
from knots_hub.filesystem import find_hub_executable
from knots_hub.installer import HubInstallRecord

LOGGER = logging.getLogger(__name__)


def is_hub_up_to_date(
    installer: Optional[HubInstallerConfig],
    filesystem: HubLocalFilesystem,
) -> bool:
    """
    Return True if the current hub version doesn't need update.

    Args:
        installer: optional expected configuration of the hub installation
        filesystem: collection of paths for storing runtime data
    """
    hubrecord_path = filesystem.hubinstall_record_path
    if not installer or not hubrecord_path.exists():
        return True

    hubinstall = HubInstallRecord.read_from_disk(hubrecord_path)
    return hubinstall.installed_version == installer.version


def get_hub_local_executable(filesystem: HubLocalFilesystem) -> Optional[Path]:
    """
    Find the filesystem path to the locally installed hub executable file.

    Args:
        filesystem: collection of paths for storing runtime data

    Returns:
        filesystem path to an existing file or None if not found.
    """
    hubrecord_path = filesystem.hubinstall_record_path
    if not hubrecord_path.exists():
        return None
    hubinstall = HubInstallRecord.read_from_disk(hubrecord_path)
    install_dir = hubinstall.installed_path
    if not install_dir:
        LOGGER.warning("Found local HubInstallRecord with null 'installed_path'")
        return None
    return find_hub_executable(install_dir)


def install_hub(
    install_src_path: Path,
    install_dst_path: Path,
    installed_version: str,
    hubrecord_path: Path,
) -> Path:
    """
    Args:
        install_src_path:
            filesystem path to a directory which correspond to the new hub to install.
        install_dst_path:
            filesystem path to the directory location to install the hub to.
        installed_version: the hub version that is being installed
        hubrecord_path: filesystem path the HubInstallRecord file

    Returns:
        filesystem path to the installed hub executable
    """
    pythonning.filesystem.copy_path_to(install_src_path, install_dst_path)
    hubrecord = HubInstallRecord(
        installed_time=time.time(),
        installed_version=installed_version,
        installed_path=install_dst_path,
    )
    hubrecord.update_disk(hubrecord_path)
    return find_hub_executable(install_dst_path)
