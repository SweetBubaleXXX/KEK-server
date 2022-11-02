from uuid import UUID

from pydantic import BaseModel


class BaseRequest(BaseModel):
    key_id: str


class SignedRequest(BaseRequest):
    signed_token: str | None


class FileInfo(BaseRequest):
    path: str


class SignedFileInfo(FileInfo, SignedRequest):
    pass


class FileData(FileInfo):
    file: bytes


class SignedFileData(SignedFileInfo, FileData):
    pass


class PublicKeyInfo(BaseRequest):
    public_key: str


class SignedPublicKeyInfo(PublicKeyInfo, SignedRequest):
    pass


class TokenResponse(BaseModel):
    token: UUID


class DetailedTokenResponse(TokenResponse):
    detail: str
