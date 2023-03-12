from pydantic import BaseModel, Field


class UploadRequestHeaders(BaseModel):
    file_size: int = Field(0, alias="File-Size")

    class Config:
        allow_population_by_field_name = True


class UploadResponse(BaseModel):
    capacity: int
    used: int
