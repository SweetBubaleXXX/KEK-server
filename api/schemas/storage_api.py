from pydantic import BaseModel, validator


class StorageRequestHeaders(BaseModel):
    authorization: str

    @validator("authorization", pre=True)
    def parse_authorization(cls, v):
        return f"Bearer {v}"


class UploadRequestHeaders(StorageRequestHeaders):
    file_size: str | int = "0"

    @validator("file_size")
    def parse_file_size(cls, v):
        return str(v)

    class Config:
        fields = {"file_size": "File-Size"}
        allow_population_by_field_name = True


class StorageSpaceResponse(BaseModel):
    capacity: int
    used: int
