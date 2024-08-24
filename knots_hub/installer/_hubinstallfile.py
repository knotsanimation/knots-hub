import dataclasses
import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class Uninitialized:
    def __bool__(self):
        return False


def _serialize_path_list(src) -> list[str]:
    return [str(path) for path in src]


def _unserialize_path_list(src) -> list[Path]:
    return [Path(path) for path in src]


def serializer(caster):
    def _inner(value):
        if value is Uninitialized:
            return "<%Uninitialized%>"
        return caster(value)

    return _inner


def unserializer(caster):
    def _inner(value):
        if value == "<%Uninitialized%>":
            return Uninitialized
        return caster(value)

    return _inner


@dataclasses.dataclass
class HubInstallFile:
    """
    A datastructure to manipulate the metadata stored along the local hub install.

    The datastructure can be serialized and unserialized from disk.
    """

    installed_time: float = dataclasses.field(
        metadata={
            "serialize": serializer(float),
            "unserialize": unserializer(float),
        },
        default=Uninitialized,
    )
    """
    Time since epoch at which the hub was last installed.
    """

    installed_version: str = dataclasses.field(
        metadata={
            "serialize": serializer(str),
            "unserialize": unserializer(str),
        },
        default=Uninitialized,
    )
    """
    Currently installed version of the hub.
    """

    installed_path: Path = dataclasses.field(
        metadata={
            "serialize": serializer(str),
            "unserialize": unserializer(Path),
        },
        default=Uninitialized,
    )
    """
    Filesystem path to the installation directoryof the hub.
    """

    additional_paths: list[Path] = dataclasses.field(
        metadata={
            "serialize": serializer(_serialize_path_list),
            "unserialize": unserializer(_unserialize_path_list),
        },
        default=Uninitialized,
    )
    """
    Additional filesystem location created for the installation.
    """

    @classmethod
    def read_from_disk(cls, path: Path) -> "HubInstallFile":
        """
        Create an instance from a serialized disk file.
        """
        with path.open("r", encoding="utf-8") as file:
            content = json.load(file)

        kwargs = {}
        for field in dataclasses.fields(cls):
            caster = field.metadata["unserialize"]
            kwargs[field.name] = caster(content[field.name])

        return cls(**kwargs)

    def write_to_disk(self, path: Path):
        """
        Write this instance as a serialized disk file.
        """
        content = {}

        for field in dataclasses.fields(self):
            caster = field.metadata["serialize"]
            value = getattr(self, field.name)
            content[field.name] = caster(value)

        with path.open("w", encoding="utf-8") as file:
            json.dump(content, file, indent=4, sort_keys=True)

    def update_disk(self, path: Path):
        """
        Write this instance as a serialized disk file, updating if the file already exists.

        Updating means only writing non-Uninitialized value of this instance.
        """
        if path.exists():
            new = self.read_from_disk(path)
            for field in dataclasses.fields(self):
                value = getattr(self, field.name)
                if value is not Uninitialized:
                    setattr(new, field.name, value)
        else:
            new = self

        new.write_to_disk(path)
