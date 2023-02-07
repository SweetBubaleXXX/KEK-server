import os

SEPARATOR = "/"


def _normalize_path(path: str) -> str:
    return os.path.normpath(path).strip(SEPARATOR)


def split_into_components(path: str) -> list[str]:
    return _normalize_path(path).split(SEPARATOR)


def split_head_and_tail(path: str) -> tuple[str, str]:
    return os.path.split(_normalize_path(path))
