from uuid import UUID

from pydantic import BaseModel


class PublicKeyInfo(BaseModel):
    key_id: str
    public_key: str


class CreateFolder(BaseModel):
    path: str
    recursive: bool = False


class TokenResponse(BaseModel):
    token: UUID


class DetailedTokenResponse(TokenResponse):
    detail: str
    registration_required: bool = False
