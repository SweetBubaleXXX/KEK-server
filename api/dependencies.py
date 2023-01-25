import base64
import binascii

from fastapi import Depends, Header
from KEK.exceptions import VerificationError
from KEK.hybrid import PublicKEK
from sqlalchemy.orm import Session

from . import crud
from .db import SessionLocal
from .exceptions import exceptions
from .sessions import SessionStorage, create_session_dependency

get_session = create_session_dependency()


def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def get_key(key_id: str = Header(), db: Session = Depends(get_db)) -> PublicKEK:
    key_record = crud.get_key(db, key_id)
    if key_record is None:
        raise exceptions.RegistrationRequired(key_id)
    public_key = PublicKEK.load(key_record.public_key.encode("ascii"))
    return public_key


def verify_token(signed_token: str | None = Header(default=None),
                 key: PublicKEK = Depends(get_key),
                 session_storage: SessionStorage = Depends(get_session)):
    key_id = key.key_id.hex()
    if signed_token is None or key_id not in session_storage:
        raise exceptions.AuthenticationRequired(key_id)
    token = session_storage.get(key_id)
    try:
        decoded_token = base64.b64decode(signed_token)
        assert key.verify(decoded_token, str(token).encode("ascii"))
    except (binascii.Error, VerificationError, AssertionError):
        raise exceptions.AuthenticationFailed()
    session_storage.pop(key_id)
