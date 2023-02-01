import os

from sqlalchemy.orm import Session

from .. import config
from ..utils.path_formatters import split_into_components
from . import models
from .engine import Base


def _get_child_folder(parent_folder: models.FolderRecord,
                      child_name: str) -> models.FolderRecord | None:
    return next(filter(
        lambda child: child.folder_name == child_name,
        parent_folder.child_folders
    ), None)


def _get_child_file(parent_folder: models.FolderRecord,
                    filename: str) -> models.FileRecord | None:
    return next(filter(
        lambda child_file: child_file.filename == filename,
        parent_folder.files
    ), None)


def _update_record(db: Session, record: Base) -> Base:
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_key(db: Session, key_id: str) -> models.KeyRecord | None:
    return db.query(models.KeyRecord).filter_by(id=key_id).first()


def add_key(db: Session,
            key_id: str,
            public_key: str,
            storage_size_limit: int | None = None,
            is_activated: bool | None = None) -> models.KeyRecord:
    key_record = models.KeyRecord(
        id=key_id,
        public_key=public_key,
        storage_size_limit=storage_size_limit or config.settings.user_storage_size_limit,
        is_activated=is_activated or config.settings.user_is_activated_default
    )
    return _update_record(db, key_record)


def find_folder(db: Session, **filters) -> models.FolderRecord | None:
    return db.query(models.FolderRecord).filter_by(**filters).first()


def create_or_return_root_folder(db: Session,
                                 key_record: models.KeyRecord) -> models.FolderRecord:
    existing_folder_record = db.query(models.FolderRecord).filter_by(
        owner=key_record,
        full_path=models.ROOT_PATH
    ).first()
    if existing_folder_record:
        return existing_folder_record
    folder_record = models.FolderRecord(
        owner_id=key_record.id,
        folder_name=models.ROOT_PATH,
        full_path=models.ROOT_PATH
    )
    key_record.folders.append(folder_record)
    _update_record(db, key_record)
    return folder_record


def create_child_folder(db: Session,
                        parent_folder: models.FolderRecord,
                        folder_name: str) -> models.FolderRecord:
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


def create_folders_recursively(db: Session,
                               owner_id: str,
                               folder_path: str) -> models.FolderRecord:
    path_components = split_into_components(folder_path)
    parent_folder = create_or_return_root_folder(db, owner_id)
    for folder_name in path_components:
        existing_child = _get_child_folder(parent_folder, folder_name)
        if existing_child:
            parent_folder = existing_child
            continue
        new_folder = models.FolderRecord(
            owner_id=owner_id,
            parent_folder_id=parent_folder.folder_id,
            folder_name=folder_name,
            full_path=os.path.join(parent_folder.full_path, folder_name)
        )
        parent_folder = create_child_folder(db, new_folder, folder_name)
    return parent_folder


def update_file_record(db: Session,
                       folder: models.FolderRecord,
                       storage_id: str,
                       filename: str,
                       size: int) -> models.FileRecord:
    existing_file = _get_child_file(folder, filename)
    file_record = existing_file or models.FileRecord(
        folder_id=folder.folder_id,
        filename=filename,
        full_path=os.path.join(folder.full_path, filename)
    )
    file_record.storage_id = storage_id
    file_record.size = size
    return _update_record(db, file_record)


def list_folder(folder: models.FolderRecord) -> dict[str, list[str]]:
    return {
        "files": list(map(lambda file: file.filename, folder.files)),
        "folders": list(map(lambda folder: folder.folder_name, folder.child_folders))
    }
