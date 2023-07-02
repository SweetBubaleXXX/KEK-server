import base64
import binascii

from fastapi import Depends, Header, status
from KEK.exceptions import VerificationError
from KEK.hybrid import PublicKEK
from sqlalchemy.orm import Session

from .db import crud, models
from .db.dependency import create_get_db_dependency
from .db.engine import SessionLocal
from .exceptions import client, core
from .utils.path_utils import normalize
from .utils.sessions import BaseSessionStorage, create_session_dependency
from .utils.storage import StorageClient

get_session = create_session_dependency()
get_db = create_get_db_dependency(SessionLocal)


def get_key_record(
    key_id: str = Header(),
    db: Session = Depends(get_db),
    session_storage: BaseSessionStorage = Depends(get_session),
) -> models.KeyRecord:
    key_record = crud.get_key_by_id(db, key_id)
    with session_storage.lock:
        if key_record is None:
            token = session_storage.get(key_id) or session_storage.add(key_id)
            raise client.RegistrationRequired(token)
    return key_record


def get_key(key_record: models.KeyRecord = Depends(get_key_record)) -> PublicKEK:
    public_key = PublicKEK.load(key_record.public_key.encode("ascii"))
    return public_key


def get_path(path: str = Header()) -> str:
    return normalize(path)


def get_folder_record(
    path: str = Depends(get_path),
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db),
) -> models.FolderRecord | None:
    return crud.find_folder(db, owner=key_record, full_path=normalize(path))


def get_folder_record_required(
    folder_record: models.FolderRecord | None = Depends(get_folder_record),
) -> models.FolderRecord:
    if folder_record is None:
        raise client.NotExists(status.HTTP_404_NOT_FOUND, detail="Folder doesn't exist")
    return folder_record


def get_file_record(
    path: str = Depends(get_path),
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db),
) -> models.FileRecord | None:
    return crud.find_file(db, owner=key_record, full_path=normalize(path))


def get_file_record_required(
    file_record: models.FileRecord | None = Depends(get_file_record),
) -> models.FileRecord:
    if file_record is None:
        raise client.NotExists(status.HTTP_404_NOT_FOUND, detail="File not found")
    return file_record


def get_available_storage(
    file_size: int = Header(),
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db),
) -> StorageClient:
    storages = (
        db.query(models.StorageRecord)
        .order_by(models.StorageRecord.priority, models.StorageRecord.free)
        .all()
    )
    for storage in storages:
        if file_size <= storage.free:
            return StorageClient(db, key_record, storage)
    raise core.NoAvailableStorage()


def validate_available_space(
    file_size: int = Header(),
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db),
):
    available_space = key_record.storage_size_limit - crud.calculate_used_storage(
        db, key_record
    )
    if file_size > available_space:
        raise client.NotEnoughSpace()


def verify_token(
    signed_token: str | None = Header(default=None),
    key: PublicKEK = Depends(get_key),
    session_storage: BaseSessionStorage = Depends(get_session),
):
    with session_storage.lock:
        key_id = key.key_id.hex()
        if key_id not in session_storage:
            raise client.AuthenticationRequired(session_storage.add(key_id))
        token = session_storage[key_id]
        if not signed_token:
            raise client.AuthenticationRequired(token)
        try:
            decoded_token = base64.b64decode(signed_token)
            assert key.verify(decoded_token, str(token).encode())
        except (binascii.Error, VerificationError, AssertionError) as exc:
            raise client.AuthenticationFailed(token) from exc
