import abc
import argparse
import json
import logging
import os
import sys
from typing import Type

import kloch
from pythonning.benchmark import timeit

import knots_hub
import knots_hub.installer
from knots_hub import HubConfig
from knots_hub import HubLocalFilesystem
from knots_hub.filesystem import is_runtime_from_local_install
from knots_hub.installer import HubInstallFile
from knots_hub.installer import HubInstallersList
from knots_hub.installer import get_hub_local_executable
from knots_hub.uninstaller import get_paths_to_uninstall
from knots_hub.uninstaller import uninstall_hub_only
from knots_hub.uninstaller import uninstall_paths

LOGGER = logging.getLogger(__name__)


def get_restart_args(
    current_argv: list[str],
    restarted_amount: int = 0,
) -> list[str]:
    """
    Get the args to pass to ``os.exec*``
    """
    argv = ["knots_hub"]  # program name expected by os.exec*
    argv += ["--restarted__", str(restarted_amount + 1)]

    new_argv = current_argv.copy()

    if "--restarted__" in new_argv:
        index = new_argv.index("--restarted__")
        # remove the arg and its value
        new_argv.pop(index)
        new_argv.pop(index)

    # prevent an infinite recursion
    if "--force-local-restart" in new_argv:
        new_argv.remove("--force-local-restart")

    argv += new_argv
    return argv


class BaseParser:
    """
    The root CLI parser who's all subparsers use as base.

    All arguments defined here are accessible by subparsers.

    Args:
        args: user command line argument already parsed by argparse
    """

    def __init__(
        self,
        args: argparse.Namespace,
        original_argv: list[str],
        config: HubConfig,
        filesystem: HubLocalFilesystem,
        extra_args: list[str],
    ):
        self._args: argparse.Namespace = args
        self._original_argv = original_argv
        self._filesystem = filesystem
        self._config = config
        self._extra_args = extra_args

    @property
    def debug(self) -> bool:
        """
        True to execute the CLI in debug mode. Usually with more verbose logging.
        """
        return self._args.debug

    @property
    def log_environ(self) -> bool:
        """
        True will log the current system environment variable. Also need the debug flag.
        """
        return self._args.log_environ

    @property
    def no_coloring(self) -> bool:
        """
        Disable colored logging, in case your system doesn't support it.
        """
        return self._args.no_coloring

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
        if self.log_environ:
            LOGGER.debug(
                "environ=" + json.dumps(dict(os.environ), indent=4, sort_keys=True)
            )

        local_install_path = self._config.local_install_path
        is_runtime_local = is_runtime_from_local_install(local_install_path)

        if not is_runtime_local:

            # an empty installer list imply the hub is never installed/updated locally
            installer_list = None
            installer_list_path = self._config.installer_list_path
            if installer_list_path:
                installer_list = HubInstallersList.from_file(path=installer_list_path)

            need_install = False

            if installer_list and not self._filesystem.is_hub_installed:
                need_install = True
            elif (
                installer_list
                and self._filesystem.is_hub_installed
                and not is_runtime_local
            ):
                hubinstall_file_path = self._filesystem.hubinstallfile_path
                hubinstall_file = HubInstallFile.read_from_disk(hubinstall_file_path)
                if installer_list.last_version != hubinstall_file.installed_version:
                    need_install = True
                    LOGGER.debug("uninstalling existing hub for upcoming update")
                    uninstall_hub_only(hubinstall_file)

            if need_install:
                src_path = installer_list.last_path
                dst_path = local_install_path
                LOGGER.info(f"installing hub '{src_path}' to '{dst_path}'")
                with timeit("installing took ", LOGGER.info):
                    exe_path = knots_hub.installer.install_hub(
                        install_src_path=src_path,
                        install_dst_path=dst_path,
                        installed_version=installer_list.last_version,
                        filesystem=self._filesystem,
                    )
                shortcut = knots_hub.installer.create_exe_shortcut(
                    shortcut_dir=self._filesystem.shortcut_dir,
                    exe_path=exe_path,
                )
                LOGGER.debug(f"updated shortcut '{shortcut}'")
                # we restart to local hub we just installed
                return sys.exit(self._restart_hub(exe=str(exe_path)))

            exe_path = get_hub_local_executable(self._filesystem)
            if exe_path:
                return sys.exit(self._restart_hub(exe=str(exe_path)))

        elif is_runtime_local and not self._restarted:
            raise RuntimeError(
                "Current application seems to be started directly from the local install."
                "You need to launch it from the server first."
            )

        # > reaching here mean the runtime is local

        # install or update vendor programs
        vendor_path = self._config.vendor_installers_config_path
        if vendor_path and not vendor_path.exists():
            LOGGER.error(f"Found non-existing vendor installer config '{vendor_path}'")
        elif vendor_path:
            LOGGER.debug(f"reading vendor installers '{vendor_path}'")
            vendor_installers = knots_hub.installer.read_vendor_installers_from_file(
                file_path=vendor_path,
            )
            LOGGER.debug(f"found {len(vendor_installers)} vendor installers.")
            knots_hub.installer.install_vendors(
                vendors=vendor_installers,
                filesystem=self._filesystem,
            )

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
            "--no-coloring",
            action="store_true",
            help=cls.no_coloring.__doc__,
        )
        parser.add_argument(
            "--log-environ",
            action="store_true",
            help=cls.log_environ.__doc__,
        )
        parser.add_argument(
            "--restarted__",
            dest="_restarted",
            default=0,
            type=int,
            help=argparse.SUPPRESS,
        )
        parser.set_defaults(func=cls)

    def _restart_hub(self, exe: str):
        """
        ! Anything after this function is not called.

        Args:
            exe: filesystem path to an existing hub executable
        """
        # safety to prevent an unlimited loop of restart.
        # not that it might happen but we never know
        if self._restarted > 3:
            raise RuntimeError(
                "Prevented a fourth restart leading to a probable infinite recursion."
                "Investigate the logs to find the cause."
            )

        current_argv = self._original_argv.copy()
        argv = get_restart_args(
            current_argv=current_argv,
            restarted_amount=self._restarted,
        )

        LOGGER.info(f"restarting hub '{exe}' ...")
        # safety mentioned in the doc
        sys.stdout.flush()
        LOGGER.debug(f"os.execv({exe},{argv})")
        os.execv(exe, argv)


