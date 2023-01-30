import os


def split_into_components(path: str) -> list[str]:
    return os.path.normpath(path.strip("/")).split(os.sep)


def split_and_format(path: str) -> tuple[str, str]:
    return os.path.split(os.path.normpath(path.strip("/")))
