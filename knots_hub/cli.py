import abc
import argparse
import logging
import os
import shutil
import sys
from typing import List
from typing import Type

import kloch
from pythonning.benchmark import timeit

import knots_hub
from knots_hub import HubInstallFilesystem
from knots_hub import HubConfig
import knots_hub.installer
from knots_hub.installer import InstallerList

LOGGER = logging.getLogger(__name__)


def get_restart_args(
    current_argv: List[str],
    restarted_amount: int = 0,
    apply_update: int = 0,
) -> List[str]:
    """
    Get the args to pass to ``os.exec*``
    """
    argv = ["knots_hub"]  # program name expected by os.exec*
    argv += ["--restarted__", str(restarted_amount + 1)]

    new_argv = current_argv.copy()

    if "__applyupdate" in new_argv:
        applyupdate_index = new_argv.index("__applyupdate")
        if apply_update:
            # imply usually the restart called at applyupdate stage 1
            new_argv.pop(applyupdate_index + 1)
            new_argv.insert(applyupdate_index + 1, str(apply_update))
        else:
            # imply usually the restart called at applyupdate stage 2
            new_argv.pop(applyupdate_index)
            new_argv.pop(applyupdate_index)

    elif apply_update:
        new_argv = ["__applyupdate", str(apply_update)] + new_argv

    if "--restarted__" in new_argv:
        index = new_argv.index("--restarted__")
        # remove the arg and its value
        new_argv.pop(index)
        new_argv.pop(index)

    argv += new_argv
    return argv


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
        original_argv: List[str],
        config: HubConfig,
        filesystem: HubInstallFilesystem,
        extra_args: List[str],
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
        # an empty installer list imply the hub is never installed/updated locally
        installer_list = None
        installer_list_path = self._config.installer_list_path
        if installer_list_path:
            installer_list = InstallerList.from_file(path=installer_list_path)

        # check installed
        if installer_list and not self._filesystem.is_installed:
            src_path = installer_list.last_path
            LOGGER.info(f"installing hub '{src_path}'")
            with timeit("installing took ", LOGGER.info):
                exe_path = knots_hub.installer.install_hub(
                    install_src_path=src_path,
                    filesystem=self._filesystem,
                )
            sys.exit(self._restart_hub(exe=str(exe_path)))

        # finalize update that took place previously
        if self._filesystem.install_old_dir.exists():
            old_dir = self._filesystem.install_old_dir
            LOGGER.debug(f"shutil.rmtree('{old_dir}')")
            shutil.rmtree(old_dir)

        # check up-to-date (only if there was no "old-dir" which implied an update all-ready just occurred.)
        elif not knots_hub.installer.is_hub_up_to_date(installer_list):
            src_path = installer_list.last_path
            LOGGER.info(f"updating hub to '{src_path}'")
            with timeit("updating took ", LOGGER.info):
                exe_path = knots_hub.installer.update_hub(
                    update_src_path=src_path,
                    filesystem=self._filesystem,
                )
            sys.exit(self._restart_hub(exe=str(exe_path), apply_update=1))

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
            "--restarted__",
            dest="_restarted",
            default=0,
            type=int,
            help=argparse.SUPPRESS,
        )
        parser.set_defaults(func=cls)

    def _restart_hub(self, exe: str, apply_update: int = 0):
        """
        ! Anything after this function is not called.

        Args:
            exe: filesystem path to an existing hub executable
            apply_update: which stage of update to apply on restart
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
            apply_update=apply_update,
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
        print("hub launched")

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        super().add_to_parser(parser)


class KlochParser(BaseParser):
    """
    A "kloch" subcommand, to start the kloch CLI.
    """

    def execute(self):
        super().execute()
        # plugins added in pyproject.toml
        os.environ["KLOCH_CONFIG_LAUNCHER_PLUGINS"] = "kloch_rezenv,kloch_kiche"

        argv = self._extra_args + (["--debug"] if self.debug else [])
        LOGGER.debug(f"using {kloch.__name__} v{kloch.__version__}")
        LOGGER.debug(f"kloch.get_cli({argv})")
        cli = kloch.get_cli(argv=argv)
        cli.execute()

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        super().add_to_parser(parser)


class ApplyUpdateParser(BaseParser):
    """
    An "applyupdate" sub-command which is only intended to be used internally.

    XXX: logic/api modification need to be propagated in `get_restart_args`
    """

    @property
    def stage(self) -> int:
        """
        The stage at which the update must be applied (updates are 2 stages process).
        """
        return self._args.stage

    def execute(self):
        if self.stage == 1:
            LOGGER.info("applying update stage 1")
            old_path = self._filesystem.install_src_dir
            new_path = self._filesystem.install_old_dir
            LOGGER.debug(f"renaming '{old_path}' to '{new_path}'")
            old_path.rename(new_path)

            exe = str(self._filesystem.exe_old)
            sys.exit(self._restart_hub(exe=exe, apply_update=2))

        if self.stage == 2:
            LOGGER.info("applying update stage 2")
            old_path = self._filesystem.install_new_dir
            new_path = self._filesystem.install_src_dir
            LOGGER.debug(f"renaming '{old_path}' to '{new_path}'")
            old_path.rename(new_path)

            exe = str(self._filesystem.exe_src)
            sys.exit(self._restart_hub(exe=exe))

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser):
        super().add_to_parser(parser)
        parser.add_argument(
            "stage",
            type=int,
            help=cls.stage.__doc__,
        )


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
    argv: List[str] = None,
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
        "kloch",
        add_help=False,
        description="Call the Kloch CLI with all arguments redirected to it.",
    )
    KlochParser.add_to_parser(subparser)

    subparser = subparsers.add_parser(
        "__applyupdate",
        add_help=False,
    )
    ApplyUpdateParser.add_to_parser(subparser)

    subparser = subparsers.add_parser(
        "uninstall",
        description="Uninstall the hub from the user system.",
    )
    UninstallParser.add_to_parser(subparser)

    argv: List[str] = sys.argv[1:] if argv is None else argv.copy()
    # allow unknown args for when we restart with `applyupdate`
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
