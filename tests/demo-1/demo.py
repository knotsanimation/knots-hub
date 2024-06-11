import os
import tempfile
from pathlib import Path

import knots_hub.__main__
from knots_hub.constants import Environ

THISDIR = Path(__file__).parent

tmpdir = Path(tempfile.mkdtemp(prefix="knots_hub_demo_"))
print(f"saving content to '{tmpdir}'")

os.environ[Environ.USER_INSTALL_PATH] = str(tmpdir / "install")
# os.environ[Environ.INSTALLER_LIST_PATH] = ""
knots_hub.__main__.main(argv=["--debug", "__applyupdate", "1"])
