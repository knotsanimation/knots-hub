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
    root_dir.mkdir()
    monkeypatch.setattr(knots_hub.filesystem, "_DEFAULT_ROOT_DIR", root_dir)

    # we fake a local install already happened
    hubinstall = knots_hub.installer.HubInstallRecord(2, "1", root_dir, {})
    hubinstall_path = root_dir / ".hubinstall"
    hubinstall.write_to_disk(hubinstall_path)

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

    source_install_dir = tmp_path / "vTest"
    source_install_dir.mkdir()

    exe_name = knots_hub.constants.EXECUTABLE_NAME
    Path(source_install_dir, exe_name).write_text("fake executable")

    # we intentionally add a useless extra nested dir
    vendor_root = tmp_path / ".vendorroot"
    vendor_install_dir = tmp_path / "vendor"
    rez_install_dir = vendor_install_dir / "rez"

    vendor_config = {
        "rez": {
            "install_dir": str(rez_install_dir),
            "dirs_to_make": [str(vendor_root), str(vendor_install_dir)],
            "python_version": "3.10.11",
            "rez_version": "2.114.1",
        }
    }
    vendor_config_path = tmp_path / "vendor-config.json"
    with vendor_config_path.open("w") as file:
        json.dump(vendor_config, file, indent=4)

    class SubprocessPatcher:

        exe: Path = None
        args: List[str] = None
        called = False

        @classmethod
        def clear(cls):
            cls.exe = None
            cls.args = None
            cls.called = False

        @classmethod
        def _patch(cls, command, *args, **kwargs):
            exe = Path(command[0])
            cls.called = True
            cls.exe = exe
            cls.args = command[1:]
            return subprocess.CompletedProcess(command, 0)

    def _patch_sys_argv():
        return sys.argv.copy() + ["UNWANTEDARG"]

    monkeypatch.setattr(subprocess, "run", SubprocessPatcher._patch)
    monkeypatch.setattr(sys, "argv", _patch_sys_argv)

    monkeypatch.setenv(knots_hub.Environ.USER_INSTALL_PATH, str(install_dir))
    monkeypatch.setenv(knots_hub.Environ.INSTALLER, f"testversion={source_install_dir}")
    monkeypatch.setenv(
        knots_hub.Environ.VENDOR_INSTALLER_CONFIG_PATHS, str(vendor_config_path)
    )

    data_root_dir = tmp_path / "knots-hub.data"
    monkeypatch.setattr(knots_hub.filesystem, "_DEFAULT_ROOT_DIR", data_root_dir)

    filesystem = knots_hub.HubLocalFilesystem()
    assert filesystem.root_dir == data_root_dir

    # check the install system

    argv = ["--log-environ"]
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    expected_local_exe = install_dir / exe_name
    assert expected_local_exe.exists()
    assert SubprocessPatcher.called is True
    assert SubprocessPatcher.exe == expected_local_exe

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

    argv = SubprocessPatcher.args.copy()[1:]
    monkeypatch.setenv(knots_hub.Environ.IS_RESTARTED, "1")
    SubprocessPatcher.clear()
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert SubprocessPatcher.called is False
    assert InstallRezPatcher.called is True
    assert InstallPythonPatcher.called is True
    assert vendor_install_dir.exists()
    assert rez_install_dir.exists()

    # check no install

    SubprocessPatcher.clear()
    InstallRezPatcher.called = False
    InstallPythonPatcher.called = False

    argv = []
    monkeypatch.setenv(knots_hub.constants.Environ.IS_RESTARTED, "1")
    SubprocessPatcher.clear()
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert SubprocessPatcher.called is False
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

    SubprocessPatcher.clear()
    InstallRezPatcher.called = False
    InstallPythonPatcher.called = False

    argv = []
    monkeypatch.setenv(knots_hub.constants.Environ.IS_RESTARTED, "1")
    SubprocessPatcher.clear()
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    assert SubprocessPatcher.called is False
    assert InstallRezPatcher.called is True
    assert InstallPythonPatcher.called is True

    # check about subcommand

    argv = ["about"]
    monkeypatch.setenv(knots_hub.constants.Environ.IS_RESTARTED, "1")
    with pytest.raises(SystemExit):
        knots_hub.__main__.main(argv=argv)

    # check uninstall

    def _patch_execv(exe_: str, argv_: List[str]):
        # we patch subprocess.run above so use a different function
        subprocess.check_call([exe_] + argv_[1:])

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
