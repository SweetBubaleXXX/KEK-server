from pydantic import BaseModel


class FileInfo(BaseModel):
    key_id: str
    path: str

    class Config:
        orm_mode = True


class FileData(FileInfo):
    file: bytes


class SignedFileInfo(FileInfo):
    signed_path: str


class SignedFileData(SignedFileInfo, FileData):
    pass


class PublicKeyInfo(BaseModel):
    id: str
    public_key: str

    class Config:
        orm_mode = True


class SignedPublicKey(PublicKeyInfo):
    signed_key_id: str
