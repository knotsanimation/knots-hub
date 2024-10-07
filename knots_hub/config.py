"""
A simple configuration system for the Knots-hub runtime.
"""

import dataclasses
import logging
import os
from pathlib import Path
from typing import Any
from typing import Optional

from knots_hub.constants import Environ

LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class HubInstallerConfig:
    """
    Configuration indicating how to install the hub.
    """

    version: str
    path: Path


def _cast_path_list(value) -> list[Path]:
    return [Path(path) for path in value.split(os.pathsep)]


def _cast_installerconfig(value: str) -> HubInstallerConfig:
    try:
        version, path = value.split("=", 1)
    except:
        LOGGER.error(f"cannot parse value '{value}' to HubInstallerConfig")
        raise
    return HubInstallerConfig(version=version, path=Path(path))


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
    installer: Optional[HubInstallerConfig] = dataclasses.field(
        default=None,
        metadata={
            "documentation": (
                "A string providing configuration for the hub installation."
                "The string is formatted as ``version=path``, where path is a fileystem"
                "path to an existing directory containing the hub to install, and version"
                "being the version of the hub corresponding to the path. The version is"
                "an arbitrary chain of character, usually following semver conventions,"
                "that is just used to check if the last locally installed version match"
                "the current installer version."
            ),
            "environ": Environ.INSTALLER,
            "environ_cast": _cast_installerconfig,
            "environ_required": False,
        },
    )
    vendor_installer_config_paths: list[Path] = dataclasses.field(
        default_factory=list,
        metadata={
            "documentation": (
                "Filesystem path to one or multiple existing json file used to specify which "
                "external program to install with which version."
                "If specified from an environment variable the list of paths is"
                "separated by the system path separator character."
            ),
            "environ": Environ.VENDOR_INSTALLER_CONFIG_PATHS,
            "environ_cast": _cast_path_list,
            "environ_required": False,
        },
    )

    skip_local_check: bool = dataclasses.field(
        default=False,
        metadata={
            "documentation": (
                "Disable the check verifying if the app is directly launched from "
                "the server or locally."
                "Any non-empty value in the environment variable will disable it."
            ),
            "environ": Environ.DISABLE_LOCAL_CHECK,
            "environ_cast": bool,
            "environ_required": False,
        },
    )

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

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
