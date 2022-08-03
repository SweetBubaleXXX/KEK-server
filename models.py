from uuid import uuid4
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from .database import Base


class PublicKeyRecord(Base):
    __tablename__ = "public_keys"

    id = Column(String, primary_key=True)
    key_data = Column(String)

    folders = relationship("FolderRecord", backref="owner")


class FolderRecord(Base):
    __tablename__ = "folders"

    folder_id = Column(String, primary_key=True, default=uuid4)
    owner_id = Column(String, ForeignKey("public_keys.id"))
    folder_name = Column(String, default="/")
    parent_folder_id = Column(String,
                              ForeignKey("folders.folder_id"),
                              nullable=True)


class FileRecord(Base):
    __tablename__ = "files"

    file_id = Column(String, primary_key=True, default=uuid4)
    key_id = Column(String, ForeignKey("public_keys.id"))
    directory = Column(String, ForeignKey("folders.name"), default="/")
    filename = Column(String)
    link = Column(String, primary_key=True)
