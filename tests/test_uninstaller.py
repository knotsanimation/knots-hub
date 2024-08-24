import os
import subprocess
import tempfile
from pathlib import Path
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
    src_log = tmp_path / "hub.log"
    src_log.write_text("🐍🐍🐍", encoding="utf-8")
    # just so it's not empty
    random_file = install_dir / "randomfile1.txt"
    random_file.write_text("🦎", encoding="utf-8")
    random_file2 = tmp_path / "randomfile2.txt"
    random_file2.write_text("✨", encoding="utf-8")

    with pytest.raises(SystemExit):
        uninstall_paths(paths=[install_dir, random_file2], logs_path=src_log)
    assert not install_dir.exists()
    assert not random_file.exists()
    assert not random_file2.exists()
    assert src_log.exists()  # (not removed)
    assert Path(tmppatched, src_log.name).exists()
