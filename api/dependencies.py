import base64
import binascii

from fastapi import Depends
from KEK.hybrid import PublicKEK
from KEK.exceptions import VerificationError
from sqlalchemy.orm import Session

from . import crud
from .database import SessionLocal
from .exceptions import exceptions
from .models import KeyRecord
from .schemas import BaseRequest, SignedRequest
from .sessions import SessionStorage, create_session_dependency

get_session = create_session_dependency()


def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def get_key(request: BaseRequest,
            db: Session = Depends(get_db)) -> PublicKEK:
    key_record = crud.get_key(request.key_id)
    if key_record is None:
        raise exceptions.RegistrationRequired(request.key_id)
    public_key = PublicKEK.load(key_record.public_key.encode("ascii"))
    return public_key


def verify_token(request: SignedRequest,
                 key: PublicKEK = Depends(get_key),
                 session_storage: SessionStorage = Depends(get_session)):
    if request.signed_token is None or request.key_id not in session_storage:
        raise exceptions.AuthenticationRequired(request.key_id)
    token = session_storage.get(request.key_id)
    try:
        decoded_token = base64.b64decode(request.signed_token)
        assert key.verify(decoded_token, str(token).encode("ascii"))
    except (binascii.Error, VerificationError, AssertionError):
        raise exceptions.AuthenticationFailed()
    session_storage.pop(request.key_id)
