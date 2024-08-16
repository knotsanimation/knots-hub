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
