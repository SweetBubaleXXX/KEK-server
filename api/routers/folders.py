from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import crud, models
from ..dependencies import (
    get_db,
    get_folder_record_required,
    get_key_record,
    verify_token,
)
from ..exceptions import client
from ..schemas.base import MoveItemRequest, RenameItemRequest
from ..schemas.folders import CreateFolderRequest
from ..utils.path_utils import split_head_and_tail
from ..utils.storage import StorageClient

router = APIRouter(tags=["folders"], dependencies=[Depends(verify_token)])


@router.get("/list")
async def list_folder(
    folder_record: models.FolderRecord = Depends(get_folder_record_required),
):
    return await folder_record.json()


@router.get("/size")
def folder_size(
    folder_record: models.FolderRecord = Depends(get_folder_record_required),
):
    return folder_record.size


@router.delete("/rmdir")
async def delete_folder(
    folder_record: models.FolderRecord = Depends(get_folder_record_required),
    db: AsyncSession = Depends(get_db),
):
    await StorageClient.delete_folder(db, folder_record)


@router.post("/mkdir")
async def create_folder(
    request: CreateFolderRequest,
    key_record: models.KeyRecord = Depends(get_key_record),
    db: AsyncSession = Depends(get_db),
):
    if request.recursive:
        await crud.create_folders_recursively(db, key_record, request.path)
    else:
        if await crud.folder_exists(
            db, owner=key_record, full_path=request.path
        ) or await crud.file_exists(db, owner=key_record, full_path=request.path):
            raise client.AlreadyExists(
                detail="Folder/file with this name already exists"
            )
        parent_path, folder_name = split_head_and_tail(request.path)
        parent_folder = await crud.find_folder(
            db, owner=key_record, full_path=parent_path
        )
        if parent_folder is None:
            raise client.NotExists(detail="Parent folder doesn't exist")
        await crud.create_child_folder(db, parent_folder, folder_name)


@router.post("/rename")
async def rename_folder(
    request: RenameItemRequest,
    key_record: models.KeyRecord = Depends(get_key_record),
    db: AsyncSession = Depends(get_db),
):
    folder_record = await crud.find_folder(db, owner=key_record, full_path=request.path)
    if folder_record is None:
        raise client.NotExists(status.HTTP_404_NOT_FOUND, detail="Folder doesn't exist")
    if await crud.item_in_folder(
        db, request.new_name, await folder_record.awaitable_attrs.parent_folder
    ):
        raise client.AlreadyExists(detail="Folder/file with this name already exists")
    await crud.rename_folder(db, folder_record, request.new_name)


@router.post("/move")
async def move_folder(
    request: MoveItemRequest,
    key_record: models.KeyRecord = Depends(get_key_record),
    db: AsyncSession = Depends(get_db),
):
    folder_record = await crud.find_folder(db, owner=key_record, full_path=request.path)
    destination_folder_record = await crud.find_folder(
        db, owner=key_record, full_path=request.destination
    )
    if not (folder_record and destination_folder_record):
        raise client.NotExists(status.HTTP_404_NOT_FOUND, detail="Folder doesn't exist")
    if await crud.item_in_folder(db, folder_record.name, destination_folder_record):
        raise client.AlreadyExists(detail="Folder/file with this name already exists")
    await crud.move_folder(db, folder_record, destination_folder_record)
