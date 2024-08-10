import logging
import logging.handlers
import sys
from typing import List
from typing import Optional

import knots_hub
from knots_hub.constants import OS
from knots_hub.constants import IS_APP_FROZEN
from knots_hub._logging import configure_logging

LOGGER = logging.getLogger(__name__)


def main(argv: Optional[List[str]] = None, logging_configuration: bool = False):
    """
    Args:
        argv: command line arguments. from sys.argv if not provided
        logging_configuration: True to configure logging system.
    """

    config = knots_hub.HubConfig.from_environment()
    filesystem = knots_hub.HubInstallFilesystem(root=config.local_install_path)
    filesystem.root.mkdir(exist_ok=True)

    cli = knots_hub.get_cli(argv=argv, config=config, filesystem=filesystem)

    log_level = logging.DEBUG if cli.debug else logging.INFO
    if logging_configuration:
        configure_logging(
            log_level=log_level,
            log_path=filesystem.log_path,
            disable_coloring=cli.no_coloring,
        )

    LOGGER.debug(
        f"starting {knots_hub.__name__} v{knots_hub.__version__} (frozen={IS_APP_FROZEN})"
    )
    LOGGER.debug(f"retrieved cli with args={cli._args}")
    LOGGER.debug(f"config={config}")

    if not OS.is_windows():
        OS.raise_unsupported()

    sys.exit(cli.execute())


if __name__ == "__main__":
    main(logging_configuration=True)  # pragma: no cover
