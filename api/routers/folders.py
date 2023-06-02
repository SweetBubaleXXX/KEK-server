from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..db import crud, models
from ..dependencies import get_db, get_folder_record_required, get_key_record, verify_token
from ..exceptions import client
from ..schemas.base import MoveItem, RenameItem
from ..schemas.folders import CreateFolder
from ..utils.path_utils import split_head_and_tail
from ..utils.storage import StorageClient

router = APIRouter(tags=["folders"], dependencies=[Depends(verify_token)])


@router.post("/mkdir")
def create_folder(
    request: CreateFolder,
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db),
):
    if request.recursive:
        crud.create_folders_recursively(db, key_record, request.path)
    else:
        if (
            crud.folder_exists(db, owner=key_record, full_path=request.path)
            or crud.file_exists(db, owner=key_record, full_path=request.path)
        ):
            raise client.AlreadyExists(detail="Folder/file with this name already exists")
        parent_path, folder_name = split_head_and_tail(request.path)
        parent_folder = crud.find_folder(db, owner=key_record, full_path=parent_path)
        if parent_folder is None:
            raise client.NotExists(detail="Parent folder doesn't exist")
        crud.create_child_folder(db, parent_folder, folder_name)


@router.post("/rename")
def rename_folder(
    request: RenameItem,
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db),
):
    folder_record = crud.find_folder(db, owner=key_record, full_path=request.path)
    if folder_record is None:
        raise client.NotExists(status.HTTP_404_NOT_FOUND, detail="Folder doesn't exist")
    if crud.item_in_folder(db, request.new_name, folder_record.parent_folder):
        raise client.AlreadyExists(detail="Folder/file with this name already exists")
    crud.rename_folder(db, folder_record, request.new_name)


@router.post("/move")
def move_folder(
    request: MoveItem,
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db),
):
    folder_record = crud.find_folder(db, owner=key_record, full_path=request.path)
    destination_folder_record = crud.find_folder(db, owner=key_record,
                                                 full_path=request.destination)
    if not (folder_record and destination_folder_record):
        raise client.NotExists(status.HTTP_404_NOT_FOUND, detail="Folder doesn't exist")
    if crud.item_in_folder(db, folder_record.name, destination_folder_record):
        raise client.AlreadyExists(detail="Folder/file with this name already exists")
    crud.move_folder(db, folder_record, destination_folder_record)


@router.get("/list")
def list_folder(
    folder_record: models.FolderRecord = Depends(get_folder_record_required),
):
    return crud.list_folder(folder_record)


@router.delete("/rmdir")
async def delete_folder(
    folder_record: models.FolderRecord = Depends(get_folder_record_required),
    db: Session = Depends(get_db)
):
    await StorageClient.delete_folder(db, folder_record)
