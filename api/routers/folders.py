from fastapi import APIRouter, Depends, Header, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from ..db import crud, models
from ..dependencies import get_db, get_key_record, verify_token
from ..schemas import CreateFolder, MoveItem, RenameItem
from ..utils.path_utils import split_head_and_tail

router = APIRouter(tags=["folders"], dependencies=[Depends(verify_token)])


@router.post("/mkdir")
def create_folder(
    request: CreateFolder,
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db)
):
    if request.recursive:
        crud.create_folders_recursively(db, key_record, request.path)
    else:
        parent_path, folder_name = split_head_and_tail(request.path)
        parent_folder = crud.find_folder(db, owner=key_record, full_path=parent_path)
        if parent_folder is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Parent folder doesn't exist")
        crud.create_child_folder(db, parent_folder, folder_name)


@router.post("/rename")
def rename_folder(
    request: RenameItem,
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db)
):
    folder_record = crud.find_folder(db, owner=key_record, full_path=request.path)
    if folder_record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Folder doesn't exist")
    sibling_folders = crud.list_folder(folder_record.parent_folder)["folders"]
    if request.new_name in sibling_folders:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="Folder/file with this name already exists")
    crud.rename_folder(db, folder_record, request.new_name)


@router.get("/list")
def list_folder(
    path: str = Header(),
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db)
) -> dict[str, list[str]]:
    folder_record = crud.find_folder(db, owner=key_record, full_path=path)
    if folder_record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Folder doesn't exist")
    return crud.list_folder(folder_record)


@router.post("/move")
def move_folder(
    request: MoveItem,
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db)
):
    folder_record = crud.find_folder(db, owner=key_record, full_path=request.path)
    destination_folder_record = crud.find_folder(db, owner=key_record,
                                                 full_path=request.destination)
    if not (folder_record and destination_folder_record):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Folder doesn't exist")
    crud.move_folder(db, folder_record, destination_folder_record)


@router.delete("/rmdir")
def delete_folder(
    path: str = Header(),
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db)
): ...
