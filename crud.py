from typing import Optional
import os

from sqlalchemy.orm import Session

import models
import schemas


def add_key_record(db: Session,
                   public_key: schemas.PublicKeyInfo) -> models.KeyRecord:
    key_record = models.KeyRecord(public_key)
    db.add(key_record)
    db.commit()
    db.refresh(key_record)
    return key_record


def create_folder_record(db: Session,
                         key_id: str,
                         path: str):
    folder_names = os.path.normpath(path.strip("/")).split(os.sep)
    for folder in folder_names:
        existing_folder = db.query(models.FolderRecord).filter_by(
            folder_name=folder
        ).first()


def create_file_record(db: Session,
                       key_id: str,
                       link: str,
                       filename: str,
                       directory: Optional[str] = None) -> models.FileRecord:
    file_record = models.FileRecord(*{key_id, filename, link, directory})
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


def get_file_link(db: Session,
                  key_id: str,
                  filename: str,
                  directory: str) -> str | None:
    file_record = db.query(models.FileRecord).filter_by(
        owner_id=key_id,
        folder_id=directory,
        filename=filename
    ).first()
    return file_record and file_record.link


def list_files_in_dir(db: Session,
                      key_id: str,
                      directory: str,
                      offset: int = 0,
                      limit: int = 200) -> list[models.FileRecord | None]:
    return db.query(models.FileRecord).filter(
        models.FileRecord.owner_id == key_id,
        models.FileRecord.folder_id == directory
    ).offset(offset).limit(limit).all()
