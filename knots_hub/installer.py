import logging
import shutil
import tempfile
import time
from pathlib import Path

import pythonning.filesystem
from pythonning.benchmark import timeit

from knots_hub.constants import INSTALLER_TEMP_DIR_PREFIX
from .filesystem import HubInstallFilesystem
from ._installer import install_python
from ._installer import resolve_dependencies
from ._installer import create_venv
from ._installer import install_dependencies
from ._installer import are_requirements_files_similar
from .launchers import get_launcher_content

LOGGER = logging.getLogger(__name__)


def _install_dependencies(
    python_bin_path: Path,
    venv_dir: Path,
    src_requirements_path: Path,
    dst_requirements_path: Path,
):
    LOGGER.info(f"creating venv at '{venv_dir}'")
    with timeit("venv creation took ", LOGGER.debug):
        create_venv(
            python_bin_path=python_bin_path,
            venv_path=venv_dir,
        )

    LOGGER.info(f"resolving dependencies to '{dst_requirements_path}'")
    with timeit("dependencies resolving took ", LOGGER.debug):
        resolve_dependencies(
            python_bin_path=python_bin_path,
            dependencies_path=src_requirements_path,
            target_path=dst_requirements_path,
        )

    LOGGER.info(f"installing dependencies into the venv")
    with timeit("dependencies installation took ", LOGGER.debug):
        install_dependencies(
            python_bin_path=python_bin_path,
            dependencies_path=dst_requirements_path,
            venv_path=venv_dir,
        )


def create_temp_launcher(current_launcher_path: Path) -> Path:
    """
    Duplicate the given launcher at a temporary location.

    We leave the user of this function responsability of cleaning the temp directory.

    Args:
        current_launcher_path: filesystem path to an existing launcher file.

    Returns:
        filesystem path to the new launcher file
    """
    tmpdir = Path(tempfile.mkdtemp(prefix=INSTALLER_TEMP_DIR_PREFIX))
    new_launcher_path = tmpdir / current_launcher_path.name
    shutil.copy(current_launcher_path, new_launcher_path)
    return new_launcher_path


def install_hub(
    local_install_path: Path,
    requirements_path: Path,
    python_version: str,
    dryrun: bool = False,
) -> bool:
    """
    Args:
        local_install_path: filesystem path to a directory that may not exist
        requirements_path: filesystem path to an existing requirements.txt file
        python_version: full python interpreter version to use for installation
        dryrun: True to only write to a temporary location that is removed on function exit.

    Returns:
        True if the hub was installed for the first time else False
    """
    filesystem = HubInstallFilesystem(root=local_install_path)
    # check if hub is not already installed locally
    if filesystem.hubinstall_path.exists():
        return False

    # install to local system
    # we first install into a temp dir that can be easily destroyed on error, and then
    # copy it to the intended location.

    with tempfile.TemporaryDirectory(prefix=INSTALLER_TEMP_DIR_PREFIX) as tmpdir:
        filesystem = HubInstallFilesystem(root=Path(tmpdir))

        python_version = python_version

        LOGGER.info(f"writing '{filesystem.python_version_path}'")
        filesystem.python_version_path.write_text(python_version, "utf-8")

        LOGGER.info(f"installing python-{python_version} to '{filesystem.python_dir}'")
        with timeit("python installing took ", LOGGER.debug):
            filesystem.python_dir.mkdir()
            python_path = install_python(
                python_version=python_version,
                target_dir=filesystem.python_dir,
            )
        assert python_path == filesystem.python_bin_path

        _install_dependencies(
            python_bin_path=filesystem.python_bin_path,
            venv_dir=filesystem.venv_dir,
            src_requirements_path=requirements_path,
            dst_requirements_path=filesystem.requirements_path,
        )

        install_hub_launcher(filesystem.launcher_path)

        LOGGER.info(f"writing '{filesystem.hubinstall_path}'")
        filesystem.hubinstall_path.write_text(str(time.time()), "utf-8")

        if dryrun:
            return True

        LOGGER.info(f"moving installation from temp dir to user location")
        with timeit("installation move took ", LOGGER.debug):
            pythonning.filesystem.move_directory_content(
                Path(tmpdir), local_install_path
            )

    return True


def install_hub_launcher(launcher_path: Path) -> bool:
    """
    Create the hub's launcher if it doesn't exist.

    The launcher path is OS-dependent.

    Args:
        launcher_path: filesystem path to a file that might exist.

    Returns:
        True if the launcher was installed for the first time else False
    """
    if launcher_path.exists():
        return False

    launcher_content = get_launcher_content()
    LOGGER.info(f"writing '{launcher_path}'")
    launcher_path.write_text(launcher_content, "utf-8")
    return True


def update_hub(
    local_install_path: Path,
    requirements_path: Path,
    python_version: str,
) -> bool:
    """
    Args:
        local_install_path: filesystem path to a directory that may not exist
        requirements_path: filesystem path to an existing requirements.txt file
        python_version: full python interpreter version to use for installation

    Returns:
        True if an update was performed or False if untouched.
    """
    if not local_install_path.exists():
        return False

    filesystem = HubInstallFilesystem(root=local_install_path)
    filesystem.updating_filesystem.root.mkdir(exist_ok=True)

    latest_python = python_version
    current_python = filesystem.python_version
    need_python_update = current_python != latest_python

    latest_requirements_path = requirements_path
    current_requirements_path = filesystem.requirements_path
    need_dependencies_update = are_requirements_files_similar(
        ref_path=latest_requirements_path,
        src_path=current_requirements_path,
    )

    new_python_bin_path = filesystem.python_bin_path

    updated = False

    if need_python_update:
        new_python_dir = filesystem.updating_filesystem.python_dir

        LOGGER.info(f"updating python {current_python} to {latest_python}")
        with timeit("python installing took", LOGGER.debug):
            python_path = install_python(
                python_version=latest_python,
                target_dir=new_python_dir,
            )
            assert python_path == filesystem.updating_filesystem.python_bin_path

        new_python_bin_path = filesystem.updating_filesystem.python_bin_path
        updated = True

    if need_dependencies_update:
        new_venv_dir = filesystem.updating_filesystem.venv_dir
        new_requirements_path = filesystem.updating_filesystem.requirements_path

        LOGGER.info(f"updating dependencies with '{new_requirements_path}'")
        _install_dependencies(
            python_bin_path=new_python_bin_path,
            venv_dir=new_venv_dir,
            src_requirements_path=latest_requirements_path,
            dst_requirements_path=new_requirements_path,
        )
        updated = True

    if not updated:
        # no update means its empty
        filesystem.updating_filesystem.root.rmdir()

    return updated
