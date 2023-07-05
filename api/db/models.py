from datetime import datetime
from typing import Annotated, Optional, TypeVar
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)

from ..schemas.base import FileInfo
from ..schemas.folders import FolderContent
from ..utils.path_utils import ROOT_PATH


class Base(AsyncAttrs, MappedAsDataclass, DeclarativeBase):
    pass


strpk = Annotated[str, mapped_column(primary_key=True)]
uuidpk = Annotated[
    str,
    mapped_column(primary_key=True, default=lambda: str(uuid4())),
]


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


class FolderRecord(Base):
    __tablename__ = "folders"

    id: Mapped[uuidpk] = mapped_column(init=False)
    owner_id: Mapped[str] = mapped_column(ForeignKey("public_keys.id"), default=None)
    parent_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("folders.id"), default=None
    )
    name: Mapped[str] = mapped_column(default=ROOT_PATH)
    full_path: Mapped[str] = mapped_column(default=ROOT_PATH)

    owner: Mapped[KeyRecord] = relationship(
        "KeyRecord", back_populates="folders", default=None
    )
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
    async def size(self) -> int:
        files_size = sum(file.size for file in await self.awaitable_attrs.files)
        child_folders_size = sum(
            folder.size for folder in await self.awaitable_attrs.child_folders
        )
        return files_size + child_folders_size

    async def json(self) -> FolderContent:
        return FolderContent(
            files=map(lambda file: file.json(), await self.awaitable_attrs.files),
            folders=map(
                lambda folder: folder.name, await self.awaitable_attrs.child_folders
            ),
        )


class FileRecord(Base):
    __tablename__ = "files"

    filename: Mapped[str]
    full_path: Mapped[str]
    size: Mapped[int]
    id: Mapped[uuidpk] = mapped_column(init=False)
    folder_id: Mapped[str] = mapped_column(ForeignKey("folders.id"), default=None)
    storage_id: Mapped[str] = mapped_column(ForeignKey("storages.id"), default=None)
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, init=False
    )

    folder: Mapped[FolderRecord] = relationship(
        "FolderRecord", back_populates="files", uselist=False, default=None
    )
    storage: Mapped["StorageRecord"] = relationship(
        "StorageRecord", back_populates="files", uselist=False, default=None
    )

    @hybrid_property
    async def owner(self) -> KeyRecord:
        folder = await self.awaitable_attrs.folder
        return await folder.awaitable_attrs.owner

    def json(self) -> FileInfo:
        return FileInfo(
            name=self.filename,
            size=self.size,
            last_modified=self.last_modified,
        )

    def update_timestamp(self) -> None:
        self.last_modified = datetime.utcnow()


class StorageRecord(Base):
    __tablename__ = "storages"

    id: Mapped[strpk]
    url: Mapped[str]
    token: Mapped[str]
    used_space: Mapped[int] = mapped_column(default=0)
    capacity: Mapped[int] = mapped_column(default=0)
    priority: Mapped[int] = mapped_column(default=1)

    files: Mapped[FileRecord] = relationship(
        "FileRecord", back_populates="storage", default_factory=list
    )

    @hybrid_property
    def free(self) -> int:
        return self.capacity - self.used_space


Record = TypeVar("Record", KeyRecord, FolderRecord, FileRecord, StorageRecord)
