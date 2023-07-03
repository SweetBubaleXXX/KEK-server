from datetime import datetime
from typing import Annotated, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    relationship,
    mapped_column,
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    registry,
)

from ..schemas.base import FileInfo
from ..schemas.folders import FolderContent
from ..utils.path_utils import ROOT_PATH


mapper_reg = registry()


@mapper_reg.as_declarative_base()
class Base:
    pass


strpk = Annotated[str, mapped_column(primary_key=True)]
uuidpk = Annotated[
    str, mapped_column(primary_key=True, default=lambda: str(uuid4()), init=False)
]


@mapper_reg.mapped_as_dataclass
class KeyRecord(Base):
    __tablename__ = "public_keys"
    id: Mapped[strpk]
    public_key: Mapped[str]
    storage_size_limit: Mapped[int] = mapped_column(default=0)
    is_activated: Mapped[bool] = mapped_column(default=0)

    folders: Mapped[list["FolderRecord"]] = relationship(
        "FolderRecord",
        back_populates="owner",
        cascade="all, delete",
        default_factory=list,
    )


@mapper_reg.mapped_as_dataclass
class FolderRecord(Base):
    __tablename__ = "folders"

    id: Mapped[uuidpk]
    owner_id: Mapped[str] = mapped_column(ForeignKey("public_keys.id"))
    parent_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("folders.id"), default=None
    )
    name: Mapped[str] = mapped_column(default=ROOT_PATH)
    full_path: Mapped[str]

    owner: Mapped[KeyRecord] = relationship("KeyRecord", back_populates="folders")
    parent_folder: Mapped[Optional["FolderRecord"]] = relationship(
        "FolderRecord",
        back_populates="child_folders",
        remote_side=[id],
        uselist=False,
        default=None,
    )
    child_folders: Mapped[list["FolderRecord"]] = relationship(
        "FolderRecord",
        back_populates="parent_folder",
        cascade="all, delete",
        default_factory=list,
    )
    files: Mapped[list["FileRecord"]] = relationship(
        "FileRecord",
        back_populates="folder",
        cascade="all, delete",
        default_factory=list,
    )

    @hybrid_property
    def size(self) -> int:
        files_size = sum(file.size for file in self.files)
        child_folders_size = sum(folder.size for folder in self.child_folders)
        return files_size + child_folders_size

    def json(self) -> FolderContent:
        return FolderContent(
            files=map(lambda file: file.json(), self.files),
            folders=map(lambda folder: folder.name, self.child_folders),
        )


@mapper_reg.mapped_as_dataclass
class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[uuidpk]
    folder_id: Mapped[str] = mapped_column(ForeignKey("folders.id"))
    storage_id: Mapped[str] = mapped_column(ForeignKey("storages.id"))
    filename: Mapped[str]
    full_path: Mapped[str]
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    size: Mapped[int]

    folder: Mapped[FolderRecord] = relationship(
        "FolderRecord", back_populates="files", uselist=False
    )
    storage: Mapped["StorageRecord"] = relationship(
        "StorageRecord", back_populates="files", uselist=False
    )

    @hybrid_property
    def owner(self) -> KeyRecord:
        return self.folder.owner

    def json(self) -> FileInfo:
        return FileInfo(
            name=self.filename,
            size=self.size,
            last_modified=self.last_modified,
        )

    def update_timestamp(self) -> None:
        self.last_modified = datetime.utcnow()


@mapper_reg.mapped_as_dataclass
class StorageRecord(Base):
    __tablename__ = "storages"

    id: Mapped[strpk]
    url: Mapped[str]
    token: Mapped[str]
    used_space: Mapped[int] = mapped_column(default=0)
    capacity: Mapped[int]
    priority: Mapped[int] = mapped_column(default=1)

    files: Mapped[FileRecord] = relationship(
        "FileRecord", back_populates="storage", default_factory=list
    )

    @hybrid_property
    def free(self) -> int:
        return self.capacity - self.used_space


Record = KeyRecord | FolderRecord | FileRecord | StorageRecord
