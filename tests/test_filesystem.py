import sys
from pathlib import Path

from knots_hub import filesystem


def test__is_runtime_from_local_install(monkeypatch):
    local_install = Path("C:/Users/lcoll/AppData/Local/knots-hub")
    local_exe = Path(r"C:\Users\lcoll\AppData\Local\knots-hub\knots_hub-v0.7.0.exe")
    monkeypatch.setattr(sys, "executable", str(local_exe))
    assert filesystem.is_runtime_from_local_install(local_install)
