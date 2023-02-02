from fastapi import APIRouter, Depends, Header, status
from fastapi.exceptions import HTTPException
from KEK.hybrid import PublicKEK
from sqlalchemy.orm import Session

from ..db import crud
from ..dependencies import get_db, get_session, verify_token
from ..schemas import PublicKeyInfo

router = APIRouter(tags=["folders"])


@router.post("/mkdir")
def create_folder(
    request: PublicKeyInfo,
    signed_token: str | None = Header(default=None),
    db: Session = Depends(get_db)
): ...
