from fastapi import APIRouter, Depends, Header
from KEK.exceptions import KeyLoadingError
from KEK.hybrid import PublicKEK
from sqlalchemy.orm import Session

from ..db import crud
from ..dependencies import get_db, get_session, verify_token
from ..exceptions import client
from ..schemas.authentication import PublicKeyInfo

router = APIRouter(tags=["registration"])


@router.post("/register")
def register_key(
    request: PublicKeyInfo,
    signed_token: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    try:
        key = PublicKEK.load(request.public_key.encode("ascii"))
        assert key.key_id.hex() == request.key_id
    except (KeyLoadingError, AssertionError) as e:
        raise client.AuthenticationFailed(detail="Could not load public key") from e
    verify_token(signed_token, key, get_session())
    key_record = crud.get_key_by_id(db, request.key_id)
    if not key_record:
        key_record = crud.add_key(db, request.key_id, request.public_key)
    crud.return_or_create_root_folder(db, key_record)
