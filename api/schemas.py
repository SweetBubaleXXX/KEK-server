from uuid import UUID

from pydantic import BaseModel, root_validator


class PublicKeyInfo(BaseModel):
    key_id: str
    public_key: str


class TokenResponse(BaseModel):
    token: UUID


class DetailedTokenResponse(TokenResponse):
    detail: str
    registration_required: bool = False


class CreateFolder(BaseModel):
    path: str
    recursive: bool = False


class RenameItem(BaseModel):
    path: str
    new_name: str


class MoveItem(BaseModel):
    path: str
    destination: str

    @root_validator
    def validate_destination_path(cls, values):
        path = values["path"]
        destination = values["destination"]
        if destination.startswith(path):
            raise ValueError("Destination should be a higher level directory")
        return values
