from urllib.parse import urljoin

import aiohttp
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from sqlalchemy.orm import Session

from ..db import models
from ..dependencies import verify_token
from ..utils.storage import calculate_used_storage_by_user, get_storage

router = APIRouter(tags=["files"], dependencies=[Depends(verify_token)])


async def redirect_file(request: Request, file: models.FileRecord, storage: models.StorageRecord):
    url = urljoin(storage.url, file.id)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=request.stream(), headers={
            "File-Size": file.size
        }) as resp:
            storage_space = await resp.json()
            storage.used_space = storage_space["used"]


def get_available_storage(db: Session, key_record: models.KeyRecord, file_size: int):
    user_available_space = key_record.storage_size_limit - calculate_used_storage_by_user()
    available_storage = get_storage(db, file_size)
    if file_size > user_available_space or available_storage is None:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    return available_storage
