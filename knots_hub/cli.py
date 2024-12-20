import abc
import argparse
import json
import logging
import os
import subprocess
import sys
import webbrowser
from typing import Type

import kloch
from pythonning.benchmark import timeit

import knots_hub
import knots_hub.installer
from knots_hub.constants import Environ
from knots_hub import HubConfig
from knots_hub import HubLocalFilesystem
from knots_hub.filesystem import is_runtime_from_local_install
from knots_hub.installer import HubInstallRecord
from knots_hub.installer import VendorInstallRecord
from knots_hub.installer import get_hub_local_executable
from knots_hub.installer import read_vendor_installer_from_file
from knots_hub.installer import uninstall_vendor
from knots_hub.uninstaller import get_paths_to_uninstall
from knots_hub.uninstaller import uninstall_hub_only
from knots_hub.uninstaller import uninstall_paths

LOGGER = logging.getLogger(__name__)


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

    @abc.abstractmethod
    def execute(self):
        """
        Arbitrary code that must be executed when the user ask this command.
        """
        restarted: int = int(os.getenv(Environ.IS_RESTARTED, 0))

        if self.log_environ:
            LOGGER.debug(
                "environ=" + json.dumps(dict(os.environ), indent=4, sort_keys=True)
            )

        local_install_path = self._config.local_install_path
        is_runtime_local = is_runtime_from_local_install(local_install_path)

        # this code is for testing purpose
        force_local = os.getenv(Environ.FORCE_CONSIDER_RUNTIME_LOCAL, None)
        # we assume the first restart is always
        # to the local interpreter (which is the case for now)
        if force_local and restarted > 0:
            is_runtime_local = True

        # we restart to the local install for performance consideration.
        # And we force to start by the remote as it's always the latest version,
        # while local may be an older version which will have issue reading more
        # up-to date configs and similar.

        if not is_runtime_local:

            # an empty installer path imply the hub is never installed/updated locally
            need_install = False
            installer = self._config.installer

            if installer and not self._filesystem.is_hub_installed:
                need_install = True
            elif (
                installer and self._filesystem.is_hub_installed and not is_runtime_local
            ):
                hubrecord_path = self._filesystem.hubinstall_record_path
                hubrecord_file = HubInstallRecord.read_from_disk(hubrecord_path)
                if installer.version != hubrecord_file.installed_version:
                    need_install = True
                    LOGGER.debug("uninstalling existing hub for upcoming update")
                    uninstall_hub_only(hubrecord_file)

            if need_install:
                src_path = installer.path
                dst_path = local_install_path
                LOGGER.info(f"installing hub '{src_path}' to '{dst_path}'")
                with timeit("installing took ", LOGGER.info):
                    exe_path = knots_hub.installer.install_hub(
                        install_src_path=src_path,
                        install_dst_path=dst_path,
                        installed_version=installer.version,
                        hubrecord_path=self._filesystem.hubinstall_record_path,
                    )
                # we restart to local hub we just installed
                return sys.exit(self._restart_hub(exe=str(exe_path)))

            exe_path = get_hub_local_executable(self._filesystem)
            if exe_path:
                return sys.exit(self._restart_hub(exe=str(exe_path)))

        elif is_runtime_local and not restarted and not self._config.skip_local_check:
            LOGGER.error(
                "Current application seems to be started directly from the local install."
                "You need to launch it from the server first."
            )
            sys.exit(-1)

        # > reaching here mean the runtime is local

        # install or update vendor programs

        vendors2install: dict[str, knots_hub.installer.BaseVendorInstaller] = {}
        vendor_config_paths = self._config.vendor_installer_config_paths
        for vendor_path in vendor_config_paths:
            if not vendor_path.exists():
                LOGGER.error(f"Non-existing vendor installer '{vendor_path}'")
                continue
            vendors = read_vendor_installer_from_file(vendor_path)
            vendors2install.update({vendor.name(): vendor for vendor in vendors})

        # we are sure the path exists as vendor happens after hub install/update
        hubrecord_path = self._filesystem.hubinstall_record_path
        hubrecord_file = HubInstallRecord.read_from_disk(hubrecord_path)
        vendor_installed_paths = hubrecord_file.vendors_record_paths
        if vendor_installed_paths:
            # vendor that were installed previously but that we don't install anymore
            vendors2uninstall = set(vendor_installed_paths.keys()).difference(
                vendors2install.keys()
            )
        else:
            vendor_installed_paths = {}
            vendors2uninstall = set()

        for vendor2uninstall in vendors2uninstall:
            vendor_record_path = vendor_installed_paths[vendor2uninstall]
            if vendor_record_path.exists():
                vendor_record = VendorInstallRecord.read_from_disk(vendor_record_path)
                LOGGER.info(f"uninstalling vendor '{vendor_record.name}'")
                uninstall_vendor(vendor_record)
            else:
                # somehow the record path was already deleted externally
                continue

        if vendors2install:
            LOGGER.debug(f"got {len(vendors2install)} vendor to check for install.")

            vendors_record_paths = {}

            for vendor_name, vendor in vendors2install.items():

                vendor_record_path = vendor_installed_paths.get(vendor_name)
                if not vendor_record_path:
                    vendor_record_path = vendor.install_record_path

                try:
                    installed = knots_hub.installer.install_vendor(
                        vendor=vendor,
                        record_path=vendor_record_path,
                    )
                except:
                    LOGGER.warning(
                        f"failed to install vendor '{vendor_name}'; "
                        f"you may need to uninstall knots-hub and restart it to trigger a fresh install."
                    )
                    raise

                if installed:
                    LOGGER.info(f"installed vendor '{vendor_name}'")
                vendors_record_paths[vendor_name] = vendor_record_path

            LOGGER.debug(
                f"updating hub records '{hubrecord_path}' with installed vendors"
            )
            HubInstallRecord(vendors_record_paths=vendors_record_paths).update_disk(
                hubrecord_path
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
        parser.set_defaults(func=cls)

    def _restart_hub(self, exe: str):
        """
        ! Anything after this function is not called.

        Args:
            exe: filesystem path to an existing hub executable
        """
        restarted: int = int(os.getenv(Environ.IS_RESTARTED, 0))

        # safety to prevent an unlimited loop of restart.
        # (happened during development on tricky refactoring)
        if restarted > 3:
            LOGGER.error(
                "Prevented a fourth restart leading to a probable infinite recursion."
                "Investigate the logs to find the cause."
            )
            sys.exit(-1)

        restarted += 1
        current_argv = self._original_argv.copy()
        command = [exe] + current_argv
        environ = os.environ.copy()
        environ[Environ.IS_RESTARTED] = str(restarted)

        # this is an undocumented env var only used for internal testing
        asshell: bool = bool(os.getenv("KNOTS_HUB_RESTART_AS_SHELL", False))

        LOGGER.info(f"restarting hub to '{exe}' (asshell={asshell}) ...")
        LOGGER.debug(f"subprocess.run({command})")
        # XXX: we use subprocess instead of os.execv because the implementation on Windows
        #   is not a real restart https://github.com/python/cpython/issues/63323.
        result = subprocess.run(command, shell=asshell, env=environ)
        sys.exit(result.returncode)


class _Parser(BaseParser):
    """
    Parser executed when no subcommand is provided.
    """

    def execute(self):

        if self._extra_args:
            LOGGER.error(
                f"Extra arguments not supported for the command {self._original_argv}"
            )
            sys.exit(-1)

        super().execute()
        LOGGER.warning("no command provided; exiting hub")

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

        argv = self._extra_args.copy()
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


class AboutParser(BaseParser):
    """
    An "about" sub-command.
    """

    def execute(self):
        super().execute()
        print(f"[{knots_hub.__name__} v{knots_hub.__version__}]")
        aboutdict = {}
        aboutdict["interpreter"] = knots_hub.constants.INTERPRETER_PATH
        aboutdict["frozen"] = knots_hub.constants.IS_APP_FROZEN
        aboutdict.update(self._config.as_dict())
        aboutdict["local_data_dir"] = self._filesystem.root_dir
        aboutdict["local_log_path"] = self._filesystem.log_path

        maxlen = max([len(k) for k in aboutdict.keys()])
        for k, v in aboutdict.items():
            print(f"| {k:>{maxlen}} | {json.dumps(v, indent=4, default=str)}")

        if self.open_install_dir:
            path = self._config.local_install_path
            LOGGER.info(f"opening '{path}'")
            webbrowser.open(str(path))

        if self.open_data_dir:
            path = self._filesystem.root_dir
            LOGGER.info(f"opening '{path}'")
            webbrowser.open(str(path))

    @property
    def open_install_dir(self):
        """
        Open the local installation directory for knots-hub in the system file explorer.
        """
        return self._args.open_install_dir

    @property
    def open_data_dir(self):
        """
        Open the local "data" directory for knots-hub in the system file explorer.
        """
        return self._args.open_data_dir

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        super().add_to_parser(parser)
        parser.add_argument(
            "--open-install-dir",
            action="store_true",
            help=cls.open_install_dir.__doc__,
        )
        parser.add_argument(
            "--open-data-dir",
            action="store_true",
            help=cls.open_data_dir.__doc__,
        )


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
        description="Uninstall the hub and its dependencies from the user system.",
    )
    UninstallParser.add_to_parser(subparser)

    subparser = subparsers.add_parser(
        "about",
        description="Display meta informations about knots hub itself.",
    )
    AboutParser.add_to_parser(subparser)

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
