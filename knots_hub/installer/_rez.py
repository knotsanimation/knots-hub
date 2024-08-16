import logging
import shutil
import subprocess
from pathlib import Path

from pythonning.benchmark import timeit
from pythonning.progress import catch_download_progress
from pythonning.web import download_file
from pythonning.filesystem import extract_zip

from knots_hub import OS
from ._base import BaseVendorInstaller
from ._python import install_python

LOGGER = logging.getLogger(__name__)

REZ_BASE_URL = "https://github.com/AcademySoftwareFoundation/rez/archive/refs/tags/{rez_version}.zip"


def install_rez(
    rez_version: str,
    python_executable: Path,
    target_dir: Path,
) -> Path:
    """
    Create a rez installation with the given configuration.

    Args:
        rez_version: full rez version to download from GitHub
        python_executable: filesystem path to the python executable to install rez with.
        target_dir: filesystem path to an empty existing directory

    Returns:
        filesystem path to the rez executable in the ``target_dir``.
    """
    rez_url = REZ_BASE_URL.format(rez_version=rez_version)
    rez_tmp_dir = target_dir / "__installer"
    rez_tmp_dir.mkdir()
    rez_zip_path = target_dir / "rez.zip"

    LOGGER.info(f"downloading '{rez_url}' to '{rez_zip_path}' ...")
    with catch_download_progress() as progress:
        download_file(
            url=rez_url,
            target_file=rez_zip_path,
            step_callback=progress.show_progress,
        )

    rez_root = extract_zip(zip_path=rez_zip_path, remove_zip=True)
    rez_installer_path = rez_root / f"rez-{rez_version}" / "install.py"
    rez_command = [
        str(python_executable),
        str(rez_installer_path),
        str(target_dir),
    ]
    LOGGER.debug(f"subprocess.run({rez_command})")
    subprocess.run(rez_command, check=True)
    shutil.rmtree(rez_tmp_dir)
    if OS.is_windows():
        return target_dir / "Scripts" / "rez" / "rez.exe"
    else:
        return target_dir / "bin" / "rez" / "rez"


class RezVendorInstaller(BaseVendorInstaller):

    def __init__(
        self,
        python_version: str,
        rez_version: str,
        version: int,
        install_dir: Path,
        dirs_to_make: list[Path] = None,
    ):
        self._python_version = python_version
        self._rez_version = rez_version
        super().__init__(
            version=version,
            install_dir=install_dir,
            dirs_to_make=dirs_to_make,
        )

    @classmethod
    def name(cls) -> str:
        return "rez"

    def install(self):

        if self.is_installed:
            return

        self.make_install_directories()

        python_dir = self._install_dir / "python"
        python_dir.mkdir()

        # rez has its dedicated python interpreter for proper isolation
        LOGGER.info(f"installing python-{self._python_version}")
        with timeit("python installation took ", LOGGER.info):
            python_exe = install_python(
                python_version=self._python_version,
                target_dir=python_dir,
            )

        rez_dir = self._install_dir / "rez"
        rez_dir.mkdir()

        LOGGER.info(f"installing rez-{self._version}")
        with timeit("rez installation took ", LOGGER.info):
            rez_exe = install_rez(
                rez_version=self._rez_version,
                target_dir=rez_dir,
                python_executable=python_exe,
            )

        self.set_install_completed()

    def uninstall(self):
        LOGGER.info(f"removing '{self._install_dir}'")
        shutil.rmtree(self._install_dir)
