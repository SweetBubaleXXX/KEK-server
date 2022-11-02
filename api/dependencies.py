import base64

from fastapi import Depends, HTTPException, status
from KEK.hybrid import PublicKEK
from sqlalchemy.orm import Session

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


def get_key(request_model: BaseRequest, db: Session = Depends(get_db)):
    key_record = db.get(KeyRecord(id=request_model.key_id))
    if key_record is None:
        raise exceptions.RegistrationRequired()
    return key_record


def verify_token(request: SignedRequest,
                 key: PublicKEK = Depends(get_key),
                 session_storage: SessionStorage = Depends(get_session)):
    if token is None or request.key_id not in session_storage:
        raise exceptions.AuthenticationRequired()
    token = session_storage.get(request.key_id)
    decoded_token = base64.b64decode(request.signed_token)
    is_verified = key.verify(decoded_token, token.bytes)
    if not is_verified:
        raise exceptions.AuthenticationFailed()
