import dataclasses
import logging
from pathlib import Path
from knots_hub import serializelib


LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class VendorInstallRecord:
    """
    A datastructure to record how a vendor was installed on the local system.

    The datastructure can be serialized and unserialized from disk.
    """

    name: str = serializelib.StrField()
    """
    Name of the vendor that is installed.
    """

    installed_time: float = serializelib.FloatField()
    """
    Time since epoch at which the vendor was last installed.
    """

    install_hash: str = serializelib.StrField()
    """
    A hash to validate if the current install is up to date.
    """

    installed_path: Path = serializelib.PathField()
    """
    Filesystem path to the installation directory of the vendor.    
    """

    extra_paths: list[Path] = serializelib.PathListField()
    """
    A list of extra paths created for the install of the vendor.
    
    They need to be removed on uninstallation.
    """

    @classmethod
    def read_from_disk(cls, path: Path) -> "VendorInstallRecord":
        """
        Create an instance from a serialized disk file.

        Args:
            path: filesystem path to an existing file
        """
        return serializelib.read_from_disk(cls, path=path)

    def write_to_disk(self, path: Path):
        """
        Write this instance as a serialized disk file.
        """
        return serializelib.write_to_disk(self, path=path)

    def update_disk(self, path: Path):
        """
        Write this instance as a serialized disk file, updating if the file already exists.

        Updating means only writing non-Uninitialized value of this instance.
        """
        return serializelib.update_disk(self, path=path)
