import abc
import argparse
import copy
import logging
import os
import subprocess
import sys
from typing import List
from typing import Type

from pythonning.benchmark import timeit

import knots_hub
from knots_hub import HubInstallFilesystem
from knots_hub import HubConfig
from knots_hub.constants import Environ
from knots_hub.constants import OS
from knots_hub._terminal import get_terminal_for_script

LOGGER = logging.getLogger(__name__)


class BaseParser:
    """
    The root parser who's all subparsers use as base.

    All arguments defined here are accessible by subparsers.

    Args:
        args: user command line argument already parsed by argparse
    """

    def __init__(
        self,
        args: argparse.Namespace,
        config: HubConfig,
        filesystem: HubInstallFilesystem,
    ):
        self._args: argparse.Namespace = args
        self._filesystem = filesystem
        self._config = config

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

    @property
    def _force_restart(self) -> bool:
        """
        Force the app to restart even if it needs no updating.

        Only intended to be used internally.
        """
        return self._args._force_restart

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
            help=cls._restarted.__doc__,
        )
        parser.add_argument(
            "--force_restart__",
            dest="_force_restart",
            action="store_true",
            help=cls._force_restart.__doc__,
        )
        parser.set_defaults(func=cls)

    def _restart_local_app(self, need_update=False):
        """
        Always restart to the locally installed hub, no matter if the current runtime is from
        somewhere else.

        Args:
            need_update:
                if True we duplicate the launcher to a temporary location so
                the hub can be updated without file access restrictions.
        """
        # safety to prevent an unlimited loop of restart that might happen
        if self._restarted >= 3:
            raise RuntimeError(
                "Prevented a fourth restart of the system which is not normal."
                "Investigate the logs to find why."
            )

        filesystem = self._filesystem  # alias for shorter lines

        launcher = filesystem.launcher_path
        if need_update:
            # XXX: this create a temp directory that we don't clean.
            #  We leave it up to the OS to clean it.
            launcher = knots_hub.installer.create_temp_launcher(
                filesystem.launcher_path
            )

        terminal_command = get_terminal_for_script(script_path=launcher)
        exe = terminal_command.pop(0)

        argv = ["knots_hub"]  # program name expected by os.execl
        argv += terminal_command
        argv += ["--restarted__", str(self._restarted + 1)]

        current_argv = sys.argv.copy()[1:]
        if "--restarted__" in current_argv:
            index = current_argv.index("--restarted__")
            # remove the arg and its value
            current_argv.pop(index)
            current_argv.pop(index)
        if "--force_restart__" in current_argv:
            current_argv.remove("--force_restart__")

        argv += current_argv

        environ = os.environ.copy()

        if need_update:
            environ[Environ.LAUNCHER_UPDATE_CWD] = str(filesystem.root)
            # we will need to restart even if the launcher doesn't need upgrading,
            # so we use back the locally installed launcher instead of the temp launcher
            argv += ["--force_restart__"]

        # safety mentioned in the doc
        sys.stdout.flush()
        # restart
        LOGGER.debug(f"os.execve({exe},*{argv},{environ})")
        os.execve(exe, argv, environ)


class _Parser(BaseParser):
    """
    Parser executed when no subcommand is provided.
    """

    @abc.abstractmethod
    def execute(self):

        local_install_path = self._config.local_install_path
        requirements_path = self._config.requirements_path
        python_version = self._config.python_version

        # 1. check if local install is required

        with timeit("hub installation took ", LOGGER.info):
            installed = knots_hub.installer.install_hub(
                local_install_path=local_install_path,
                requirements_path=requirements_path,
                python_version=python_version,
                dryrun=self.dryrun,
            )
        if installed:
            LOGGER.info("restarting app ...")
            self._restart_local_app()
            return

        # 2. check if local update required

        with timeit("hub updating took ", LOGGER.info):
            updated = knots_hub.installer.update_hub(
                local_install_path=local_install_path,
                requirements_path=requirements_path,
                python_version=python_version,
            )
        if updated:
            LOGGER.info("restarting app ...")
            self._restart_local_app(need_update=True)
            return

        # 3. check if launcher need to be updated
        with timeit("hub launcher updating took ", LOGGER.info):
            updated = knots_hub.installer.install_hub_launcher(
                launcher_path=self._filesystem.launcher_path,
            )
        if updated:
            LOGGER.info("restarting app ...")
            self._restart_local_app()
            return

        if self._force_restart:
            LOGGER.info("restarting app ...")
            self._restart_local_app()
            return

        # we can assume we are in a powershell context
        if OS.is_windows():
            print("hello world !")

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


def get_cli(
    config: HubConfig,
    filesystem: HubInstallFilesystem,
    argv=None,
) -> BaseParser:
    """
    Return the command line interface generated from user arguments provided.

    Args:
        argv: source command line argument to use instea dof the usual sys.argv
        config:
        filesystem:
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
    cli_class: Type[BaseParser] = args.func
    instance: BaseParser = cli_class(
        args=args,
        config=config,
        filesystem=filesystem,
    )
    return instance
