from pydantic import BaseModel


class CreateFolder(BaseModel):
    path: str
    recursive: bool = False
