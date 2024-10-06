import contextlib
import os.path


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
