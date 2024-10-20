import dataclasses
import logging

from ._base import BaseVendorInstaller


LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class KnotsVendorInstaller(BaseVendorInstaller):
    """
    "Meta" kind vendor which install whatever is needed for the downstream pipeline.
    """

    @classmethod
    def name(cls) -> str:
        return "knots"

    @classmethod
    def version(cls) -> int:
        return 1

    def install(self):
        # the current implementation just need the Base install_dir to be created
        #   which is handled by this method:
        self.make_install_directories()

    @classmethod
    def get_documentation(cls) -> list[str]:
        doc = super().get_documentation()
        return [cls.__doc__, ""] + doc
