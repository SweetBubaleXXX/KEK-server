from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import models


def get_available_storage(db: Session, key_record: models.KeyRecord, file_size: int):
    user_available_space = key_record.storage_size_limit - calculate_used_storage(db, key_record)
    available_storage = __get_storage(db, file_size)
    if file_size > user_available_space or available_storage is None:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    return available_storage


def calculate_used_storage(db: Session, key_record: models.KeyRecord) -> int:
    return db.query(func.sum(models.FileRecord.size))\
        .join(models.FileRecord.folder)\
        .filter_by(owner=key_record).scalar()


def __get_storage(db: Session, file_size: int) -> models.StorageRecord | None:
    storages = db.query(models.StorageRecord).order_by(models.StorageRecord.priority).all()
    for storage in storages:
        available_space = storage.capacity - storage.used_space
        if file_size <= available_space:
            return storage
    return None
