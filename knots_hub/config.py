"""
A simple configuration system for the Knots-hub runtime.
"""

import dataclasses
import logging
import os
from pathlib import Path
from typing import Optional

from knots_hub.constants import Environ

LOGGER = logging.getLogger(__name__)


def _cast_path_list(value) -> list[Path]:
    return [Path(path) for path in value.split(os.pathsep)]


@dataclasses.dataclass
class HubConfig:
    """
    Options determining how the hub must be installed.
    """

    local_install_path: Path = dataclasses.field(
        metadata={
            "documentation": (
                "Filesystem path to a directory that may exist, "
                "used to store all the filesystem data for the hub."
            ),
            "environ": Environ.USER_INSTALL_PATH,
            "environ_cast": Path,
            "environ_required": True,
        }
    )
    installer_list_path: Optional[Path] = dataclasses.field(
        default=None,
        metadata={
            "documentation": (
                "Filesystem path to an existing json file used to store a mapping of "
                "`hub version`: `installer path`. The `installer path` can be a directory"
                "or a zip archive."
            ),
            "environ": Environ.INSTALLER_LIST_PATH,
            "environ_cast": Path,
            "environ_required": False,
        },
    )
    vendor_installer_config_paths: list[Path] = dataclasses.field(
        default_factory=list,
        metadata={
            "documentation": (
                "Filesystem path to an existing json file used to specify which "
                "external program to install with which version."
            ),
            "environ": Environ.VENDOR_INSTALLER_CONFIG_PATHS,
            "environ_cast": _cast_path_list,
            "environ_required": False,
        },
    )

    @classmethod
    def from_environment(cls) -> "HubConfig":
        """
        Generate an instance from environment variables.
        """
        kwargs = {}

        for field in dataclasses.fields(cls):
            envvar_name = field.metadata["environ"]
            envvar_casting = field.metadata["environ_cast"]
            envvar_required = field.metadata["environ_required"]
            envvar = os.getenv(envvar_name)
            if envvar:
                kwargs[field.name] = envvar_casting(envvar)
            elif not envvar and envvar_required:
                raise EnvironmentError(f"Missing '{envvar_name}' environment variable.")

        return HubConfig(**kwargs)
