from fastapi import APIRouter, Depends, Header
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..db import crud, models
from ..dependencies import (
    get_available_storage,
    get_db,
    get_file_record_required,
    get_path,
    validate_available_space,
    verify_token,
)
from ..exceptions import client
from ..utils.storage import StorageClient

router = APIRouter(tags=["files"], dependencies=[Depends(verify_token)])


@router.get("/download", dependencies=[])
async def download_file(
    file_record: models.FileRecord = Depends(get_file_record_required),
):
    return StreamingResponse(StorageClient.download_file(file_record))


@router.post("/upload", dependencies=[Depends(validate_available_space)])
async def upload_file(
    request: Request,
    path: str = Depends(get_path),
    file_size: int = Header(),
    storage_client: StorageClient = Depends(get_available_storage),
    db: Session = Depends(get_db),
):
    if crud.folder_exists(db, owner=storage_client.client, full_path=path):
        raise client.AlreadyExists(detail="Folder with this name already exists")
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
