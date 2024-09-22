import time
from pathlib import Path

from knots_hub.installer import HubInstallFile


def test__HubInstallFile__read__write(tmp_path):
    installed_time = time.time()
    installed_version = "3.2.1"
    installed_path = Path(tmp_path)
    records_paths = {"foo": Path(tmp_path)}

    dst_path = tmp_path / ".hubinstall"

    instance = HubInstallFile(
        installed_time=installed_time,
        installed_version=installed_version,
        installed_path=installed_path,
        vendors_record_paths=records_paths,
    )
    instance.write_to_disk(dst_path)
    assert dst_path.exists()

    instance_read = HubInstallFile.read_from_disk(dst_path)
    assert instance_read.installed_time == installed_time
    assert instance_read.installed_version == installed_version
    assert instance_read.installed_path == installed_path
    assert instance_read.vendors_record_paths == records_paths


def test__HubInstallFile__update(tmp_path):
    installed_time = time.time()
    installed_version = "3.2.1"
    installed_path = Path(tmp_path)
    records_paths = {"foo": Path(tmp_path)}

    dst_path = tmp_path / ".hubinstall"

    instance = HubInstallFile(
        installed_time=installed_time,
        installed_version=installed_version,
        installed_path=installed_path,
        vendors_record_paths=records_paths,
    )
    instance.write_to_disk(dst_path)
    assert dst_path.exists()

    new_time = 1435435435
    new_instance = HubInstallFile(
        installed_time=new_time,
    )
    new_instance.update_disk(dst_path)

    updated_instance = HubInstallFile.read_from_disk(dst_path)
    assert updated_instance.installed_time == new_time
