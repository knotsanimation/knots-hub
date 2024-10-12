import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path

import knots_hub
from knots_hub import HubLocalFilesystem
from knots_hub import OS
from knots_hub.filesystem import rmtree
from knots_hub.installer import HubInstallRecord
from knots_hub.installer import VendorInstallRecord

LOGGER = logging.getLogger(__name__)


def uninstall_paths(paths: list[Path]):
    """
    Exit the hub and remove anything file related to knots-hub from the filesystem.

    Args:
        paths: list of existing filesystem path to remove
    """
    prefix = f"{knots_hub.__name__}_uninstall"

    # we will let the system automatically delete the tmp directory
    uninstall_dir = Path(tempfile.mkdtemp(prefix=f"{prefix}_"))

    # XXX: we cannot guarantee that all path exists at the exact moment they are deleted.
    #   example if paths=["/foo", "/foo/bar"], "/foo" being deleted first, we can't delete "/foo/bar".

    if OS.is_windows():
        script_path = uninstall_dir / "uninstall.bat"
        content = ["@echo off"]
        for path in paths:
            content += [
                f"echo - removing '{path}' ...",
                f'{"RMDIR" if path.is_dir() else "DEL"} /S /Q "{path}"',
                f"echo   ^ removed !",
            ]
        content += [
            "echo - removing uninstalling script",
            f'start /b "" cmd /C RMDIR /S /Q "{uninstall_dir}"',
        ]
        script_path.write_text("\n".join(content), encoding="utf-8")
        exe = str(script_path)
        argv = [exe]
    else:
        script_path = uninstall_dir / "uninstall.sh"
        bash_path = shutil.which("bash")
        content = []
        for path in paths:
            content += [
                f"echo ⨂ removing '{path}' ...",
                f'rm -rf "{path}"',
                f"echo   ⨽ removed !",
            ]
        script_path.write_text("\n".join(content), encoding="utf-8")
        exe = str(bash_path)
        # TODO: not sure we need the prefix
        argv = [prefix, str(script_path)]

    LOGGER.debug(f"os.execv({exe}, {argv})")

    sys.exit(os.execv(exe, argv))


def get_paths_to_uninstall(filesystem: HubLocalFilesystem) -> list[Path]:
    """
    Get all the paths that need to be removed to fully delete the hub from the local user system.

    Args:
        filesystem: collection of paths for storing runtime data

    Returns:
        list of existing filesystem path (files or directories).
    """
    to_uninstall = []

    hubrecord_path = filesystem.hubinstall_record_path
    hubrecord = HubInstallRecord.read_from_disk(hubrecord_path)
    paths = [hubrecord.installed_path] + [filesystem.root_dir]
    vendor_record_paths = hubrecord.vendors_record_paths
    vendor_record_paths = vendor_record_paths.values() if vendor_record_paths else []

    for vendorrecord_path in vendor_record_paths:
        vendorrecord = VendorInstallRecord.read_from_disk(vendorrecord_path)
        paths += [vendorrecord.installed_path] + vendorrecord.extra_paths

    for path in paths:
        if not path or not path.exists():
            continue
        to_uninstall.append(path)

    return to_uninstall


def uninstall_hub_only(hubinstall_file: HubInstallRecord):
    """
    Only uninstall the hub but not the vendors or additional paths.
    """
    installed_path = hubinstall_file.installed_path
    LOGGER.debug(f"rmtree('{installed_path}')")
    rmtree(installed_path)
