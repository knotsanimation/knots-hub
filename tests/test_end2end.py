import json
import os
import sys
from pathlib import Path
from typing import List

import pytest

import knots_hub.__main__
import knots_hub.installer._python
import knots_hub.installer._rez


def test__main__config():
    argv = []
    with pytest.raises(OSError) as error:
        knots_hub.__main__.main(argv=argv)
        assert "environment variable" in str(error)


def test__main__no_installers(monkeypatch, tmp_path):

    install_dir = tmp_path / "hub"
    monkeypatch.setenv(knots_hub.Environ.USER_INSTALL_PATH, str(install_dir))

    argv = []
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)


def test__main__full(monkeypatch, data_dir, tmp_path, caplog):
    """
    We run the full update system by manually faking a restart for each stage.
    """
    caplog.set_level("DEBUG")

    install_dir = tmp_path / "hub"
    filesystem = knots_hub.HubInstallFilesystem(root=install_dir)

    last_hub_version = "999.1.0"
    installers_content = {
        last_hub_version: "./v999",
        "0.3.0": str(data_dir / "v0.3"),
    }
    installers_path = tmp_path / "installers.json"
    with installers_path.open("w") as file:
        json.dump(installers_content, file, indent=4)

    os.mkdir(tmp_path / "v999")
    Path(tmp_path, "v999", filesystem.expected_exe_src.name).write_text(
        "fake executable"
    )

    vendor_install_dir = tmp_path / "vendor"

    vendor_config = {
        "rez": {
            "version": 1,
            "python_version": "3.10.11",
            "rez_version": "2.114.1",
        }
    }
    vendor_config_path = tmp_path / "vendor-config.json"
    with vendor_config_path.open("w") as file:
        json.dump(vendor_config, file, indent=4)

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

    monkeypatch.setattr(os, "execv", ExecvPatcher._patch_os_execv)
    monkeypatch.setattr(sys, "argv", _patch_sys_argv)

    monkeypatch.setenv(knots_hub.Environ.USER_INSTALL_PATH, str(install_dir))
    monkeypatch.setenv(knots_hub.Environ.INSTALLER_LIST_PATH, str(installers_path))
    monkeypatch.setenv(knots_hub.Environ.VENDOR_INSTALL_PATH, str(vendor_install_dir))
    monkeypatch.setenv(
        knots_hub.Environ.VENDOR_INSTALLERS_CONFIG_PATH, str(vendor_config_path)
    )

    # check the install system
    argv = ["--log-environ"]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called
    assert ExecvPatcher.exe == filesystem.current_exe_src
    assert ExecvPatcher.exe.parent.exists()
    assert filesystem.install_src_dir.exists()
    assert not filesystem.install_new_dir.exists()
    assert not filesystem.install_old_dir.exists()
    assert "--restarted__" in ExecvPatcher.args
    assert "UNWANTEDARG" not in ExecvPatcher.args

    # check the update system
    ExecvPatcher.called = False
    argv = ExecvPatcher.args.copy()[1:]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called
    assert ExecvPatcher.exe == filesystem.current_exe_new
    assert ExecvPatcher.exe.parent.exists()
    assert filesystem.install_src_dir.exists()
    assert filesystem.install_new_dir.exists()
    assert not filesystem.install_old_dir.exists()
    assert "--restarted__" in ExecvPatcher.args
    assert "__applyupdate 1" in " ".join(ExecvPatcher.args)
    assert "UNWANTEDARG" not in ExecvPatcher.args

    # check the apply update stage 1 system
    ExecvPatcher.called = False
    argv = ExecvPatcher.args.copy()[1:]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called
    assert ExecvPatcher.exe == filesystem.current_exe_old
    assert ExecvPatcher.exe.parent.exists()
    assert not filesystem.install_src_dir.exists()
    assert filesystem.install_new_dir.exists()
    assert filesystem.install_old_dir.exists()
    assert "--restarted__" in ExecvPatcher.args
    assert "__applyupdate 2" in " ".join(ExecvPatcher.args)
    assert "UNWANTEDARG" not in ExecvPatcher.args

    # check the apply update stage 2 system
    ExecvPatcher.called = False
    argv = ExecvPatcher.args.copy()[1:]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called
    assert ExecvPatcher.exe == filesystem.current_exe_src
    assert ExecvPatcher.exe.parent.exists()
    assert filesystem.install_src_dir.exists()
    assert not filesystem.install_new_dir.exists()
    assert filesystem.install_old_dir.exists()
    assert "--restarted__" in ExecvPatcher.args
    assert "__applyupdate" not in ExecvPatcher.args

    # the hub is supposed to restarted with the latest version so we fake it by manually
    # overriding it.
    monkeypatch.setattr(knots_hub, "__version__", last_hub_version)

    # check post-update
    # it must first trigger the vendors install

    class InstallRezPatcher:

        called = False

        @classmethod
        def patch(cls, *args, **kwargs):
            cls.called = True

    monkeypatch.setattr(
        knots_hub.installer._rez,
        "install_rez",
        InstallRezPatcher.patch,
    )

    class InstallPythonPatcher:

        called = False

        @classmethod
        def patch(cls, *args, **kwargs):
            cls.called = True

    monkeypatch.setattr(
        knots_hub.installer._rez,
        "install_python",
        InstallPythonPatcher.patch,
    )

    ExecvPatcher.called = False
    argv = ExecvPatcher.args.copy()[1:]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert not ExecvPatcher.called
    assert filesystem.install_src_dir.exists()
    assert not filesystem.install_new_dir.exists()
    assert not filesystem.install_old_dir.exists()
    assert InstallRezPatcher.called is True
    assert InstallPythonPatcher.called is True

    # check launching after everything is installed

    ExecvPatcher.called = False
    InstallPythonPatcher.called = False
    InstallRezPatcher.called = False

    argv = []
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called is False, ExecvPatcher.args
    assert InstallRezPatcher.called is False
    assert InstallPythonPatcher.called is False

    # update the vendor and check if it re-trigger an update

    vendor_config = {
        "rez": {
            # we just need to update the version
            "version": 2,
            "python_version": "3.10.11",
            "rez_version": "2.114.1",
        }
    }
    vendor_config_path = tmp_path / "vendor-config.json"
    with vendor_config_path.open("w") as file:
        json.dump(vendor_config, file, indent=4)

    argv = []
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called is False, ExecvPatcher.args
    assert InstallRezPatcher.called is True
    assert InstallPythonPatcher.called is True

    # check --force-local-restart is working

    ExecvPatcher.called = False
    InstallPythonPatcher.called = False
    InstallRezPatcher.called = False

    argv = ["--force-local-restart"]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called is True, ExecvPatcher.args
    assert ExecvPatcher.exe == filesystem.current_exe_src
    assert "--force-local-restart" not in ExecvPatcher.args
    assert InstallRezPatcher.called is False
    assert InstallPythonPatcher.called is False
