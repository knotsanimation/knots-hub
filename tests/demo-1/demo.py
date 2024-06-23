import os
import tempfile
from pathlib import Path

import knots_hub.__main__
from knots_hub.constants import Environ

THISDIR = Path(__file__).parent

with tempfile.TemporaryDirectory(prefix="knots_hub_demo_") as tmpdir:
    tmpdir = Path(tmpdir)
    print(f"saving content to '{tmpdir}'")
    os.environ[Environ.USER_INSTALL_PATH] = str(tmpdir / "install")
    # os.environ[Environ.INSTALLER_LIST_PATH] = ""
    knots_hub.__main__.main(argv=["kloch", "plugins", "--debug"])
