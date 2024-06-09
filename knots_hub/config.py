import dataclasses
import logging
import os
import shlex
from pathlib import Path
from typing import List

from knots_hub.constants import Environ

LOGGER = logging.getLogger(__name__)


def _cast_command_line_args(src: str) -> List[str]:
    return shlex.split(src)


@dataclasses.dataclass
class HubConfig:
    """
    Options determining how the hub must be installed.
    """

    local_install_path: Path = dataclasses.field(
        metadata={
            "documentation": "",
            "environ": Environ.USER_INSTALL_PATH,
            "environ_cast": Path,
            "environ_required": True,
        }
    )
    requirements_path: Path = dataclasses.field(
        metadata={
            "documentation": "",
            "environ": Environ.INSTALLER_REQUIREMENTS_PATH,
            "environ_cast": Path,
            "environ_required": True,
        }
    )
    python_version: str = dataclasses.field(
        metadata={
            "documentation": "",
            "environ": Environ.PYTHON_VERSION,
            "environ_cast": str,
            "environ_required": True,
        }
    )
    terminal_windows: List[str] = dataclasses.field(
        default_factory=list,
        metadata={
            "documentation": (
                "A command line that can execute .ps1 powershell script. "
                "It is being appened the path to the script.\n\n"
                "If specified from an environment variable, the value is converted to "
                "a list of str using ``shlex.split``."
            ),
            "environ": Environ.TERMINAL_WINDOWS,
            "environ_cast": _cast_command_line_args,
            "environ_required": False,
        },
    )
    terminal_linux: List[str] = dataclasses.field(
        default_factory=list,
        metadata={
            "documentation": (
                "A command line that can execute .sh shell script. "
                "It is being appened the path to the script.\n\n"
                "If specified from an environment variable, the value is converted to "
                "a list of str using ``shlex.split``."
            ),
            "environ": Environ.TERMINAL_LINUX,
            "environ_cast": _cast_command_line_args,
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
