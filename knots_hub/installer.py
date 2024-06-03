import dataclasses
import logging
import os
import shutil
import tempfile
from pathlib import Path

from pythonning.benchmark import timeit

from knots_hub.constants import Environ
from knots_hub.constants import OS
from knots_hub.constants import LOCAL_ROOT_FILESYSTEM
from ._installer import install_python
from ._installer import resolve_dependencies
from ._installer import create_venv
from ._installer import install_dependencies
from ._installer import are_requirements_files_similar

LOGGER = logging.getLogger(__name__)


class HubInstallFilesystem:
    """
    Represent the filestructure of a sucessfull hub installation.

    All paths listed are guaranteed to exist on disk.
    """

    def __init__(self, root: Path):
        self.root = root
        # XXX: some paths are used by the launcher scripts, kept them synced !
        self.venv_dir = root / ".venv"
        self.python_dir = root / "python"
        self.python_version_path = root / ".pythonversion"
        self.requirements_path = root / "resolved-requirements.txt"
        self.updating_dir = root / "__newupdate__"

    @property
    def updating_filesystem(self) -> "HubInstallFilesystem":
        return HubInstallFilesystem(self.updating_dir)

    @property
    def python_bin_path(self) -> Path:
        if OS.is_windows():
            return self.python_dir / "python.exe"
        else:
            return self.python_dir / "bin" / "python"

    @property
    def python_version(self) -> str:
        return self.python_version_path.read_text("utf-8")

    @property
    def is_updating(self) -> bool:
        """
        Returns:
            True if the hub is being updated with new a new python environment.
        """
        return self.updating_filesystem.root.exists()

    @classmethod
    def from_local_root(cls) -> "HubInstallFilesystem":
        return cls(root=LOCAL_ROOT_FILESYSTEM.install_dir)


@dataclasses.dataclass
class HubInstallConfig:
    """
    Options determining how the hub must be installed.
    """

    local_install_path: Path
    requirements_path: Path
    python_version: str

    @classmethod
    def from_environment(cls) -> "HubInstallConfig":
        """
        Generate an instance from environment variables.
        """

        kwargs_by_envvar = {
            # keys are dataclass field names
            # values are ("env var name", "env var value casting")
            "local_install_path": (
                Environ.USER_INSTALL_PATH,
                Path,
            ),
            "requirements_path": (
                Environ.INSTALLER_REQUIREMENTS_PATH,
                Path,
            ),
            "python_version": (
                Environ.PYTHON_VERSION,
                str,
            ),
        }

        kwargs = {}

        for kwarg, config in kwargs_by_envvar.items():
            envvar_name, casting = config
            envvar = os.getenv(envvar_name)
            if not envvar:
                raise EnvironmentError(f"Missing '{envvar_name}' environment variable.")
            kwargs[kwarg] = casting(envvar)

        return HubInstallConfig(**kwargs)


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
    # check if hub is not already installed locally
    if local_install_path.exists():
        return False

    # install to local system
    # we first install into a temp dir that can be easily destroyed on error, and then
    # copy it to the intended location.

    with tempfile.TemporaryDirectory(prefix="knots_hub_installer_") as tmpdir:
        filesystem = HubInstallFilesystem(root=Path(tmpdir))

        python_version = python_version

        LOGGER.info(f"writting '{filesystem.python_version_path}'")
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

        if dryrun:
            return True

        LOGGER.info(f"copying installation from temp dir to user location")
        with timeit("copying took ", LOGGER.debug):
            shutil.copytree(tmpdir, local_install_path)

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
