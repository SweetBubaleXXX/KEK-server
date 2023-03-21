import posixpath

ROOT_PATH = "/"
SEPARATOR = "/"


def normalize(path: str) -> str:
    return posixpath.normpath(path).rstrip(SEPARATOR)


def split_into_components(path: str) -> list[str]:
    return normalize(path).split(SEPARATOR)


def split_head_and_tail(path: str) -> tuple[str, str]:
    return posixpath.split(normalize(path))
