import abc
import logging
import time
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)


class BaseVendorInstaller(abc.ABC):
    """
    An abstract class defining how to install an external program.

    An installation directory is always provided but might not be used by the developer
    to store the actual program. However the directory is still used to specify that
    the program was installed.

    The version is an arbitrary text that is used in a binary fashion, meaning or the
    version installed on disk is similar to the instance, or both are different then
    the instance is always prioritized. In theory an user can't have a more recent
    version on disk than the one listed in the config.
    """

    def __init__(
        self,
        version: int,
        install_dir: Path,
        dirs_to_make: list[Path] = None,
    ):
        self._version = version
        self._install_dir = install_dir
        self._install_file = install_dir / ".installed"
        self._dirs_to_make = dirs_to_make or []

    def __str__(self):
        return f"{self.__class__.__name__}<v{self.version}>"

    def __lt__(self, other: "BaseVendorInstaller"):
        if not isinstance(other, BaseVendorInstaller):
            raise TypeError(
                f"Cannot compare '{other.__class__.__name__}' "
                f"with '{self.__class__.__name__}'"
            )
        return self.version < other.version

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        """
        Unique installer name across all installer subclasses.
        """
        pass

    @property
    def version(self) -> int:
        """
        Current version of the installer configuration.
        """
        return self._version

    @property
    def install_dir(self) -> Path:
        """
        Filesystem path to a directory that may not exist and used to install the vendor program to.
        """
        return self._install_dir

    @property
    def dirs_to_make(self) -> list[Path]:
        """
        List of filesystem path to directory that must be created on installation.
        """
        return self._dirs_to_make

    @property
    def is_installed(self) -> bool:
        """
        Returns:
            True if there is already an active install else False.
        """
        return True if self.time_installed else False

    @property
    def version_installed(self) -> Optional[int]:
        """
        Returns:
            a number that is incremented everytime an installer config change and
            allow to check if an existing installation need updating.
        """
        if self._install_file.exists():
            return int(self._install_file.read_text().split("=")[0])
        return None

    @property
    def time_installed(self) -> Optional[float]:
        """
        Returns:
            time in seconds since the Epoch at which the program was last installed,
            or None if never installed.
        """
        if self._install_file.exists():
            return float(self._install_file.read_text().split("=")[1])
        return None

    def set_install_completed(self):
        """
        To call at the end of the :meth:`install` method.
        """
        LOGGER.debug(f"writting '{self._install_file}'")
        self._install_file.write_text(f"{self._version}={time.time()}")

    def make_install_directories(self):
        """
        Create all the directories used for installation, given by the user.

        Usually manually called in the ``install`` method subclass override.
        """
        for dir_path in self._dirs_to_make + [self._install_dir]:
            if not dir_path.exists():
                LOGGER.debug(f"mkdir('{dir_path}')")
                dir_path.mkdir()

    @abc.abstractmethod
    def install(self):
        """
        Arbitrary process to install a program.

        Developer is responsible for calling :meth:`set_install_completed` at the end
        or to check if an existing install exist.
        """
        pass

    @abc.abstractmethod
    def uninstall(self):
        """
        Arbitrary process to uninstall a program.

        Developer is responsible for removing the "install file".
        """
        pass
