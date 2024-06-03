import os
import tempfile
from pathlib import Path

import knots_hub.__main__

THISDIR = Path(__file__).parent

tmpdir = Path(tempfile.mkdtemp(prefix="knots_hub_demo_"))
print(f"saving content to '{tmpdir}'")

os.environ["KNOTSHUB_USER_INSTALL_PATH"] = str(tmpdir / "install")
os.environ["KNOTSHUB_INSTALLER_REQUIREMENTS_PATH"] = str(THISDIR / "requirements.txt")
os.environ["KNOTSHUB_PYTHON_VERSION"] = "3.10.11"
knots_hub.__main__.main(argv=["--debug"])
