import os
import subprocess
import tempfile
from pathlib import Path
from typing import List

import pytest

import knots_hub
from knots_hub.installer import HubInstallersList
from knots_hub.installer import uninstall_hub


def test__InstallerList__from_file(data_dir):
    path = data_dir / "installerlist.1.json"
    instance = HubInstallersList.from_file(path)
    assert instance.last_version == "4.6.0"
    assert instance.last_path == data_dir / "path4"


def test__InstallerList(data_dir):
    content = [
        ("0.1.0", Path("path1")),
        ("3.10.5", Path("path2")),
        ("4.6.0", Path("path4")),
        ("3.2.8", Path("path3")),
    ]
    instance = HubInstallersList(content=content)
    assert instance.last_version == "3.2.8"
    assert instance.last_path == Path("path3")

    assert instance.get_path("4.6.0") == Path("path4")


def test__uninstall_hub(tmp_path, monkeypatch):

    def _patch_execv(exe: str, argv: List[str]):
        subprocess.run([exe] + argv[1:], check=True)

    monkeypatch.setattr(os, "execv", _patch_execv)

    def _patch_tempfile(*args, **kwargs):
        return str(tmp_path)

    monkeypatch.setattr(tempfile, "mkdtemp", _patch_tempfile)

    install_dir = tmp_path / ".hubinstall"
    install_dir.mkdir()
    filesystem = knots_hub.HubInstallFilesystem(root=install_dir)
    # just so it's not empty
    Path(install_dir, "randomfile.txt").write_text("🦎", encoding="utf-8")
    filesystem.install_src_dir.mkdir()

    assert filesystem.root.exists()
    with pytest.raises(SystemExit):
        uninstall_hub(filesystem=filesystem)
    assert not filesystem.root.exists()
