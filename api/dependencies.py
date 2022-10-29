from typing import Type

from fastapi import Depends, HTTPException, status
from KEK.hybrid import PublicKEK
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import KeyRecord
from .schemas import BaseRequest, SignedRequest

tokens = {}


def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def get_key(request_model: BaseRequest, db: Session = Depends(get_db)):
    key_record = db.get(KeyRecord(id=request_model.key_id))
    if key_record is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return key_record


def create_signing_dependency(request_schema: Type[SignedRequest]):
    def signing_dependency(request_model: request_schema,
                           key: PublicKEK = Depends(get_key)):
        pass
    return signing_dependency
