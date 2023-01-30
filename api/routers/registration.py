from fastapi import APIRouter, Depends, Header, status
from fastapi.exceptions import HTTPException
from KEK.exceptions import KeyLoadingError
from KEK.hybrid import PublicKEK
from sqlalchemy.orm import Session

from ..db import crud
from ..dependencies import get_db, get_session, verify_token
from ..schemas import PublicKeyInfo

router = APIRouter()


@router.post("/register")
def register_key(
    request: PublicKeyInfo,
    signed_token: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    try:
        key = PublicKEK.load(request.public_key.encode("ascii"))
        assert key.key_id.hex() == request.key_id
    except (KeyLoadingError, AssertionError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Could not load public key")
    verify_token(signed_token, key, get_session())
    if not crud.get_key(db, request.key_id):
        crud.add_key(db, request.key_id, request.public_key)