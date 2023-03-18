import base64
import binascii

from fastapi import Depends, Header, status
from fastapi.exceptions import HTTPException
from KEK.exceptions import VerificationError
from KEK.hybrid import PublicKEK
from sqlalchemy.orm import Session

from .db import crud, models
from .db.dependency import create_get_db_dependency
from .db.engine import SessionLocal
from .exceptions import client, core
from .utils.sessions import SessionStorage, create_session_dependency
from .utils.storage import StorageClient

get_session = create_session_dependency()
get_db = create_get_db_dependency(SessionLocal)


def get_key_record(key_id: str = Header(), db: Session = Depends(get_db)) -> models.KeyRecord:
    key_record = crud.get_key_by_id(db, key_id)
    if key_record is None:
        raise client.RegistrationRequired(key_id)
    return key_record


def get_key(key_record: models.KeyRecord = Depends(get_key_record)) -> PublicKEK:
    public_key = PublicKEK.load(key_record.public_key.encode("ascii"))
    return public_key


def verify_token(signed_token: str | None = Header(default=None),
                 key: PublicKEK = Depends(get_key),
                 session_storage: SessionStorage = Depends(get_session)):
    key_id = key.key_id.hex()
    if signed_token is None or key_id not in session_storage:
        raise client.AuthenticationRequired(key_id)
    token = session_storage.get(key_id)
    try:
        decoded_token = base64.b64decode(signed_token)
        assert key.verify(decoded_token, str(token).encode("ascii"))
    except (binascii.Error, VerificationError, AssertionError) as exc:
        raise client.AuthenticationFailed() from exc
    session_storage.pop(key_id)


def validate_available_space(file_size: int = Header(),
                             key_record: models.KeyRecord = Depends(get_key_record),
                             db: Session = Depends(get_db)):
    available_space = key_record.storage_size_limit - crud.calculate_used_storage(db, key_record)
    if file_size > available_space:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


def get_available_storage(file_size: int = Header(),
                          key_record: models.KeyRecord = Depends(get_key_record),
                          db: Session = Depends(get_db)) -> StorageClient:
    storages = db.query(models.StorageRecord).order_by(models.StorageRecord.priority).all()
    for storage in storages:
        available_space = storage.capacity - storage.used_space
        if file_size <= available_space:
            return StorageClient(storage, key_record, db)
    raise core.NoAvailableStorage
