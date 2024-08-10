import enum
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Union


class Colors(enum.Enum):
    reset = "\x1b[0m"
    black = "\x1b[30m"
    black_bold = "\x1b[30;1m"
    black_faint = "\x1b[30;2m"
    red = "\x1b[31m"
    red_bold = "\x1b[31;1m"
    red_faint = "\x1b[31;2m"
    green = "\x1b[32m"
    green_bold = "\x1b[32;1m"
    green_faint = "\x1b[32;2m"
    yellow = "\x1b[33m"
    yellow_bold = "\x1b[33;1m"
    yellow_faint = "\x1b[33;2m"
    blue = "\x1b[34m"
    blue_bold = "\x1b[34;1m"
    blue_faint = "\x1b[34;2m"
    magenta = "\x1b[35m"
    magenta_bold = "\x1b[35;1m"
    magenta_faint = "\x1b[35;2m"
    cyan = "\x1b[36m"
    cyan_bold = "\x1b[36;1m"
    cyan_faint = "\x1b[36;2m"
    white = "\x1b[37m"
    white_bold = "\x1b[37;1m"
    white_faint = "\x1b[37;2m"
    grey = "\x1b[39m"


class ColoredFormatter(logging.Formatter):

    COLOR_BY_LEVEL = {
        logging.DEBUG: Colors.white_faint,
        logging.INFO: Colors.blue,
        logging.WARNING: Colors.yellow,
        logging.ERROR: Colors.red,
        logging.CRITICAL: Colors.red_bold,
    }

    def __init__(self, disable_coloring: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._disable_coloring = disable_coloring

    def format(self, record):
        on = not self._disable_coloring
        level_color = self.COLOR_BY_LEVEL.get(record.levelno, None)
        if level_color:
            record.level_color = level_color.value if on else ""
        for color in Colors:
            setattr(record, color.name, color.value if on else "")

        message = super().format(record)
        if not message.endswith(Colors.reset.value) and on:
            message += Colors.reset.value
        return message


def configure_logging(
    log_level: Union[int, str],
    log_path: Path,
    disable_coloring: bool = False,
):

    disk_formatter = logging.Formatter(
        "{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
    )
    stream_formatter = ColoredFormatter(
        disable_coloring=disable_coloring,
        fmt="{level_color}{levelname: <7}{reset}{white_faint} | {asctime} [{name}]{reset}{level_color} {message}",
        style="{",
    )

    # XXX: this will affect other libraries logging
    logging.root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(stream_formatter)
    logging.root.addHandler(handler)

    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=65536,
        # need at least one backup to rotate
        backupCount=1,
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(disk_formatter)
    logging.root.addHandler(handler)
