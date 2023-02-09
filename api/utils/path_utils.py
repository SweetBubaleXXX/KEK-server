import posixpath

ROOT_PATH = "/"
SEPARATOR = "/"


def split_into_components(path: str) -> list[str]:
    return posixpath.normpath(path).removeprefix(ROOT_PATH).strip(SEPARATOR).split(SEPARATOR)


def split_head_and_tail(path: str) -> tuple[str, str]:
    return posixpath.split(posixpath.normpath(path).rstrip(SEPARATOR))
