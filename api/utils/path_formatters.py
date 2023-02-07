import os

SEPARATOR = "/"


def split_into_components(path: str) -> list[str]:
    return os.path.normpath(path).strip(SEPARATOR).split(SEPARATOR)


def split_head_and_tail(path: str) -> tuple[str, str]:
    return os.path.split(os.path.normpath(path).rstrip(SEPARATOR))
