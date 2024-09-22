import dataclasses
import logging
from pathlib import Path
from typing import Union

from knots_hub import serializelib
from knots_hub.serializelib import UninitializedType


LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class HubInstallRecord:
    """
    A datastructure to manipulate the metadata stored along the local hub install.

    The datastructure can be serialized and unserialized from disk.
    """

    installed_time: Union[float, UninitializedType] = serializelib.FloatField()
    """
    Time since epoch at which the hub was last installed.
    """

    installed_version: Union[str, UninitializedType] = serializelib.StrField()
    """
    Currently installed version of the hub.
    """

    installed_path: Union[Path, UninitializedType] = serializelib.PathField()
    """
    Filesystem path to the installation directory of the hub.
    """

    vendors_record_paths: Union[dict[str, Path], UninitializedType] = (
        serializelib.DictOfStrNPathField()
    )
    """
    A mapping of vendor names installed, and their vendor installation record path.
    """

    @classmethod
    def read_from_disk(cls, path: Path) -> "HubInstallRecord":
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
