from typing import Optional

from sqlalchemy.orm import Session

from . import models, schemas


def create_file_record(db: Session,
                       key_id: str,
                       link: str,
                       filename: str,
                       directory: Optional[str] = None) -> models.FileRecord:
    file_record = models.FileRecord(**{key_id, filename, link, directory})
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


def get_file_link(db: Session,
                  key_id: str,
                  filename: str,
                  directory: str) -> str | None:
    file_record = db.query(models.FileRecord).filter(
        models.FileRecord.key_id == key_id,
        models.FileRecord.directory == directory,
        models.FileRecord.filename == filename
    ).first()
    return file_record and file_record.link


def list_files_in_dir(db: Session,
                      key_id: str,
                      directory: str,
                      offset: int = 0,
                      limit: int = 200) -> list[models.FileRecord | None]:
    db.query(models.FileRecord).filter(
        models.FileRecord.key_id == key_id,
        models.FileRecord.directory == directory
    ).offset(offset).limit(limit).all()
