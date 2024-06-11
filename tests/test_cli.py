import pytest

import knots_hub


def test__cli__no_args(tmp_path):

    config = knots_hub.HubConfig(
        local_install_path=tmp_path,
    )
    filesystem = knots_hub.HubInstallFilesystem(root=config.local_install_path)
    argv = []
    cli = knots_hub.get_cli(config=config, filesystem=filesystem, argv=argv)
    cli.execute()


def test__cli____applyupdate1(tmp_path):

    config = knots_hub.HubConfig(
        local_install_path=tmp_path,
    )
    filesystem = knots_hub.HubInstallFilesystem(root=config.local_install_path)
    argv = ["__applyupdate", "1", "--fakeextraarg"]
    cli = knots_hub.get_cli(config=config, filesystem=filesystem, argv=argv)
    # cannot rename file that doesnt exists
    with pytest.raises(FileNotFoundError):
        cli.execute()


def test__get_restart_args():
    src_argv = ["--debug", "--restarted__", "1"]
    result = knots_hub.cli.get_restart_args(
        current_argv=src_argv,
        restarted_amount=1,
        apply_update=0,
    )
    assert result == ["knots_hub", "--restarted__", "2", "--debug"]

    src_argv = ["--debug"]
    result = knots_hub.cli.get_restart_args(
        current_argv=src_argv,
        restarted_amount=0,
        apply_update=0,
    )
    assert result == ["knots_hub", "--restarted__", "1", "--debug"]

    src_argv = ["__applyupdate", "1", "--debug", "--restarted__", "1"]
    result = knots_hub.cli.get_restart_args(
        current_argv=src_argv,
        restarted_amount=1,
        apply_update=2,
    )
    assert result == [
        "knots_hub",
        "--restarted__",
        "2",
        "__applyupdate",
        "2",
        "--debug",
    ]

    src_argv = ["--debug", "__applyupdate", "2"]
    result = knots_hub.cli.get_restart_args(
        current_argv=src_argv,
        restarted_amount=0,
        apply_update=0,
    )
    assert result == [
        "knots_hub",
        "--restarted__",
        "1",
        "--debug",
    ]
