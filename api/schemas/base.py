from datetime import datetime

from pydantic import BaseModel, Field, root_validator, validator

from ..utils.path_utils import add_trailing_slash, normalize


class ItemRequest(BaseModel):
    path: str = Field(..., regex=r"^/[\w+/]+$")

    @validator("path")
    def normalize_path(cls, v):
        return normalize(v)


class RenameItemRequest(ItemRequest):
    new_name: str = Field(..., regex=r"^[\w+]+$")


class MoveItemRequest(ItemRequest):
    destination: str = Field(..., regex=r"^/[\w+/]+$")

    _normalize_destination = validator("destination", allow_reuse=True)(normalize)

    @root_validator(skip_on_failure=True)
    def validate_destination_path(cls, values):
        path = values["path"]
        destination = values["destination"]
        if destination == path or destination.startswith(add_trailing_slash(path)):
            raise ValueError("Destination should be a higher level directory")
        return values


class StorageInfoResponse(BaseModel):
    used: int
    limit: int


class FileInfo(BaseModel):
    name: str
    size: int
    last_modified: datetime
