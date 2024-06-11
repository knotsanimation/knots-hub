import logging
import logging.handlers
import sys
from typing import List
from typing import Optional

import knots_hub
from knots_hub.constants import OS
from knots_hub.constants import IS_APP_FROZEN

LOGGER = logging.getLogger(__name__)


def main(argv: Optional[List[str]] = None):
    """
    Args:
        argv: command line arguments. from sys.argv if not provided
    """

    config = knots_hub.HubConfig.from_environment()
    filesystem = knots_hub.HubInstallFilesystem(root=config.local_install_path)
    filesystem.root.mkdir(exist_ok=True)

    cli = knots_hub.get_cli(argv=argv, config=config, filesystem=filesystem)

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
        filesystem.log_path,
        maxBytes=65536,
        # need at least one backup to rotate
        backupCount=1,
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)

    LOGGER.debug(
        f"starting {knots_hub.__name__} v{knots_hub.__version__} (frozen={IS_APP_FROZEN})"
    )
    LOGGER.debug(f"retrieved cli with args={cli._args}")

    if not OS.is_windows():
        raise OSError(f"Unsupported Operating System '{OS}'.")

    sys.exit(cli.execute())


if __name__ == "__main__":
    main()  # pragma: no cover