class _Parser(BaseParser):
    """
    Parser executed when no subcommand is provided.
    """

    def execute(self):

        if self._extra_args:
            raise ValueError(
                f"Extra arguments not supported for the command {self._original_argv}"
            )

        super().execute()
        print("no command provided; exiting hub")

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        super().add_to_parser(parser)


class KlochParser(BaseParser):
    """
    A "kloch" subcommand, to start the kloch CLI.
    """

    def execute(self):
        super().execute()
        kloch_config = kloch.KlochConfig.from_environment()
        # plugins added in pyproject.toml
        kloch_config.launcher_plugins.extend(
            [
                "kloch_rezenv",
                "kloch_kiche",
            ]
        )

        argv = self._extra_args + (["--debug"] if self.debug else [])
        LOGGER.debug(f"using {kloch.__name__} v{kloch.__version__}")
        LOGGER.debug(f"kloch.get_cli({argv})")
        cli = kloch.get_cli(argv=argv, config=kloch_config)
        try:
            sys.exit(cli.execute())
        finally:
            # needed else we might get some filehandler permission issue
            # when clearing the log directory
            logging.shutdown()

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        super().add_to_parser(parser)


class UninstallParser(BaseParser):
    """
    An "uninstall" sub-command.
    """

    def execute(self):
        paths = get_paths_to_uninstall(filesystem=self._filesystem)
        if not paths:
            LOGGER.info("nothing to uninstall; exiting")
            return

        LOGGER.info(f"uninstalling hub from the filesystem.")
        LOGGER.debug(f"removing {paths}")
        sys.exit(uninstall_paths(paths=paths))

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        super().add_to_parser(parser)


def get_cli(
    config: HubConfig,
    filesystem: HubLocalFilesystem,
    argv: list[str] = None,
) -> BaseParser:
    """
    Return the command line interface generated from user arguments provided.

    Args:
        argv: source command line argument to use instea dof the usual sys.argv
        config: user-defined runtime configuration of the hub
        filesystem: collection of paths for storing runtime data
    """
    parser = argparse.ArgumentParser(
        knots_hub.__name__,
        description="Manage and access the knots pipeline for its users.",
    )
    _Parser.add_to_parser(parser)
    subparsers = parser.add_subparsers(required=False)

    subparser = subparsers.add_parser(
        "kloch",
        add_help=False,
        description="Call the Kloch CLI with all arguments redirected to it.",
    )
    KlochParser.add_to_parser(subparser)

    subparser = subparsers.add_parser(
        "uninstall",
        description="Uninstall the hub from the user system.",
    )
    UninstallParser.add_to_parser(subparser)

    argv: list[str] = sys.argv[1:] if argv is None else argv.copy()
    # allow unknown args for the `kloch` command
    args, extra_args = parser.parse_known_args(argv)
    cli_class: Type[BaseParser] = args.func
    instance: BaseParser = cli_class(
        args=args,
        original_argv=argv,
        config=config,
        filesystem=filesystem,
        extra_args=extra_args,
    )
    return instance
