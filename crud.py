import os
from typing import Optional

from sqlalchemy.orm import Session

import models


def add_key(db: Session,
            key_id: str,
            public_key: str) -> models.KeyRecord:
    key_record = models.KeyRecord(
        id=key_id,
        public_key=public_key
    )
    db.add(key_record)
    db.commit()
    db.refresh(key_record)
    return key_record


def find_folder(db: Session,
                **filters) -> models.FolderRecord | None:
    return db.query(models.FolderRecord).filter_by(**filters).first()


def create_root_folder(db: Session,
                       owner_id: str) -> models.FolderRecord:
    root_folder = models.FolderRecord(
        owner_id=owner_id,
        folder_name=models.ROOT_PATH,
        full_path=models.ROOT_PATH
    )
    db.add(root_folder)
    db.commit()
    db.refresh(root_folder)
    return root_folder


def create_child_folder(db: Session,
                        parent_folder: models.FolderRecord,
                        folder_name: str) -> models.FolderRecord | None:
    child_folder = models.FolderRecord(
        owner_id=parent_folder.owner_id,
        folder_name=folder_name,
        full_path=os.path.join(parent_folder.full_path, folder_name)
    )
    parent_folder.child_folders.append(child_folder)
    db.add(parent_folder)
    db.commit()
    db.refresh(child_folder)
    return child_folder


def upload_file_to_folder(db: Session,
                          folder: models.FolderRecord,
                          filename: str) -> models.FileRecord:
    existing_file = next(filter(
        lambda file: file.filename == filename,
        folder.files
    ), None)
    file_record = existing_file or models.FileRecord(
        folder_id=folder.folder_id,
        filename=filename,
        full_path=os.path.join(folder.full_path, filename)
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


# def upload_file(db: Session,
#                 file_info: schemas.FileInfo) -> models.FileRecord:
#     folder_path, filename = os.path.split(
#         os.path.normpath(file_info.path.strip("/")))
#     existing_folder = find_folder(
#         db,
#         owner_id=file_info.key_id,
#         full_path=folder_path or models.ROOT_PATH
#     )
#     if existing_folder is None:
#         pass
#     existing_file = next(filter(
#         lambda file: file.filename == filename,
#         folder.files
#     ), None)
#     if existing_file:
#         return existing_file
#     db.add(file_record)
#     db.commit()
#     db.refresh(file_record)
#     return file_record


# def get_file_link(db: Session,
#                   key_id: str,
#                   filename: str,
#                   directory: str) -> str | None:
#     file_record = db.query(models.FileRecord).filter_by(
#         owner_id=key_id,
#         folder_id=directory,
#         filename=filename
#     ).first()
#     return file_record and file_record.link


# def list_files_in_dir(db: Session,
#                       key_id: str,
#                       directory: str,
#                       offset: int = 0,
#                       limit: int = 200) -> list[models.FileRecord | None]:
#     return db.query(models.FileRecord).filter(
#         models.FileRecord.owner_id == key_id,
#         models.FileRecord.folder_id == directory
#     ).offset(offset).limit(limit).all()
