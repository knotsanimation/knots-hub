import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import knots_hub
import knots_hub.__main__

LOGGER = logging.getLogger(__name__)

THISDIR = Path(__file__).parent


def mk_vendor_config(target_path: Path):
    content = {
        "rez": {
            "install_dir": "$KHUB_VENDOR_REZ_ROOT",
            "dirs_to_make": ["$KHUB_VENDOR_INSTALL_ROOT"],
            "python_version": "3.10.11",
            "rez_version": "2.113.0",
        },
        "knots": {
            "install_dir": "$KHUB_KNOTS_PATH",
            "dirs_to_make": [],
        },
    }
    print(f"creating vendor config '{target_path}'")
    with target_path.open("w") as file:
        json.dump(content, file, indent=4)


def mk_shortcut(target_path: Path):
    shortcut_script = Path(__file__).parent / "create-windows-shortcut.ps1"
    reference_path = sys.executable
    arguments = '"-m knots_hub"'
    command = [
        "powershell",
        str(shortcut_script),
        str(target_path),
        reference_path,
        arguments,
    ]
    print(f"creating shortcut '{target_path}'")
    print(f"subprocess.run({command})")
    subprocess.run(command, check=True)
    assert target_path.exists()


def get_hub_calls(argv: list[str]) -> list[list[str]]:
    """
    Return the different block of successive hub command to call.

    Blocks are pipe (``|``) separated arguments.
    """
    blocks = [[]]
    index = 0
    for arg in argv:
        if "|" in arg:
            index += 1
            blocks.append([])
            continue
        blocks[index].append(arg)

    return blocks


def main(tmpdir: Path):

    installers_path = tmpdir / "serverinstalls"
    installers_path.mkdir()
    last_installer_path = installers_path / "last"
    last_installer_path.mkdir()
    exe_path = last_installer_path / f"{knots_hub.constants.EXECUTABLE_NAME}.lnk"
    mk_shortcut(exe_path)

    user_install_path = tmpdir / "userinstall"
    vendor_install_config_path = tmpdir / "vendorinstallers.json"
    mk_vendor_config(vendor_install_config_path)

    vendor_install_path = tmpdir / "vendorinstall"
    vendor_rez_path = vendor_install_path / "rez"
    runtime_path = tmpdir / "runtime"
    knots_path = tmpdir / "knots"

    resources_path = THISDIR / "resources"

    khubenv = knots_hub.constants.Environ
    environ = os.environ.copy()
    environ.update(
        {
            khubenv.USER_INSTALL_PATH: str(user_install_path),
            khubenv.VENDOR_INSTALLER_CONFIG_PATHS: str(vendor_install_config_path),
            khubenv.INSTALLER: f"vTest={last_installer_path}",
            khubenv.RUNTIME_STORAGE_ROOT: str(runtime_path),
            khubenv.FORCE_CONSIDER_RUNTIME_LOCAL: "1",
            "KHUB_VENDOR_INSTALL_ROOT": str(vendor_install_path),
            "KHUB_VENDOR_REZ_ROOT": str(vendor_rez_path),
            "KHUB_RESOURCES_PATH": str(resources_path),
            "KHUB_KNOTS_PATH": str(knots_path),
            "KNOTS_HUB_RESTART_AS_SHELL": "1",
            "KLOCH_CONFIG_PROFILE_ROOTS": str(resources_path / "profiles"),
        }
    )

    blocks = get_hub_calls(sys.argv[1:])
    for index, block in enumerate(blocks):
        command = [sys.executable, "-m", "knots_hub"] + block
        header = (
            f"=== {index+1:0>2}/{len(blocks):0>2} [{' '.join(block)}] ================="
        )
        print("_" * len(header))
        print(header)
        result = subprocess.run(command, env=environ)
        if result.returncode:
            print(f"! ERROR executing knots_hub command '{block}' !")
            sys.exit(-1)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="knots_hub_test_") as _tmpdir:
        main(Path(_tmpdir))
