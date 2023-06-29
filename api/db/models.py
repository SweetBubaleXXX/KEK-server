from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ..schemas.base import FileInfo
from ..schemas.folders import FolderContent
from ..utils.path_utils import ROOT_PATH
from .engine import Base


class KeyRecord(Base):
    __tablename__ = "public_keys"
    id = Column(String, primary_key=True)
    public_key = Column(String)
    storage_size_limit = Column(Integer, default=0, nullable=False)
    is_activated = Column(Integer, default=0, nullable=False)

    folders = relationship(
        "FolderRecord", back_populates="owner", cascade="all, delete"
    )


class FolderRecord(Base):
    __tablename__ = "folders"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    owner_id = Column(String, ForeignKey("public_keys.id"))
    parent_id = Column(String, ForeignKey("folders.id"), nullable=True)
    name = Column(String, default=ROOT_PATH)
    full_path = Column(String)

    owner = relationship("KeyRecord", back_populates="folders")
    parent_folder = relationship(
        "FolderRecord", back_populates="child_folders", remote_side=[id], uselist=False
    )
    child_folders = relationship(
        "FolderRecord", back_populates="parent_folder", cascade="all, delete"
    )
    files = relationship("FileRecord", back_populates="folder", cascade="all, delete")

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


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    folder_id = Column(String, ForeignKey("folders.id"))
    storage_id = Column(String, ForeignKey("storages.id"))
    filename = Column(String)
    full_path = Column(String)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    size = Column(Integer)

    folder = relationship("FolderRecord", back_populates="files", uselist=False)
    storage = relationship("StorageRecord", back_populates="files", uselist=False)

    @hybrid_property
    def owner(self) -> KeyRecord:
        return self.folder.owner

    def json(self) -> FileInfo:
        return FileInfo(
            name=self.filename,
            size=self.size,
            last_modified=self.last_modified,
        )

    def update_timestamp(self):
        self.last_modified = datetime.utcnow()


class StorageRecord(Base):
    __tablename__ = "storages"

    id = Column(String, primary_key=True)
    url = Column(String)
    token = Column(String)
    used_space = Column(Integer, default=0)
    capacity = Column(Integer)
    priority = Column(Integer, default=1)

    files = relationship("FileRecord", back_populates="storage")

    @hybrid_property
    def free(self) -> int:
        return self.capacity - self.used_space


Record = KeyRecord | FolderRecord | FileRecord | StorageRecord
