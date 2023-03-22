from pydantic import BaseModel, validator

from .base import FileInfo, Item


class CreateFolder(Item):
    recursive: bool = False


class FolderContent(BaseModel):
    files: list[FileInfo]
    folders: list[str]

    @validator("files", "folders", pre=True)
    def validate_iterable(cls, v):
        if isinstance(v, list):
            return v
        return list(v)
