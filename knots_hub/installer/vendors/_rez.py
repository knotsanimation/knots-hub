import dataclasses
import logging
import shutil
import subprocess
from pathlib import Path

from pythonning.benchmark import timeit
from pythonning.progress import catch_download_progress
from pythonning.web import download_file
from pythonning.filesystem import extract_zip

from knots_hub import OS
from knots_hub import serializelib
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
    result = subprocess.run(
        rez_command,
        check=True,
        capture_output=True,
        text=True,
    )
    LOGGER.debug(f"subprocess[stdout]={result.stdout}")
    LOGGER.debug(f"subprocess[stderr]={result.stderr}")
    shutil.rmtree(rez_tmp_dir)
    if OS.is_windows():
        return target_dir / "Scripts" / "rez" / "rez.exe"
    else:
        return target_dir / "bin" / "rez" / "rez"


@dataclasses.dataclass
class RezVendorInstaller(BaseVendorInstaller):
    python_version: str = serializelib.StrField(
        doc="a full valid python version to install rez with"
    )
    rez_version: str = serializelib.StrField(
        doc="a full valid rez version to install from the official GitHub repo."
    )

    @classmethod
    def name(cls) -> str:
        return "rez"

    @classmethod
    def version(cls) -> int:
        return 2

    def install(self):

        self.make_install_directories()

        python_dir = self.install_dir / "python"
        python_dir.mkdir()

        # rez has its dedicated python interpreter for proper isolation
        LOGGER.info(f"installing python-{self.python_version}")
        with timeit("python installation took ", LOGGER.info):
            python_exe = install_python(
                python_version=self.python_version,
                target_dir=python_dir,
            )

        rez_dir = self.install_dir / "rez"
        rez_dir.mkdir()

        LOGGER.info(f"installing rez-{self.version()}")
        with timeit("rez installation took ", LOGGER.info):
            rez_exe = install_rez(
                rez_version=self.rez_version,
                target_dir=rez_dir,
                python_executable=python_exe,
            )
