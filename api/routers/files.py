import aiohttp
from fastapi import APIRouter, Depends, Header
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from api.exceptions import core
from api.schemas import storage_api

from ..db import crud, models
from ..dependencies import (get_available_storage, get_db, get_file_record_required,
                            validate_available_space, verify_token)
from ..utils.storage import StorageClient

router = APIRouter(tags=["files"], dependencies=[Depends(verify_token)])


@router.get("/download", dependencies=[])
async def download_file(
    file_record: models.FileRecord = Depends(get_file_record_required),
):
    async with aiohttp.ClientSession(file_record.storage.url) as session:
        res = await session.get(
            f'/file/{file_record.id}',
            headers=storage_api.StorageRequestHeaders(
                authorization=file_record.storage.token
            ).dict(by_alias=True),
        )
        if not res.ok:
            raise core.StorageResponseError(res)
        return StreamingResponse(res.content, background=BackgroundTask(res.close))


@router.post("/upload", dependencies=[Depends(validate_available_space)])
async def upload_file(
    request: Request,
    path: str = Header(),
    file_size: int = Header(),
    storage_client: StorageClient = Depends(get_available_storage),
    db: Session = Depends(get_db),
):
    file_record = await storage_client.upload_file(path, file_size, request.stream())
    crud.update_record(db, file_record)


@router.delete("/delete")
async def delete_file(
    file_record: models.FileRecord = Depends(get_file_record_required),
    db: Session = Depends(get_db),
):
    storage_client = StorageClient(db, file_record.owner, file_record.storage)
    await storage_client.delete_file(file_record)
    db.commit()
