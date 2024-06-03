import abc
import argparse
import copy
import logging
import os
import subprocess
import sys
from typing import List

from pythonning.benchmark import timeit

import knots_hub
from knots_hub.constants import OS
from knots_hub.constants import LOCAL_ROOT_FILESYSTEM
from knots_hub.installer import HubInstallFilesystem
from knots_hub.installer import HubInstallConfig

LOGGER = logging.getLogger(__name__)


class BaseParser:
    """
    The root parser who's all subparsers use as base.

    All arguments defined here are accessible by subparsers.

    Args:
        args: user command line argument already parsed by argparse
    """

    def __init__(self, args: argparse.Namespace):
        self._args: argparse.Namespace = args
        self.install_filesystem = HubInstallFilesystem.from_local_root()

    @property
    def debug(self) -> bool:
        """
        True to execute the CLI in debug mode. Usually with more verbose logging.
        """
        return self._args.debug

    @property
    def dryrun(self) -> bool:
        """
        True to run the app as much as possible without writing anything to disk.
        """
        return self._args.dryrun

    @property
    def _restarted(self) -> int:
        """
        True if the app has been call has a restarted session.

        Only intended to be used internally.
        """
        return self._args._restarted

    @abc.abstractmethod
    def execute(self):
        """
        Arbitrary code that must be executed when the user ask this command.
        """
        raise NotImplementedError()

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        """
        Configure the given argparse ArgumentParser.
        """
        parser.add_argument(
            "--debug",
            action="store_true",
            help=cls.debug.__doc__,
        )
        parser.add_argument(
            "--dryrun",
            action="store_true",
            help=cls.dryrun.__doc__,
        )
        parser.add_argument(
            "--restarted__",
            dest="_restarted",
            default=0,
            type=int,
            help=cls.dryrun.__doc__,
        )
        parser.set_defaults(func=cls)

    def _restart_local_app(self):
        """
        Always restart to the locally installed hub, no matter if the current runtime is from
        somehwere else.
        """
        # safety to prevent an unlimited loop of restart that might happen
        if self._restarted >= 3:
            raise RuntimeError(
                "Prevented a fourth restart of the system which is not normal."
                "Invesitgate the logs to find why."
            )

        exe = self.install_filesystem.python_bin_path
        if self.install_filesystem.is_updating:
            exe = self.install_filesystem.updating_filesystem.python_bin_path

        argv = ["knots_hub"]  # program name expected by os.execl
        argv += ["-m", "knots_hub", "--restarted__", self._restarted + 1]

        current_argv = sys.argv.copy()[1:]
        if "--restarted__" in current_argv:
            index = current_argv.index("--restarted__")
            # remove the arg and its value
            current_argv.pop(index)
            current_argv.pop(index)

        argv += current_argv

        # safety mentioned in the doc
        sys.stdout.flush()
        # restart
        LOGGER.debug(f"os.execv({exe},*{argv})")
        os.execv(exe, argv)


class _Parser(BaseParser):
    """
    Parser executed when no subcommand is provided.
    """

    @abc.abstractmethod
    def execute(self):
        install_config = HubInstallConfig.from_environment()
        LOGGER.debug(f"config={install_config}")

        # 1. check if local install is required

        with timeit("hub installation took ", LOGGER.info):
            installed = knots_hub.installer.install_hub(
                local_install_path=install_config.local_install_path,
                requirements_path=install_config.requirements_path,
                python_version=install_config.python_version,
                dryrun=self.dryrun,
            )
        if installed:
            LOGGER.info("restarting app")
            self._restart_local_app()
            return

        # 2. check if local update required

        with timeit("hub updating took ", LOGGER.info):
            updated = knots_hub.installer.update_hub(
                local_install_path=install_config.local_install_path,
                requirements_path=install_config.requirements_path,
                python_version=install_config.python_version,
            )
        if updated:
            LOGGER.info("restarting app")
            self._restart_local_app()
            return

        # 3. check if an update was performed previously and need to be applied

        if OS.is_windows():
            subprocess.run(
                [
                    "wt",
                    "--window",
                    "0",
                    "new-tab",
                    "--title",
                    "knots-hub",
                    "--profile",
                    "Windows PowerShell",
                    "echo",
                    "hello world !",
                ]
            )

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        super().add_to_parser(parser)


class UninstallParser(BaseParser):
    """
    An "uninstall" sub-command.
    """

    def execute(self):
        pass

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        super().add_to_parser(parser)


def get_cli(argv=None) -> BaseParser:
    """
    Return the command line interface generated from user arguments provided.

    Args:
        argv: source command line argument to use instea dof the usual sys.argv
    """
    parser = argparse.ArgumentParser(
        knots_hub.__name__,
        description="Manage and access the knots pipeline for its users.",
    )
    _Parser.add_to_parser(parser)
    subparsers = parser.add_subparsers(required=False)

    subparser = subparsers.add_parser(
        "uninstall",
        description="Uninstall the hub from the user system.",
    )
    UninstallParser.add_to_parser(subparser)

    argv: List[str] = copy.copy(argv) or sys.argv[1:]
    args = parser.parse_args(argv)
    instance: BaseParser = args.func(args)

    return instance
