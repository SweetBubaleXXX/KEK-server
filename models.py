from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class PublicKeyRecord(Base):
    __tablename__ = "public_keys"

    id = Column(String, primary_key=True)
    key_data = Column(String)

    files = relationship("FileRecord", backref="owner")


class FileRecord(Base):
    __tablename__ = "files"

    key_id = Column(String, ForeignKey("public_keys.id"))
    directory = Column(String, default="/")
    filename = Column(String)
    link = Column(String, primary_key=True)
