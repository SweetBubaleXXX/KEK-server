from datetime import datetime

from pydantic import BaseModel, root_validator, validator

from ..utils.path_utils import normalize


class Item(BaseModel):
    path: str

    @validator("path")
    def normalize_path(cls, v):
        return normalize(v)


class RenameItem(Item):
    new_name: str


class MoveItem(BaseModel):
    path: str
    destination: str

    _normalize_destination = validator("destination", allow_reuse=True)(normalize)

    @root_validator
    def validate_destination_path(cls, values):
        path = values["path"]
        destination = values["destination"]
        if destination.startswith(path):
            raise ValueError("Destination should be a higher level directory")
        return values


class FileInfo(BaseModel):
    filename: str
    last_modified: datetime
    size: int
