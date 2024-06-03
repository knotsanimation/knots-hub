import logging
import shutil
import subprocess
from pathlib import Path

from pythonning.web import download_file
from pythonning.progress import catch_download_progress
from pythonning.benchmark import timeit
from pythonning.filesystem import move_directory_content

from knots_hub.constants import OS
from knots_hub.utils import log_subprocess_result

LOGGER = logging.getLogger(__name__)


def _install_python_windows(python_version: str, target_dir: Path) -> Path:
    """
    Use nuget to install a standalone python interpreter at the given location.

    Args:
        python_version:
        target_dir: filesystem path to an existing empty directory

    Returns:
        filesystem path to the existing python executable downloaded.
    """

    url = "https://dist.nuget.org/win-x86-commandline/latest/nuget.exe"
    nuget_path = target_dir / "nuget.exe"

    LOGGER.info(f"downloading nuget '{url}' to '{nuget_path}'")
    with timeit("download_file(nuget) took ", LOGGER.debug):
        with catch_download_progress() as progress:
            download_file(
                url=url,
                target_file=nuget_path,
                step_callback=progress.show_progress,
            )

    nugest_install_dir = target_dir / "python"
    nuget_command = [
        str(nuget_path),
        "install",
        "python",
        "-OutputDirectory",
        str(nugest_install_dir),
        "-Version",
        python_version,
    ]
    LOGGER.info(f"downloading 'python-{python_version}' to '{nugest_install_dir}'")
    with timeit("subprocess.run(nuget, python) took ", LOGGER.debug):
        result = subprocess.run(nuget_command, check=True, capture_output=True)

    log_subprocess_result(result, logger=LOGGER.debug)

    with timeit("install finaling took ", LOGGER.debug):
        nuget_path.unlink()

        python_src_dir = nugest_install_dir / f"python.{python_version}" / "tools"
        LOGGER.debug(f"moving downloaded python at the expected location")
        move_directory_content(python_src_dir, target_dir)

        LOGGER.debug(f"cleaning nuget left-over files")
        shutil.rmtree(nugest_install_dir)

    return target_dir / "python.exe"


def install_python(python_version: str, target_dir: Path) -> Path:
    """
    Download and install a standalone isolate python interpreter in the given dir.

    Args:
        python_version:
            a full or partial python version.
            partial python version resolve to the latest version available.
            Example: "3.9" or "3.9.19"
        target_dir: filesystem path to an existing empty directory

    Returns:
        path to the python interpreter file located in the ``target_dir``
    """
    if OS.is_windows():
        python_bin_path = _install_python_windows(python_version, target_dir)
    else:
        raise OSError(f"Unsupported OS {OS}")

    return python_bin_path
