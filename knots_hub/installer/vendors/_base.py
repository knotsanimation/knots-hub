import abc
import dataclasses
import hashlib
import logging
from pathlib import Path
from knots_hub import serializelib

LOGGER = logging.getLogger(__name__)


class VendorNameError(Exception):
    """
    The serialized representation is not for the expected vendor class.
    """

    pass


@dataclasses.dataclass
class BaseVendorInstaller(abc.ABC):
    """
    An abstract class defining how to install an external program.

    An instance represent the configuration in which to install the program.

    An installation directory is always provided but might not be used by the developer
    to store the actual program. However the directory is still used to specify that
    the program was installed.
    """

    install_dir: Path = serializelib.PathField(
        doc=(
            "filesystem path to a directory that may exists."
            "The parent directory must exist (use the ``dirs_to_make`` if the parent may not exist yet)."
            "The path can contains environment variable like *$ENVAR/foo* "
            "where the ``$`` can be escaped by doubling it like ``$$``."
        ),
        expandvars=True,
    )
    """
    Filesystem path to a directory that may not exist and used to install the vendor program to.
    """

    dirs_to_make: list[Path] = serializelib.PathListField(
        doc=(
            "optional list of filesystem path to directories that may exists."
            "Each directory will be created on install if it doesn't exist but each of their parent directory must exist. "
            "The path can contains environment variable like *$ENVAR/foo* "
            "where the ``$`` can be escaped by doubling it like ``$$``."
        ),
        expandvars=True,
    )
    """
    List of filesystem path to directory that must be created on installation.
    """

    def __str__(self):
        return f"VendorInstaller:{self.name()}-v{self.version()}"

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

    @classmethod
    @abc.abstractmethod
    def version(cls) -> int:
        """
        The version of the installer API.

        Any change in the code of the subclass imply to bump this version which should
        trigger an update on the user system.
        """
        pass

    @classmethod
    def unserialize(
        cls,
        serialized: str,
        context: serializelib.UnserializeContext,
    ) -> "BaseVendorInstaller":
        """
        Create a dataclass instance from a serialized string representation.

        Raises:
            VendorNameError:
                if the serialized string is not corresponding to this subclass.
                This is a pretty common issue.
        """

        def preprocess(src: dict) -> dict:
            subset = src.get(cls.name())
            if subset is None:
                raise VendorNameError(
                    f"Cannot found vendor name '{cls.name()}' among keys '{src.keys()}'"
                )
            return subset

        return serializelib.unserialize(
            serialized=serialized,
            data_class=cls,
            context=context,
            pre_process=preprocess,
        )

    @classmethod
    def get_documentation(cls) -> list[str]:
        """
        Get the documentation for the subclass as a list of lines.

        Returns:
            list of lines as valid .rst syntax.
        """
        doc = []
        for field in dataclasses.fields(cls):
            field_doc = serializelib.get_field_doc(field)
            field_type = serializelib.get_field_typehint(field)
            doc += [f"- ``{field.name}`` `({field_type})`: {field_doc}"]
        return doc

    @property
    def install_record_path(self) -> Path:
        """
        Get the path to the file used to store metadata about the installation.
        """
        return self.install_dir / ".vendorrecord"

    def get_hash(self) -> str:
        """
        Get a hash that allow to differenciate this instance against a previously installed one.
        """
        serialized = self.serialize() + self.name() + str(self.version())
        serialized = serialized.encode("utf-8")
        return hashlib.md5(serialized).hexdigest()

    def make_install_directories(self):
        """
        Create all the directories used for installation, given by the user.

        Usually manually called in the ``install`` method subclass override.
        """
        for dir_path in self.dirs_to_make + [self.install_dir]:
            if not dir_path.exists():
                LOGGER.debug(f"mkdir('{dir_path}')")
                dir_path.mkdir()

    def serialize(self) -> str:
        """
        Convert this instance to a serialized string representation.
        """

        def postprocess(src: dict) -> dict:
            return {self.name(): src}

        return serializelib.serialize(unserialized=self, post_process=postprocess)

    @abc.abstractmethod
    def install(self):
        """
        Arbitrary process to install a program.

        Developer is responsible for calling :meth:`set_install_completed` at the end
        or to check if an existing install exist.
        """
        pass
