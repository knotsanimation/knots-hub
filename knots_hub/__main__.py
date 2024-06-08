import logging
import logging.handlers
import sys
from typing import List
from typing import Optional

import knots_hub
from knots_hub.constants import LOCAL_ROOT_FILESYSTEM
from knots_hub.constants import OS

LOGGER = logging.getLogger(__name__)


def main(argv: Optional[List[str]] = None):
    """
    Args:
        argv: command line arguments. from sys.argv if not provided
    """
    cli = knots_hub.get_cli(argv=argv)

    log_level = logging.DEBUG if cli.debug else logging.INFO

    formatter = logging.Formatter(
        "{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
    )
    # XXX: this will affect other libraries logging
    logging.root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)

    handler = logging.handlers.RotatingFileHandler(
        LOCAL_ROOT_FILESYSTEM.log_path,
        maxBytes=65536,
        # need at least one backup to rotate
        backupCount=1,
        encoding="utf-8",
        # the parent directory might not be created yet so delay
        delay=True,
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)

    initialized = LOCAL_ROOT_FILESYSTEM.initialize()

    # it is now possible to log

    LOGGER.debug(f"starting {knots_hub.__name__} v{knots_hub.__version__}")
    if initialized:
        LOGGER.debug(f"initialized filesystem '{LOCAL_ROOT_FILESYSTEM}'")
    LOGGER.debug(f"retrieved cli with args={cli._args}")

    if not OS.is_windows():
        raise OSError(f"Unsupported Operating System '{OS}'.")

    sys.exit(cli.execute())


if __name__ == "__main__":
    main()  # pragma: no cover
