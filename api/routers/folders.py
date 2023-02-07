from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from ..db import crud, models
from ..dependencies import get_db, get_key_record, verify_token
from ..schemas import CreateFolder
from ..utils.path_utils import split_head_and_tail

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
        parent_path, folder_name = split_head_and_tail(request.path)
        parent_folder = crud.find_folder(db, owner=key_record, full_path=parent_path)
        if parent_folder is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Parent folder doesn't exist")
        crud.create_child_folder(db, parent_folder, folder_name)
