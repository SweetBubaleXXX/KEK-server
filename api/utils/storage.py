from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import crud, models


def get_storage(db: Session, file_size: int) -> models.StorageRecord | None:
    storages = db.query(models.StorageRecord).order_by(models.StorageRecord.priority).all()
    for storage in storages:
        available_space = storage.capacity - storage.used_space
        if file_size < available_space:
            return storage
    return None


def calculate_used_storage_by_user(db: Session, key_record: models.KeyRecord) -> int:
    return db.query(func.sum(models.FileRecord.size))\
        .join(models.FileRecord.folder)\
        .filter_by(owner=key_record).scalar()
