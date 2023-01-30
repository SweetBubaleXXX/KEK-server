from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..config import settings
from .engine import Base

ROOT_PATH = "/"


class KeyRecord(Base):
    __tablename__ = "public_keys"

    id = Column(String, primary_key=True)
    public_key = Column(String)
    storage_size_limit = Column(Integer, default=settings.user_storage_size_limit)
    is_activated = Column(Integer, default=settings.user_is_activated_default)

    folders = relationship("FolderRecord", backref="owner")


class FolderRecord(Base):
    __tablename__ = "folders"

    folder_id = Column(String, primary_key=True, default=uuid4)
    owner_id = Column(String, ForeignKey("public_keys.id"))
    parent_folder_id = Column(String,
                              ForeignKey("folders.folder_id"),
                              nullable=True)
    folder_name = Column(String, default=ROOT_PATH)
    full_path = Column(String)

    child_folders = relationship("FolderRecord",
                                 remote_side=[folder_id],
                                 uselist=True)
    files = relationship("FileRecord", backref="folder", uselist=True)


class FileRecord(Base):
    __tablename__ = "files"

    file_id = Column(String, primary_key=True, default=uuid4)
    folder_id = Column(String, ForeignKey("folders.folder_id"))
    storage_id = Column(String, ForeignKey("storages.id"))
    filename = Column(String)
    full_path = Column(String)
    last_modified = Column(DateTime, onupdate=datetime.utcnow)
    size = Column(Integer)


class StorageRecord(Base):
    __tablename__ = "storages"

    id = Column(String, primary_key=True)
    url = Column(String)
    token = Column(String)
    used_space = Column(Integer, default=0)
    capacity = Column(Integer)
    priority = Column(Integer, default=1)
