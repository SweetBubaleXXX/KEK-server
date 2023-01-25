from uuid import UUID

from pydantic import BaseModel


class PublicKeyInfo(BaseModel):
    key_id: str
    public_key: str


class TokenResponse(BaseModel):
    token: UUID


class DetailedTokenResponse(TokenResponse):
    detail: str
    registration_required: bool = False
