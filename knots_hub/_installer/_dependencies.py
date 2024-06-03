import logging
import os
import subprocess
from pathlib import Path

import uv

from knots_hub.utils import log_subprocess_result

LOGGER = logging.getLogger(__name__)

UV_PATH: str = uv.find_uv_bin()


def are_requirements_files_similar(ref_path: Path, src_path: Path) -> bool:
    """
    Args:
        ref_path: filesystem path to an existing requirements.txt file
        src_path: filesystem path to an existing requirements.txt file

    Returns:
        True if the 2 file have the same dependencies listing
    """
    ref_content = ref_path.read_text("utf-8").split("\n")
    ref_content = sorted([line for line in ref_content if not line.startswith("#")])

    src_content = src_path.read_text("utf-8").split("\n")
    src_content = sorted([line for line in src_content if not line.startswith("#")])
    return src_content == ref_content


def resolve_dependencies(
    python_bin_path: Path,
    dependencies_path: Path,
    target_path: Path,
) -> Path:
    """
    Resolve the given dependencies to a more restrictive list of dependencies.

    Args:
        python_bin_path: filesystem path to an existing python interpreter executable
        dependencies_path: a "requirements" file as supported by ``uv``
        target_path: filesystem path to a file to write the resolved dependencies to

    Returns:
        the ``target_path`` argument
    """
    result = subprocess.run(
        [
            UV_PATH,
            "pip",
            "compile",
            str(dependencies_path),
            "-o",
            str(target_path),
            "--python",
            python_bin_path,
            "--verbose",
        ],
        env=None,
        cwd=target_path.parent,
        check=True,
        capture_output=True,
    )
    log_subprocess_result(result, logger=LOGGER.debug)
    return target_path


def create_venv(python_bin_path: Path, venv_path: Path):
    """
    Create a pyton virtual environement at the given location.

    Args:
        python_bin_path: filesystem path to an existing python interpreter executable
        venv_path: filesystem path to a directory that might exist
    """
    result = subprocess.run(
        [
            UV_PATH,
            "venv",
            "--verbose",
            "--python",
            str(python_bin_path),
            str(venv_path),
        ],
        env=None,
        cwd=venv_path.parent,
        check=True,
        capture_output=True,
    )
    log_subprocess_result(result, logger=LOGGER.debug)


def install_dependencies(
    python_bin_path: Path,
    venv_path: Path,
    dependencies_path: Path,
):
    """
    Install the dependencies in the given virtual environment.

    It is recommended for the virtual environment to be freshly created.

    Args:
        python_bin_path:  filesystem path to an existing python interpreter executable
        dependencies_path: a ``requirements.txt`` file as supported by ``uv``
        venv_path: filesystem path to an existing directory where the virtual environment must be installed.
    """
    environ = os.environ.copy()
    environ["VIRTUAL_ENV"] = str(venv_path)
    result = subprocess.run(
        [
            UV_PATH,
            "pip",
            "install",
            "-r",
            str(dependencies_path),
            "--python",
            str(python_bin_path),
            "--verbose",
        ],
        env=environ,
        cwd=venv_path,
        check=True,
        capture_output=True,
    )
    log_subprocess_result(result, logger=LOGGER.debug)
