import logging
import shutil
import subprocess
from pathlib import Path

from pythonning.progress import catch_download_progress
from pythonning.web import download_file
from pythonning.filesystem import move_directory_content

from knots_hub import OS

LOGGER = logging.getLogger(__name__)
NUGET_URL = "https://dist.nuget.org/win-x86-commandline/latest/nuget.exe"


def _install_python_windows(
    python_version: str,
    target_dir: Path,
) -> Path:
    url = NUGET_URL
    nuget_path = target_dir / "__nuget.exe"

    LOGGER.info(f"downloading '{url}' to '{nuget_path}' ...")
    with catch_download_progress() as progress:
        download_file(
            url=url,
            target_file=nuget_path,
            step_callback=progress.show_progress,
        )

    nugest_install_dir = target_dir / "__python.tmp"
    nuget_command = [
        str(nuget_path),
        "install",
        "python",
        "-OutputDirectory",
        str(nugest_install_dir),
        "-Version",
        python_version,
    ]
    LOGGER.debug(f"downloading python-{python_version} to {nugest_install_dir}")
    LOGGER.debug(f"subprocess.run({nuget_command})")
    subprocess.run(nuget_command, check=True)

    nuget_path.unlink()

    python_src_dir = nugest_install_dir / f"python.{python_version}" / "tools"
    LOGGER.debug(f"move_directory_content{python_src_dir}, {target_dir})")
    move_directory_content(python_src_dir, target_dir)
    shutil.rmtree(nugest_install_dir)

    if OS.is_windows():
        python_bin_path = target_dir / "python.exe"
    else:
        python_bin_path = target_dir / "bin" / "python"

    assert python_bin_path.exists(), python_bin_path
    return python_bin_path


def install_python(
    python_version: str,
    target_dir: Path,
):
    """
    Create a python interpreter of the given version at the given location.

    Args:
        python_version: full python version to install
        target_dir: filesystem path to an empty directory

    Returns:
        filesystem path to the python executable
    """
    if OS.is_windows():
        return _install_python_windows(
            python_version=python_version,
            target_dir=target_dir,
        )
    else:
        OS.raise_unsupported()
