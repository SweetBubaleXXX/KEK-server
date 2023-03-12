from typing import AsyncIterator
from urllib.parse import urljoin

import aiohttp
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from ..db import models
from ..dependencies import verify_token
from ..schemas.storage_api import UploadRequestHeaders, UploadResponse
from ..utils.storage import calculate_used_storage, get_storage

router = APIRouter(tags=["files"], dependencies=[Depends(verify_token)])


async def redirect_file(stream: AsyncIterator[bytes],
                        file_record: models.FileRecord,
                        storage: models.StorageRecord):
    url = urljoin(storage.url, file_record.id)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=stream, headers=UploadRequestHeaders(
            file_size=file_record.size
        ).dict(by_alias=True)) as resp:
            storage_space = UploadResponse.parse_obj(await resp.json())
            storage.used_space = storage_space.used


def get_available_storage(db: Session, key_record: models.KeyRecord, file_size: int):
    user_available_space = key_record.storage_size_limit - calculate_used_storage(db, key_record)
    available_storage = get_storage(db, file_size)
    if file_size > user_available_space or available_storage is None:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    return available_storage
