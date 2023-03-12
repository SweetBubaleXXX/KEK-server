from pydantic import BaseModel, root_validator


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
