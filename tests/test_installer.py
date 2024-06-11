from pathlib import Path

from knots_hub.installer import InstallerList


def test__InstallerList__from_file(data_dir):
    path = data_dir / "installerlist.1.json"
    instance = InstallerList.from_file(path)
    assert instance.last_version == "4.6.0"
    assert instance.last_path == data_dir / "path4"


def test__InstallerList(data_dir):
    content = [
        ("0.1.0", Path("path1")),
        ("3.10.5", Path("path2")),
        ("4.6.0", Path("path4")),
        ("3.2.8", Path("path3")),
    ]
    instance = InstallerList(content=content)
    assert instance.last_version == "3.2.8"
    assert instance.last_path == Path("path3")

    assert instance.get_path("4.6.0") == Path("path4")
