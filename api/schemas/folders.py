from typing import Iterable

from pydantic import BaseModel, validator

from .base import Item


class CreateFolder(Item):
    recursive: bool = False


class FolderContent(BaseModel):
    files: list[str]
    folders: list[str]

    @validator("files", "folders", pre=True)
    def validate_iterable(cls, v):
        if isinstance(v, list):
            return v
        return list(v)
