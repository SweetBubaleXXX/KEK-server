import os

SEPARATOR = "/"


def split_into_components(path: str) -> list[str]:
    return os.path.normpath(path).strip(f" / \t\r\n").split(SEPARATOR)


def split_and_format(path: str) -> tuple[str, str]:
    return os.path.split(os.path.normpath(path).strip("/ \t\r\n"))
