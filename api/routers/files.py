from fastapi import APIRouter, Depends, Header
from fastapi.requests import Request
from sqlalchemy.orm import Session

from ..db import crud, models
from ..dependencies import (get_available_storage, get_db, get_key_record,
                            validate_available_space, verify_token)
from ..exceptions import client
from ..utils.storage import StorageClient

router = APIRouter(tags=["files"], dependencies=[Depends(verify_token)])


@router.post("/upload", dependencies=[Depends(validate_available_space)])
async def upload_file(
    request: Request,
    path: str = Header(),
    file_size: int = Header(),
    storage_client: StorageClient = Depends(get_available_storage),
    db: Session = Depends(get_db)
):
    await storage_client.upload_file(path, file_size, request.stream())
    crud.update_record(db, storage_client.storage)
