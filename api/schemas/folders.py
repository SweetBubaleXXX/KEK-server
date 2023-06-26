from typing import Iterable

from pydantic import BaseModel, validator

from .base import FileInfo, ItemRequest


class CreateFolderRequest(ItemRequest):
    recursive: bool = False


class FolderContent(BaseModel):
    files: list[FileInfo] | Iterable[FileInfo]
    folders: list[str] | Iterable[str]

    @validator("files", "folders", pre=True)
    def validate_iterable(cls, v):
        if isinstance(v, list):
            return v
        return list(v)
