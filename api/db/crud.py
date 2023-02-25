import posixpath

from sqlalchemy.orm import Session

from .. import config
from ..utils.path_utils import split_head_and_tail, split_into_components
from . import models
from .engine import Base


def _get_child_folder(parent_folder: models.FolderRecord,
                      child_name: str) -> models.FolderRecord | None:
    return next(filter(
        lambda child: child.name == child_name,
        parent_folder.child_folders
    ), None)


def _get_child_file(parent_folder: models.FolderRecord,
                    filename: str) -> models.FileRecord | None:
    return next(filter(
        lambda child_file: child_file.filename == filename,
        parent_folder.files
    ), None)


def _update_child_full_paths(folder: models.FolderRecord):
    for file in folder.files:
        file.full_path = posixpath.join(folder.full_path, file.filename)
    for child_folder in folder.child_folders:
        child_folder.full_path = posixpath.join(folder.full_path, child_folder.name)
        _update_child_full_paths(child_folder)


def _update_record(db: Session, record: Base) -> Base:
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_key_by_id(db: Session, key_id: str) -> models.KeyRecord | None:
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


def return_or_create_root_folder(db: Session,
                                 key_record: models.KeyRecord) -> models.FolderRecord:
    existing_folder_record = db.query(models.FolderRecord).filter_by(
        owner=key_record,
        full_path=models.ROOT_PATH
    ).first()
    if existing_folder_record:
        return existing_folder_record
    folder_record = models.FolderRecord(
        owner=key_record,
        name=models.ROOT_PATH,
        full_path=models.ROOT_PATH
    )
    return _update_record(db, folder_record)


def create_child_folder(db: Session,
                        parent_folder: models.FolderRecord,
                        name: str) -> models.FolderRecord:
    child_folder = models.FolderRecord(
        owner=parent_folder.owner,
        parent_folder=parent_folder,
        name=name,
        full_path=posixpath.join(parent_folder.full_path, name)
    )
    return _update_record(db, child_folder)


def create_folders_recursively(db: Session,
                               key_record: models.KeyRecord,
                               folder_path: str) -> models.FolderRecord:
    current_folder = return_or_create_root_folder(db, key_record)
    path_components = split_into_components(folder_path)
    for folder_name in path_components:
        existing_child = _get_child_folder(current_folder, folder_name)
        if existing_child:
            current_folder = existing_child
            continue
        current_folder = create_child_folder(db, current_folder, folder_name)
    return current_folder


def rename_folder(db: Session,
                  folder: models.FolderRecord,
                  new_name: str) -> models.FolderRecord:
    folder.name = new_name
    parent_path, _ = split_head_and_tail(folder.full_path)
    folder.full_path = posixpath.join(parent_path, new_name)
    _update_child_full_paths(folder)
    return _update_record(db, folder)


def move_folder(db: Session,
                folder: models.FolderRecord,
                destination_folder: models.FolderRecord) -> models.FolderRecord:
    folder.parent_folder = destination_folder
    folder.full_path = posixpath.join(destination_folder.full_path, folder.name)
    _update_child_full_paths(folder)
    return _update_record(db, folder)


def list_folder(folder: models.FolderRecord) -> dict[str, list[str]]:
    return {
        "files": list(map(lambda file: file.filename, folder.files)),
        "folders": list(map(lambda folder: folder.name, folder.child_folders))
    }


def update_file_record(db: Session,
                       folder: models.FolderRecord,
                       filename: str,
                       storage: models.StorageRecord,
                       size: int) -> models.FileRecord:
    existing_file = _get_child_file(folder, filename)
    file_record = existing_file or models.FileRecord(
        folder=folder,
        filename=filename,
        full_path=posixpath.join(folder.full_path, filename)
    )
    file_record.storage = storage
    file_record.size = size
    return _update_record(db, file_record)
