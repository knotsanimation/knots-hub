import subprocess
from typing import Callable


def log_subprocess_result(
    result: subprocess.CompletedProcess,
    logger: Callable[[str], None],
):
    logger("_" * 50)

    if result.stdout:
        logger("|--- stdout: ---")
        for line in result.stdout.decode("utf-8").split("\n"):
            logger(f"| {line}")

    if result.stderr:
        logger("|--- stderr: ---")
        for line in result.stderr.decode("utf-8").split("\n"):
            logger(f"| {line}")

    logger("=" * 50)
