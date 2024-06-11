import json
import os
import sys
from pathlib import Path
from typing import List

import pytest

import knots_hub.__main__


def test__main__config():
    argv = []
    with pytest.raises(OSError) as error:
        knots_hub.__main__.main(argv=argv)
        assert "environment variable" in str(error)


def test__main__1(monkeypatch, tmp_path):

    install_dir = tmp_path / "hub"
    monkeypatch.setenv(knots_hub.Environ.USER_INSTALL_PATH, str(install_dir))

    argv = []
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)


def test__main__2(monkeypatch, data_dir, tmp_path):

    installers_content = {
        "999.1.0": "./v999",
        "0.3.0": str(data_dir / "v0.3"),
    }
    installers_path = tmp_path / "installers.json"
    with installers_path.open("w") as file:
        json.dump(installers_content, file, indent=4)

    os.mkdir(tmp_path / "v999")
    Path(tmp_path, "v999", knots_hub.constants.EXECUTABLE_NAME).write_text(
        "fake executable"
    )

    install_dir = tmp_path / "hub"
    filesystem = knots_hub.HubInstallFilesystem(root=install_dir)

    class ExecvPatcher:

        exe: Path = None
        args: List[str] = None
        called = False

        @classmethod
        def _patch_os_execv(cls, exe, args):
            exe = Path(exe)
            cls.called = True
            cls.exe = exe
            cls.args = args

    def _patch_sys_argv():
        return sys.argv.copy() + ["UNWANTEDARG"]

    monkeypatch.setenv(knots_hub.Environ.USER_INSTALL_PATH, str(install_dir))
    monkeypatch.setenv(knots_hub.Environ.INSTALLER_LIST_PATH, str(installers_path))
    monkeypatch.setattr(os, "execv", ExecvPatcher._patch_os_execv)
    monkeypatch.setattr(sys, "argv", _patch_sys_argv)

    # check the install system
    argv = []
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called
    assert ExecvPatcher.exe == filesystem.exe_src
    assert ExecvPatcher.exe.parent.exists()
    assert filesystem.install_src_dir.exists()
    assert not filesystem.install_new_dir.exists()
    assert not filesystem.install_old_dir.exists()
    assert "--restarted__" in ExecvPatcher.args
    assert "UNWANTEDARG" not in ExecvPatcher.args

    # check the update system
    ExecvPatcher.called = False
    argv = []
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.exe == filesystem.exe_new
    assert ExecvPatcher.exe.parent.exists()
    assert filesystem.install_src_dir.exists()
    assert filesystem.install_new_dir.exists()
    assert not filesystem.install_old_dir.exists()
    assert "--restarted__" in ExecvPatcher.args
    assert "__applyupdate" in ExecvPatcher.args
    assert "UNWANTEDARG" not in ExecvPatcher.args

    # check the apply update stage 1 system
    ExecvPatcher.called = False
    argv = ["__applyupdate", "1"]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.exe == filesystem.exe_old
    assert ExecvPatcher.exe.parent.exists()
    assert not filesystem.install_src_dir.exists()
    assert filesystem.install_new_dir.exists()
    assert filesystem.install_old_dir.exists()
    assert "--restarted__" in ExecvPatcher.args
    assert "__applyupdate" in ExecvPatcher.args
    assert "UNWANTEDARG" not in ExecvPatcher.args
