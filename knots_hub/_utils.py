import contextlib
import os.path
import subprocess
import textwrap
from pathlib import Path


def expand_envvars(src_str: str) -> str:
    """
    Resolve environment variable pattern in the given string.

    Using ``os.path.expandvars`` but allow escaping using ``$$``
    """
    # temporary remove escape character
    new_str = src_str.replace("$$", "##tmp##")
    # environment variable expansion
    new_str = os.path.expandvars(new_str)
    # restore escaped character
    new_str = new_str.replace("##tmp##", "$")
    return new_str


@contextlib.contextmanager
def backup_environ(clear=True):
    """
    Context to back up the environ and restore it on exit.

    Args:
        clear: If true clear the environ before entering the context.
    """
    backup = os.environ.copy()
    if clear:
        os.environ.clear()
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(backup)


def format_subprocess_result(result: subprocess.CompletedProcess) -> str:
    """
    Create a human-readable string detailing the execution of a completed subprocess.

    As verbose as the subprocess was.
    """
    args = result.args
    if isinstance(args, (str, Path)):
        args = str(args)
    else:
        args = " ".join(args)

    stdout = result.stdout
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8")
    stdout = textwrap.indent(stdout, prefix="# ", predicate=lambda line: True)

    stderr = result.stderr
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8")
    stderr = textwrap.indent(stderr, prefix="# ", predicate=lambda line: True)

    message = f"completed process '{args}' with exit code {result.returncode}\n"
    message += f"======[stdout]======:\n{stdout}"
    message += f"======[stderr]======:\n{stderr}"
    message += f"====== end ======"
    return message
