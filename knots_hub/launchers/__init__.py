from pathlib import Path

from knots_hub.constants import OS

_THISDIR = Path(__file__).parent


def get_launcher_content() -> str:
    """
    Get the launcher script content for the current runtime OS.
    """
    if OS.is_windows():
        path = _THISDIR / "hub-launcher.ps1"
    else:
        path = _THISDIR / "hub-launcher.sh"
    return path.read_text("utf-8")
