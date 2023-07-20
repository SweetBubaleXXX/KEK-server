from fastapi import APIRouter, Depends, Header, status
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import crud, models
from ..dependencies import (
    get_available_storage,
    get_db,
    get_file_record_required,
    get_path,
    validate_file_size,
    verify_token,
)
from ..exceptions import client
from ..utils.storage import StorageClient

router = APIRouter(tags=["files"], dependencies=[Depends(verify_token)])


@router.get("/download")
async def download_file(
    file_record: models.FileRecord = Depends(get_file_record_required),
):
    return StreamingResponse(StorageClient.download_file(file_record))


@router.post(
    "/upload",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(validate_file_size)],
)
async def upload_file(
    request: Request,
    path: str = Depends(get_path),
    file_size: int = Header(),
    storage_client: StorageClient = Depends(get_available_storage),
    db: AsyncSession = Depends(get_db),
):
    if await crud.folder_exists(db, owner=storage_client.client, full_path=path):
        raise client.AlreadyExists(detail="Folder with this name already exists")
    file_record = await storage_client.upload_file(path, file_size, request.stream())
    await crud.update_record(db, file_record)


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_record: models.FileRecord = Depends(get_file_record_required),
    db: AsyncSession = Depends(get_db),
):
    storage_client = StorageClient(
        db, await file_record.owner, await file_record.awaitable_attrs.storage
    )
    await storage_client.delete_file(file_record)
    await db.flush()
