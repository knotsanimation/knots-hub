import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

import knots_hub
from knots_hub.constants import OS
from knots_hub.constants import IS_APP_FROZEN
from knots_hub.constants import INTERPRETER_PATH
from knots_hub._logging import configure_logging

LOGGER = logging.getLogger(__name__)


def main(argv: Optional[list[str]] = None, logging_configuration: bool = False):
    """
    Args:
        argv: command line arguments. from sys.argv if not provided
        logging_configuration: True to configure logging system.
    """

    config = knots_hub.HubConfig.from_environment()
    filesystem = knots_hub.HubLocalFilesystem()
    filesystem.root_dir.mkdir(exist_ok=True)

    cli = knots_hub.get_cli(argv=argv, config=config, filesystem=filesystem)

    log_level = logging.DEBUG if cli.debug else logging.INFO
    if logging_configuration:
        configure_logging(
            log_level=log_level,
            log_path=filesystem.log_path,
            disable_coloring=cli.no_coloring,
        )

    exe: Path = INTERPRETER_PATH

    LOGGER.debug(
        f"starting {knots_hub.__name__} v{knots_hub.__version__} "
        f"(frozen={IS_APP_FROZEN})(exe={exe})"
    )
    LOGGER.debug(f"retrieved cli with args={cli._args}")
    LOGGER.debug(f"config={config}")

    # probably a nuitka compiling bug ?
    if not exe.exists():
        LOGGER.error(f"The current system executable '{exe}' doesn't exist")
        sys.exit(-1)

    if not OS.is_windows():
        LOGGER.error(f"OSError: Unsupported operating system '{OS}'")
        sys.exit(-1)

    # noinspection PyBroadException
    try:
        exitcode = cli.execute()
    except Exception:
        LOGGER.exception(f"Unexpected exception while executing '{sys.argv}'")
        exitcode = -1

    sys.exit(exitcode)


if __name__ == "__main__":
    main(logging_configuration=True)  # pragma: no cover
