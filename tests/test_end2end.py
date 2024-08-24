import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

import pytest

import knots_hub.__main__
from knots_hub import HubLocalFilesystem


def test__main__config(tmp_path, monkeypatch):
    root_dir = tmp_path / "knots-hub"
    monkeypatch.setattr(knots_hub.filesystem, "_DEFAULT_ROOT_DIR", root_dir)

    argv = []
    with pytest.raises(OSError) as error:
        knots_hub.__main__.main(argv=argv)
        assert "environment variable" in str(error)

    assert not root_dir.exists()


def test__main__no_installers(monkeypatch, tmp_path, caplog):

    caplog.set_level(logging.DEBUG)

    install_dir = tmp_path / "hub"
    monkeypatch.setenv(knots_hub.Environ.USER_INSTALL_PATH, str(install_dir))
    root_dir = tmp_path / "knots-hub"
    monkeypatch.setattr(knots_hub.filesystem, "_DEFAULT_ROOT_DIR", root_dir)

    argv = []
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert root_dir.exists()


def test__main__full(monkeypatch, data_dir, tmp_path, caplog):
    """
    We run the full update system by manually faking a restart for each stage.
    """
    caplog.set_level("DEBUG")

    install_dir = tmp_path / "hub"

    last_hub_version = "999.1.0"
    installers_content = {
        last_hub_version: "./v999",
        "0.3.0": str(data_dir / "v0.3"),
    }
    installers_path = tmp_path / "installers.json"
    with installers_path.open("w") as file:
        json.dump(installers_content, file, indent=4)

    exe_name = knots_hub.constants.EXECUTABLE_NAME

    os.mkdir(tmp_path / "v999")
    Path(tmp_path, "v999", exe_name).write_text("fake executable")

    vendor_install_dir = tmp_path / "vendor"
    rez_install_dir = vendor_install_dir / "rez"

    vendor_config = {
        "rez": {
            "version": 1,
            "install_dir": str(rez_install_dir),
            "dirs_to_make": [str(vendor_install_dir)],
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
        def clear(cls):
            cls.exe = None
            cls.args = None
            cls.called = False

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
    monkeypatch.setenv(
        knots_hub.Environ.VENDOR_INSTALLERS_CONFIG_PATH, str(vendor_config_path)
    )

    data_root_dir = tmp_path / "knots-hub.data"
    monkeypatch.setattr(knots_hub.filesystem, "_DEFAULT_ROOT_DIR", data_root_dir)

    filesystem = knots_hub.HubLocalFilesystem()
    assert filesystem.root_dir == data_root_dir

    def _check_shortcut():
        _src_shortcut_path = knots_hub.installer.create_exe_shortcut(
            filesystem.shortcut_dir, ExecvPatcher.exe, dry_run=True
        )
        assert _src_shortcut_path.exists()
        if knots_hub.OS.is_windows():
            # XXX: windows lnk store the link in ascii
            local_exe = knots_hub.installer.get_hub_local_executable(filesystem)
            assert local_exe
            assert bytes(local_exe) in _src_shortcut_path.read_bytes()

    # check the install system

    argv = ["--log-environ"]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    expected_local_exe = install_dir / exe_name
    assert expected_local_exe.exists()
    _check_shortcut()
    assert ExecvPatcher.called is True
    assert ExecvPatcher.exe == expected_local_exe

    # check the vendor install system

    class InstallRezPatcher:

        called = False

        @classmethod
        def patch(cls, *args, **kwargs):
            cls.called = True

    monkeypatch.setattr(
        knots_hub.installer.vendors._rez,
        "install_rez",
        InstallRezPatcher.patch,
    )

    class InstallPythonPatcher:
        called = False

        @classmethod
        def patch(cls, *args, **kwargs):
            cls.called = True

    monkeypatch.setattr(
        knots_hub.installer.vendors._rez,
        "install_python",
        InstallPythonPatcher.patch,
    )

    def _patched_is_runtime_from_local_install(*args):
        knots_hub.filesystem.LOGGER.info("// patched")
        return True

    monkeypatch.setattr(
        knots_hub.cli,
        "is_runtime_from_local_install",
        _patched_is_runtime_from_local_install,
    )

    argv = ExecvPatcher.args.copy()[1:]
    ExecvPatcher.clear()
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called is False
    assert InstallRezPatcher.called is True
    assert InstallPythonPatcher.called is True
    assert vendor_install_dir.exists()
    assert rez_install_dir.exists()

    # check no install

    ExecvPatcher.clear()
    InstallRezPatcher.called = False
    InstallPythonPatcher.called = False

    argv = ["--restarted", "1"]
    ExecvPatcher.clear()
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called is False
    assert InstallRezPatcher.called is False
    assert InstallPythonPatcher.called is False

    # update the vendor and check if it re-trigger an update

    vendor_config = {
        "rez": {
            # we just need to update the version
            "version": 2,
            "python_version": "3.10.11",
            "rez_version": "2.114.1",
            "install_dir": str(rez_install_dir),
            "dirs_to_make": [str(vendor_install_dir)],
        }
    }
    vendor_config_path = tmp_path / "vendor-config.json"
    with vendor_config_path.open("w") as file:
        json.dump(vendor_config, file, indent=4)

    ExecvPatcher.clear()
    InstallRezPatcher.called = False
    InstallPythonPatcher.called = False

    argv = ["--restarted", "1"]
    ExecvPatcher.clear()
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert ExecvPatcher.called is False
    assert InstallRezPatcher.called is True
    assert InstallPythonPatcher.called is True

    # check uninstall

    def _patch_execv(exe_: str, argv_: List[str]):
        subprocess.run([exe_] + argv_[1:], check=True)

    monkeypatch.setattr(os, "execv", _patch_execv)

    tmppatched = tmp_path / "tmp.uninstall"
    tmppatched.mkdir()

    def _patch_tempfile(*args, **kwargs):
        return str(tmppatched)

    monkeypatch.setattr(tempfile, "mkdtemp", _patch_tempfile)

    argv = ["uninstall"]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert not rez_install_dir.exists()
    assert not vendor_install_dir.exists()
    assert not data_root_dir.exists()
    assert list(tmppatched.glob("*"))
