import logging
import time
from pathlib import Path
from typing import Optional

from ._base import BaseVendorInstaller
from knots_hub.filesystem import rmtree
from knots_hub.installer import VendorInstallRecord

LOGGER = logging.getLogger(__name__)


def uninstall_vendor(record_file: VendorInstallRecord):
    """
    Uninstall the previously installed vendor as recorded by the given file.
    """
    for path in [record_file.installed_path] + record_file.extra_paths:
        if path.is_file():
            LOGGER.debug(f"unlink('{path}')")
            path.unlink()
        elif path.is_dir():
            LOGGER.debug(f"rmtree('{path}')")
            rmtree(path)
        else:
            LOGGER.debug(f"skipping already deleted '{path}'")
            # the path doesn't exist anymore (manually deleted somehow)
            continue


def install_vendor(
    vendor: BaseVendorInstaller,
    record_path: Path,
) -> bool:
    """
    Install OR update the vendor as configured by the user.

    Args:
        vendor: the vendor installer instance to install/update.
        record_path:
            filesystem path to a file that may exist and should record the
            last and future vendor installation configuration.
    """
    record_file: Optional[VendorInstallRecord] = None
    if record_path.exists():
        record_file = VendorInstallRecord.read_from_disk(record_path)

    if record_file and vendor.get_hash() == record_file.install_hash:
        # already up-to-date
        return False

    if record_file:
        uninstall_vendor(record_file)

    try:
        vendor.install()
    except:
        if record_file:
            LOGGER.debug(
                "upcoming vendor install error, removing potential files created."
            )
            uninstall_vendor(record_file)
        raise

    record_file = VendorInstallRecord(
        name=vendor.name(),
        installed_time=time.time(),
        install_hash=vendor.get_hash(),
        installed_path=vendor.install_dir,
        extra_paths=vendor.dirs_to_make,
    )
    LOGGER.debug(f"writing VendorInstallRecord to '{record_path}'")
    record_file.write_to_disk(record_path)
    return True
