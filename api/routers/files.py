import aiohttp
from urllib.parse import urljoin
from fastapi import APIRouter, Depends, Header, status
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from sqlalchemy.orm import Session

from ..db import crud, models
from ..dependencies import get_db, get_key_record, verify_token
from ..utils.path_utils import split_head_and_tail
from ..utils.storage import calculate_used_storage_by_user, get_storage

router = APIRouter(tags=["files"], dependencies=[Depends(verify_token)])


async def _redirect_file(request: Request, file: models.FileRecord, storage: models.StorageRecord):
    url = urljoin(storage.url, file.id)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=request.stream(), headers={
            "File-Size": file.size
        }) as resp:
            storage_space = await resp.json()
            storage.used_space = storage_space["used"]


@router.post("/upload")
async def upload_file(
    request: Request,
    path: str = Header(),
    file_size: int = Header(),
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db)
):
    user_available_space = key_record.storage_size_limit - calculate_used_storage_by_user()
    available_storage = get_storage(db, file_size)
    if file_size > user_available_space or available_storage is None:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    file_record = crud.find_file(db, owner=key_record, full_path=path)
    old_storage_id = None
    if file_record is None:
        folder_name, filename = split_head_and_tail(path)
        folder_record = crud.find_folder(db, owner=key_record, full_path=folder_name)
        file_record = crud.create_file_record(db, folder_record, filename,
                                              available_storage, file_size)
    else:
        old_storage_id = file_record.storage_id
        file_record.storage = available_storage
        file_record.size = file_size
    await _redirect_file(request, file_record, available_storage)
    # delete file from old storage
    crud.update_record(db, file_record)
    crud.update_record(db, available_storage)
