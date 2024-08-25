import os
import subprocess
import tempfile
import time
from typing import List

import pytest

from knots_hub.uninstaller import uninstall_paths


def test__uninstall_paths(tmp_path, monkeypatch):

    def _patch_execv(exe: str, argv: List[str]):
        subprocess.run([exe] + argv[1:], check=True)

    monkeypatch.setattr(os, "execv", _patch_execv)

    tmppatched = tmp_path / "tmppatched"
    tmppatched.mkdir()

    def _patch_tempfile(*args, **kwargs):
        return str(tmppatched)

    monkeypatch.setattr(tempfile, "mkdtemp", _patch_tempfile)

    install_dir = tmp_path / ".hubinstall"
    install_dir.mkdir()
    # just so it's not empty
    random_file = install_dir / "randomfile1.txt"
    random_file.write_text("🦎", encoding="utf-8")
    random_file2 = tmp_path / "randomfile2.txt"
    random_file2.write_text("✨", encoding="utf-8")

    with pytest.raises(SystemExit):
        uninstall_paths(paths=[install_dir, random_file2])
    assert not install_dir.exists()
    assert not random_file.exists()
    assert not random_file2.exists()

    # the deletion is parallel so wait for it to catchup
    time.sleep(0.5)
    assert not tmppatched.exists()
