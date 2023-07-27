import posixpath

ROOT_PATH = posixpath.sep


def normalize(path: str) -> str:
    if path == ROOT_PATH:
        return path
    return posixpath.normpath(path).rstrip(posixpath.sep)


def split_into_components(path: str) -> list[str]:
    return normalize(path).lstrip(posixpath.sep).split(posixpath.sep)


def split_head_and_tail(path: str) -> tuple[str, str]:
    return posixpath.split(normalize(path))


def add_trailing_slash(path: str) -> str:
    if path.endswith(posixpath.sep):
        return path
    return f"{path}{posixpath.sep}"
