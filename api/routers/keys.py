from fastapi import APIRouter, Depends, Header
from KEK.exceptions import KeyLoadingError
from KEK.hybrid import PublicKEK
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import crud, models
from ..dependencies import get_db, get_key_record, get_session, verify_token
from ..exceptions import client
from ..schemas.authentication import PublicKeyInfo
from ..schemas.base import StorageInfoResponse

router = APIRouter(tags=["keys"])


@router.post("/register")
async def register_key(
    request: PublicKeyInfo,
    signed_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        key = PublicKEK.load(request.public_key.encode("ascii"))
        assert key.key_id.hex() == request.key_id
    except (KeyLoadingError, AssertionError) as exc:
        raise client.RegistrationFailed(detail="Could not load public key") from exc
    verify_token(signed_token, key, get_session())
    key_record = await crud.get_key_by_id(db, request.key_id)
    if not key_record:
        key_record = await crud.add_key(db, request.key_id, request.public_key)
    await crud.return_or_create_root_folder(db, key_record)


@router.get("/storage", dependencies=[Depends(verify_token)])
async def storage_info(
    key_record: models.KeyRecord = Depends(get_key_record),
    db: AsyncSession = Depends(get_db),
):
    return StorageInfoResponse(
        used=await crud.calculate_used_storage(db, key_record),
        limit=key_record.storage_size_limit,
    )
