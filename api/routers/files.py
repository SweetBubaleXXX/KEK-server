from fastapi import APIRouter, Depends, Header
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..db import crud, models
from ..dependencies import (get_available_storage, get_db, get_file_record_required,
                            validate_available_space, verify_token)
from ..utils.storage import StorageClient

router = APIRouter(tags=["files"], dependencies=[Depends(verify_token)])


@router.get("/download", dependencies=[])
async def download_file(
    file_record: models.FileRecord = Depends(get_file_record_required),
):
    stream_reader = await StorageClient.download_file(file_record)
    return StreamingResponse(stream_reader)


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
