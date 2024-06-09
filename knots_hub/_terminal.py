import logging
import os
import shutil
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)


def get_default_powershell_terminal() -> List[str]:
    """
    Return a terminal that can open a .ps1 powershell script.

    Returns:
        list of command-line arguments.
    """
    # check if https://github.com/microsoft/terminal is installed
    windowsterminal_path = shutil.which("wt")
    if windowsterminal_path:
        # open a new tab in the first existing instance
        # https://learn.microsoft.com/en-gb/windows/terminal/command-line-arguments?tabs=windows#new-tab-command
        return [
            windowsterminal_path,
            "--window",
            "0",
            "new-tab",
            "--title",
            "knots-hub",
            "--profile",
            "Windows PowerShell",
        ]

    # else use standard builtin powershell
    return [shutil.which("powershell")]


def get_default_shell_terminal() -> List[str]:
    """
    Return a terminal that can open a .sh shell script.

    We assume on Linux all distros can execute it without anything specific.
    """
    return []


def is_terminal_context_powershell() -> bool:
    """
    Check if this python interpreter was executed from a powershell terminal.

    This function is intended to be called on Windows only.

    References:
        - [1] https://stackoverflow.com/a/55598796/13806195

    Returns:
        True if powershell else False
    """

    return len(os.getenv("PSModulePath", "").split(os.pathsep)) >= 3


def get_terminal_for_script(script_path: Path) -> List[str]:
    """
    Get a command that can open the given script file.

    The command is ready to be called and include the path to the file.

    Args:
        script_path: filesystem path to a script file that may not exist.

    Returns:
        list of command line arguments to open the given script
    """
    if script_path.suffix == ".ps1":
        if is_terminal_context_powershell():
            return [str(script_path)]
        return get_default_powershell_terminal() + [str(script_path)]
    elif script_path.suffix == ".sh":
        return get_default_shell_terminal() + [str(script_path)]
    else:
        raise TypeError(
            f"Unsupported file extension '{script_path.suffix}' for '{script_path}'."
        )
