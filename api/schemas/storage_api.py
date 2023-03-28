from pydantic import BaseModel, Field, validator


class StorageRequestHeaders(BaseModel):
    authorization: str

    @validator("authorization", pre=True)
    def parse_authorization(cls, v):
        return f"Bearer {v}"


class UploadRequestHeaders(StorageRequestHeaders):
    file_size: int = Field(0, alias="File-Size")

    class Config:
        allow_population_by_field_name = True


class StorageSpaceResponse(BaseModel):
    capacity: int
    used: int
